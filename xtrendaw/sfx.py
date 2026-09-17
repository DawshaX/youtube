"""مؤثرات صوتية مرخّصة — طبقة الاستوديو (ووش/ارتطام/صعود).

المصدر الشبكي الأول: **Freesound** عبر `FREESOUND_API_KEY`.
قاعدة الترخيص حاكمة زي كل المصنع: بنقبل **CC0 وCC-BY بس** —
الترخيص غير التجاري (NC) مرفوض لأن القناة ممكن تتربح يومًا ما.
كل مؤثر بيتسجل في `vault/index.json` بترخيصه واعتماده قبل ما يدخل أي
مونتاج (بند 0/4) — ومؤثرات `internal` المولدة بايتس مسموحة دايمًا بلا نت.

الاستخدام:
    sfx.pick("whoosh", workdir) → Path mp3 أو None
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import requests

from . import settings
from .tts import ffmpeg

API = "https://freesound.org/apiv2"
SFX_DIR = settings.STATE / "sfxlib"
UA = {"User-Agent": "DaoushaFactory/1.0 (educational shorts)"}

# اعتمادات المؤثرات اللي اتسجلت في الجلسة الحالية (للوصف تحت Credits:)
_SESSION_CREDITS: list[str] = []


def session_credits() -> list[str]:
    return list(_SESSION_CREDITS)


# خانات الاستوديو ← كلمات بحث + ترخيص مقبول
CATEGORIES = {
    "whoosh": ("cinematic whoosh transition", 0.4, 2.5),
    "impact": ("deep cinematic impact hit", 0.8, 3.0),
    "riser": ("tension riser", 1.5, 5.0),
    "reveal": ("magical reveal sparkle", 0.8, 3.5),
}

# تراخيص فريساوند المسموحة ← ترجمة لترخيص الحارس
_LICENSE_MAP = {
    "Creative Commons 0": ("CC0", False),
    "Attribution": ("CC-BY-4.0", True),
    # "Attribution NonCommercial" مرفوضة عمدًا — القناة قابلة للتربح
}


def license_ok(freesound_license: str) -> tuple[str, bool] | None:
    """ترخيص فريساوند → (ترخيص الحارس، هل الإسناد مطلوب)."""
    return _LICENSE_MAP.get((freesound_license or "").strip())


def _search(query: str, dur_lo: float, dur_hi: float) -> list[dict]:
    key = settings.FREESOUND_API_KEY
    if not key:
        return []
    try:
        r = requests.get(
            f"{API}/search/text/",
            params={
                "query": query,
                "token": key,
                # الفلترة الحقيقية على الترخيص بتتم عندنا في `license_ok`
                # (ما نأمنش لصياغة الفلاتر نضيف عليها مصير الرندر)
                "filter": f"duration:[{dur_lo} TO {dur_hi}]",
                "fields": "id,name,license,username,previews",
                "sort": "rating_desc",
                "page_size": 8,
            },
            headers=UA, timeout=25,
        )
        if not r.ok:
            return []
        return r.json().get("results", [])
    except Exception:
        return []


def fetch(category: str, out_dir: Path) -> Path | None:
    """هات مؤثر مرخّص للخانة → ملف mp3 مسجل في الخزنة، أو None."""
    if category not in CATEGORIES:
        return None
    query, dur_lo, dur_hi = CATEGORIES[category]
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    for res in _search(query, dur_lo, dur_hi):
        mapped = license_ok(res.get("license", ""))
        if mapped is None:
            continue  # مش مسموح — ارفض وتجاهل لغيره
        url = (res.get("previews") or {}).get("preview-hq-mp3", "")
        if not url:
            continue
        digest = hashlib.sha256(url.encode()).hexdigest()[:14]
        cached = SFX_DIR / f"{category}_{digest}.mp3"
        if not cached.exists():
            try:
                r = requests.get(url, headers=UA, timeout=60)
                if not r.ok or len(r.content) < 20_000:
                    continue
                cached.write_bytes(r.content)
            except Exception:
                continue
        # قيد الترخيص إلزامي قبل ما المؤثر يتاح لأي مونتاج (بند 0/4)
        from . import vault
        lic, attribution = mapped
        credit = ""
        if attribution:
            credit = (f"SFX: \"{res.get('name', '?')}\" by "
                      f"{res.get('username', '?')} via Freesound, {lic}")
        if credit not in _SESSION_CREDITS:
            _SESSION_CREDITS.append(credit)
        try:
            vault.register(cached, source="freesound", license=lic,
                           attribution_required=attribution,
                           credit_line=credit, url=url)
        except RuntimeError:
            cached.unlink(missing_ok=True)
            continue
        # نسخة شغالة للمونتاج الجاري
        out = out_dir / f"sfx_{category}_{digest}.mp3"
        subprocess.run([ffmpeg(), "-y", "-i", str(cached), "-c", "copy",
                        str(out)], capture_output=True)
        return out if out.exists() else None
    return None


def pick(category: str, workdir: Path) -> Path | None:
    """واجهة الاستوديو: مؤثر جاهز للدمج، أو صمت (المصنع ما يقفش على مؤثر)."""
    if not settings.FREESOUND_API_KEY:
        return None
    try:
        return fetch(category, workdir)
    except Exception:
        return None
