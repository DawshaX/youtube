"""مكتبة العالم — بيانات حقيقية عن دولة الفيديو (restcountries.com).

مصدر مجاني يعمل بلا مفتاح (ومع سر `RESTCOUNTRIES` حدود أعلى). العين
بتستخدمها عشان تضيف قسم «الفيديو في العالم» في الـ DNA: الخطاف والنبرة
بيتعاملوا مع دولة حقيقية (سكان/لغة/عملة/منطقة) — لا أرقام متخيلة.

أي فشل في الشبكة = {} (تدهور صريح — الدليل يقف بدون قسم العالم).
"""
from __future__ import annotations

import re

from . import settings

BASE = "https://restcountries.com/v3.1"
_KEY = settings.get("RESTCOUNTRIES_API_KEY") or settings.get("RESTCOUNTRIES")


def _req():
    """requests تحت الطلب — المودول يستورد أوفلاين."""
    import requests
    return requests


def _headers() -> dict:
    return {"Authorization": _KEY} if _KEY else {}


def country_info(query: str) -> dict:
    """ملف دولة حقيقي: رمز ISO (EG) أو اسم (Egypt / مصر مش مدعوم — بالإنجليزي).

    يعيد: {name, region, subregion, capital, population, languages,
    currency, area, timezones} — و{} عند أي فشل.
    """
    q = (query or "").strip()
    if not q:
        return {}
    url = (f"{BASE}/alpha/{q.upper()}" if re.fullmatch(r"[A-Za-z]{2}", q)
           else f"{BASE}/name/{q}")
    try:
        r = _req().get(url, headers=_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return {}
    if not isinstance(data, list) or not data:
        return {}
    c = data[0]
    common = (c.get("names") or {}).get("common") or {}
    name = common.get("en") or c.get("name") or q
    langs = list((c.get("languages") or {}).values())
    cur = next(iter((c.get("currencies") or {}).values()), None)
    return {
        "name": name,
        "region": c.get("region") or "",
        "subregion": c.get("subregion") or "",
        "capital": (c.get("capital") or ["-"])[0],
        "population": c.get("population") or 0,
        "languages": ", ".join(langs[:3]),
        "currency": (f"{cur['name']} ({cur.get('symbol', '')})" if cur
                     else "-"),
        "area": c.get("area") or 0,
        "timezones": (c.get("timezones") or [])[:2],
    }


def profile_line(info: dict) -> str:
    """سطر واحد مضغوط للقسم في الـ digest."""
    if not info:
        return ""
    pop = f"{info['population']:,}" if info.get("population") else "?"
    return (f"{info['name']} ({info.get('subregion') or info.get('region') or '-'}) — "
            f"العاصمة: {info.get('capital', '-')} · السكان: {pop} · "
            f"اللغة: {info.get('languages', '-')} · العملة: {info.get('currency', '-')}")
