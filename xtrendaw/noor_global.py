"""🌍 الطبقة العالمية — نور يفهمه العالم كله.

- **ترجمة الآيات معتمدة**: من ترجمات موثّقة على alquran.cloud (مش ترجمة آلية)
  en.sahih · ur.jalandhry · fr.hamidullah · id.indonesian · tr.diyanet · es.cortes
- **ترجمة الميتاداتا** (العنوان/الوصف) بالترجمة المفتوحة مع كاش — فشل صامت
  مقصود: لو الترجمة وقعت، الفيديو ينشر عربي زي ما هو (مفيش تعطيل).
- أسماء اللغات بأسمائها الأصلية للعرض في الوصف (ثقة + بحث محلي).
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from . import settings

CACHE = settings.STATE / "noor_cache" / "i18n"
UA = {"User-Agent": "NoorFactory/1.0"}

# لغات الجمهور المسلم الأكبر على يوتيوب (بالترتيب)
LANGS = ["en", "ur", "id", "tr", "fr"]
LANG_LABEL = {"en": "English", "ur": "اردو", "id": "Bahasa Indonesia",
              "tr": "Türkçe", "fr": "Français", "es": "Español"}
VERSE_EDITION = {"en": "en.sahih", "ur": "ur.jalandhry", "fr": "fr.hamidullah",
                 "id": "id.indonesian", "tr": "tr.diyanet", "es": "es.cortes"}


def _cached(name: str, fn, ttl_days: float = 60.0):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / name
    try:
        if p.exists() and (time.time() - p.stat().st_mtime) < ttl_days * 86400:
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    val = fn()
    if val:
        try:
            p.write_text(json.dumps(val, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return val


def verse_translation(surah: int, ayah: int, lang: str) -> str:
    """ترجمة آية من ترجمة **معتمدة** (مش آلية) — لأي لغة مدعومة."""
    ed = VERSE_EDITION.get(lang)
    if not ed:
        return ""
    def fetch():
        url = f"https://api.alquran.cloud/v1/ayah/{int(surah)}:{int(ayah)}/{ed}"
        d = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=30).read())
        return {"t": (d.get("data") or {}).get("text", "")}
    got = _cached(f"v_{surah}_{ayah}_{lang}.json", fetch)
    return str((got or {}).get("t") or "")


def translate_text(text: str, target: str) -> str:
    """ترجمة نص عادي (عنوان/وصف) — مفتوحة + كاش + فشل صامت."""
    text = (text or "").strip()
    if not text:
        return ""
    key = f"t_{target}_{abs(hash(text)) % (10 ** 12)}.json"
    def fetch():
        q = urllib.parse.quote(text[:1200])
        url = ("https://translate.googleapis.com/translate_a/single?"
               f"client=gtx&sl=auto&tl={target}&dt=t&q={q}")
        for _ in range(2):
            try:
                d = json.loads(urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=25).read()
                    .decode("utf-8", "replace"))
                out = "".join(seg[0] for seg in (d[0] or []) if seg and seg[0])
                if out.strip():
                    return {"t": out.strip()}
            except Exception:
                time.sleep(2)
        return None
    got = _cached(key, fetch, ttl_days=365)
    return str((got or {}).get("t") or "")


def global_block(title: str, body: str, surah: int | None = None,
                 ayah: int | None = None, langs: list[str] | None = None) -> str:
    """بلوك وصف متعدد اللغات: العنوان مترجم + ترجمة الآية المعتمدة (لو موجودة).

    ده اللي بيخلي الفيديو «مناسب ١٠٠٪ للعالم» — أي حد يقرا يفهم.
    """
    langs = langs or LANGS
    rows = []
    for lg in langs:
        label = LANG_LABEL.get(lg, lg)
        tt = translate_text(title, lg)
        vt = verse_translation(surah, ayah, lg) if (surah and ayah) else ""
        if not tt and not vt:
            continue
        piece = f"🌍 {label}: {tt}" if tt else f"🌍 {label}:"
        if vt:
            piece += f"\n    「{vt[:260]}」"
        rows.append(piece)
    return ("\n\n🌍 For the world — International:\n" + "\n".join(rows)) if rows else ""
