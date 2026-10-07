"""🎙️ تنويع الأصوات — كل نوع محتوى له نبرته، ودوران بلا تكرار مزعج.

ليه؟ نفس الصوت كل يوم = رتابة ⇒ الناس تحس إنه بوت. الأصوات دي كلها نيورال
عربية **حقيقية** (نفس عيلة أصوات المصنع المعتمدة في NOVA — استُخدمت في
تشغيلات فعلية) — بنوزّعها حسب نوع المحتوى، وبندوّرها بترتيب المسجّل.
"""
from __future__ import annotations

# الأصوات مقسّمة بالمزاج (كلها من العيلة المعتمدة في المصنع)
VOICES: dict[str, list[str]] = {
    "calm": ["ar-EG-SalmaNeural", "ar-SA-ZariyahNeural", "ar-SY-AmanyNeural"],
    "warm": ["ar-SA-HamedNeural", "ar-QA-MoazNeural", "ar-JO-TaimNeural"],
    "serious": ["ar-EG-ShakirNeural", "ar-KW-FahedNeural", "ar-OM-AbdullahNeural"],
}

KIND_MOOD = {
    "spirit": "calm", "athkar": "calm", "dua": "calm",
    "asma": "warm", "quiz": "warm", "salah": "warm", "hijri": "warm",
    "qfacts": "warm", "proverb": "warm",
    "quran": "serious", "tafsir": "serious", "hadith": "serious",
    "qissa": "serious", "story": "serious", "ayah": "serious", "reel": "serious",
}


def pick(kind: str, turn: int = 0) -> str | None:
    mood = KIND_MOOD.get(str(kind or ""), "warm")
    pool = VOICES.get(mood) or VOICES["warm"]
    return pool[int(turn) % len(pool)]


def apply(item: dict) -> str:
    """يظبط صوت الحلقة على مزاج نوعها — ويرجّع الصوت المستخدم."""
    from . import settings
    turn = 0
    try:
        from . import noor_plan
        turn = int((noor_plan._ledger().get("n") or 0))
    except Exception:
        pass
    kind = str(item.get("kind") or item.get("plan_kind") or "")
    v = pick(kind, turn)
    if v:
        settings.VOICE_AR = v
    return str(getattr(settings, "VOICE_AR", "") or "")
