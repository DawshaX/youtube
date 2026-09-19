"""خزنة الوسائط المرخّصة — `vault/index.json` هو حارس الترخيص.

القاعدة الحاكمة (بند 0/4 في البريف): **مفيش أصل وسائط يدخل الرندر من غير
سجل ترخيص في الفهرس — والمخالفة فشل صريح، مش تجاهل.**

كل أصل مسجل بحقول:
    path · source · license · attribution_required · credit_line · url ·
    fetched_at · sha256

`credits_for()` بيجمّع سطور الاعتماد المطلوبة — الناشر بيحطها تلقائيًا في
وصف الفيديو تحت `Credits:`.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import settings

VAULT_DIR = settings.ROOT / "vault"
INDEX_PATH = VAULT_DIR / "index.json"

# التراخيص المسموح تمريرها للريندر (اللائحة في docs/MEDIA_VAULT_SOURCES.md).
#
# الدرس (2026-09-19): الفلتر كان محصورًا في CC0/CC-BY، فكان بينزّل لقطات
# بيكسلز وبيكساباي وناسا **وبعدين يمسحها** ويرجع للمخزون الداخلي الثابت —
# يعني كل مفاتيح الميديا كانت ميتة عمليًا. اللائحة الموثقة في docs بتعتبر
# المصادر دي 🟢، والرخص دي بتسمح الاستخدام التجاري **بلا إسناد**، فمفيش
# سبب لرفضها. الباقي (All-Rights-Reserved وأي رخصة مملوكة) يفضل مرفوض.
ALLOWED_NETWORK_LICENSES = {
    "CC0", "CC-BY-3.0", "CC-BY-4.0",
    "Pexels-License",      # استخدام تجاري بلا إسناد
    "Pixabay-License",     # استخدام تجاري بلا إسناد
    "NASA-Media-Usage",    # وسائط ناسا — استخدام إعلامي/تعليمي
    "Public-Domain",       # أرشيف الإنترنت/كومنز بلا قيود
}

ALLOWED_LICENSES = {
    "CC0",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "Public-Domain",
    "Pexels-License",
    "Pixabay-License",
    "NASA-Media-Usage",
    "Apache-2.0",
    "MIT",
    "OFL-1.1",
    "Internal-Generated",   # مولّد برمجيًا داخل المصنع — ملك المشروع بالكامل
}


def _rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(settings.ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def load_index() -> dict[str, dict]:
    """الفهرس: مسار نسبي → سجل ترخيص."""
    if not INDEX_PATH.exists():
        return {}
    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        return {rec["path"]: rec for rec in data.get("assets", [])
                if rec.get("path")}
    except Exception:
        return {}


def record_for(path: Path | str) -> dict | None:
    return load_index().get(_rel(path))


def require_license(path: Path | str) -> dict:
    """حارس الترخيص: أصل غير مسجل أو ترخيصه مش مسموح → فشل صريح."""
    rel = _rel(path)
    index = load_index()
    rec = index.get(rel)
    if rec is None:
        raise RuntimeError(
            f"vault: الأصل {rel} مش مسجل في {INDEX_PATH} — مفيش وسائط من "
            "غير سجل ترخيص (بند 0/4). سجّله بـ vault.register() الأول.")
    lic = rec.get("license", "")
    if lic not in ALLOWED_LICENSES:
        raise RuntimeError(
            f"vault: ترخيص الأصل {rel} هو {lic!r} — مش في اللائحة المسموحة.")
    if rec.get("attribution_required") and not (rec.get("credit_line") or "").strip():
        raise RuntimeError(
            f"vault: الأصل {rel} محتاج ذكر مصدر ({lic}) ومفيش credit_line — "
            "ارفض الرندر بدل النشر المخالف.")
    return rec


def register(path: Path | str, source: str, license: str,
             attribution_required: bool = False, credit_line: str = "",
             url: str = "") -> dict:
    """يسجل أصلًا جديدًا في الفهرس (بصمة + وقت التسجيل) — للقطات المجْلوبة."""
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"vault: الأصل {p} مش موجود على القرص")
    rec = {
        "path": _rel(p),
        "source": source,
        "license": license,
        "attribution_required": bool(attribution_required),
        "credit_line": credit_line,
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }
    data = {"assets": list(load_index().values())}
    data["assets"] = [a for a in data["assets"] if a["path"] != rec["path"]]
    data["assets"].append(rec)
    data["assets"].sort(key=lambda a: a["path"])
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def sources_for(paths: list[Path | str]) -> dict:
    """تلخيص مصادر الميديا المستخدمة في الحلقة: {المصدر: العدد}.

    بيغذّي سطر الملخص في اللوج — دليل ظاهر إن الحلقة استخدمت ميديا حيّة
    من الـAPIs مش صور مركبة/مخزون قديم.
    """
    index = load_index()
    out: dict[str, int] = {}
    for p in paths:
        rec = index.get(_rel(p)) or {}
        src = str(rec.get("source") or "unknown").lower()
        out[src] = out.get(src, 0) + 1
    return out


def credits_for(paths: list[Path | str]) -> list[str]:
    """سطور الاعتماد لكل الأصول المستخدمة (اللي محتاجة ذكر بس)."""
    index = load_index()
    out: list[str] = []
    for p in paths:
        rec = index.get(_rel(p))
        if rec and rec.get("attribution_required") \
                and (rec.get("credit_line") or "").strip():
            line = rec["credit_line"].strip()
            if line not in out:
                out.append(line)
    return out
