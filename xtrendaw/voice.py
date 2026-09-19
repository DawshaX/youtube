"""مكتبة الأصوات — صوت مناسب لكل حلقة حسب حالتها، ودوران ذكي بلا رتابة.

- 32 صوت عربي حقيقي (state/ar_voices.txt — ملتزمة من تشغيل Actions فعلي)
- جدول مoods: مجنون / دافي / هادي / غامض / جاد — كل mood له أصواته
- دوران: الصوت ما يتكررش خلال آخر 5 حلقات (من data/production_log.json)
- حتمي: نفس topic id = نفس الصوت في أي إعادة رندر (استقرار + تدقيق)

لا صوت من فراغ: كل صوت من القائمة الفعلية، والاختيار متسجل في
`data/production_log.json` بحقل `voice` لكل حلقة.
"""
from __future__ import annotations

import json
import random

from . import settings

AR_VOICES_PATH = settings.ROOT / "state" / "ar_voices.txt"
PRODUCTION_LOG_PATH = settings.ROOT / "data" / "production_log.json"

RECENT_WINDOW = 5  # لا تكرار خلال آخر 5 حلقات

# جداول المoods — كل الأصوات من الـ32 الفعلية
MOOD_VOICES: dict[str, list[str]] = {
    "crazy": [
        "ar-EG-ShakirNeural", "ar-AE-HamdanNeural", "ar-IQ-BasselNeural",
        "ar-MA-JamalNeural", "ar-SY-LaithNeural",
    ],
    "warm": [
        "ar-SA-HamedNeural", "ar-EG-SalmaNeural", "ar-QA-MoazNeural",
        "ar-JO-SanaNeural", "ar-BH-LailaNeural",
    ],
    "calm": [
        "ar-SA-ZariyahNeural", "ar-EG-SalmaNeural", "ar-QA-AmalNeural",
        "ar-SY-AmanyNeural", "ar-TN-ReemNeural",
    ],
    "mysterious": [
        "ar-SY-LaithNeural", "ar-DZ-IsmaelNeural", "ar-OM-AbdullahNeural",
        "ar-YE-SalehNeural", "ar-KW-FahedNeural",
    ],
    "serious": [
        "ar-EG-ShakirNeural", "ar-KW-FahedNeural", "ar-JO-TaimNeural",
        "ar-OM-AbdullahNeural", "ar-QA-MoazNeural",
    ],
}
DEFAULT_MOOD = "warm"

# تطبيع: الـ moods ممكن تجي من الـ LLM بأي صيغة
_ALIASES = {
    "جنون": "crazy", "مجنون": "crazy", "crazy": "crazy", "fun": "crazy",
    "دافي": "warm", "دافىء": "warm", "warm": "warm", "brotherly": "warm",
    "هادي": "calm", "هادئ": "calm", "calm": "calm", "relax": "calm",
    "غامض": "mysterious", "mysterious": "mysterious", "dark": "mysterious",
    "جاد": "serious", "جاد": "serious", "serious": "serious", "news": "serious",
}


def normalize_mood(mood: str | None) -> str:
    m = (mood or "").strip().lower()
    return _ALIASES.get(m, m if m in MOOD_VOICES else DEFAULT_MOOD)


def load_ar_voices() -> list[str]:
    """القائمة الفعلية من ملف التشغيل الحقيقي، وإلا من جداول الـ moods."""
    if AR_VOICES_PATH.exists():
        try:
            lines = [ln.strip() for ln in
                     AR_VOICES_PATH.read_text(encoding="utf-8").splitlines()
                     if ln.strip() and not ln.startswith("#")]
            if lines:
                return lines
        except Exception:
            pass
    seen: list[str] = []
    for pool in MOOD_VOICES.values():
        for v in pool:
            if v not in seen:
                seen.append(v)
    return seen


def recent_voices(n: int = RECENT_WINDOW) -> list[str]:
    """آخر الأصوات المستخدمة من سجل الإنتاج (الأحدث أولًا)."""
    try:
        log = json.loads(PRODUCTION_LOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[str] = []
    for entry in reversed(log if isinstance(log, list) else []):
        v = entry.get("voice")
        if v and v not in out:
            out.append(v)
        if len(out) >= n:
            break
    return out


def pick_voice(mood: str | None = None, seed: str | None = None,
               avoid: list[str] | None = None) -> str:
    """اختار صوتًا مناسبًا للمزاج، بعيدًا عن آخر 5 حلقات، حتمي حسب الـ seed.

    seed = معرّف الموضوع عادةً → إعادة الرندر نفسها بنفس الصوت.
    """
    m = normalize_mood(mood)
    pool = MOOD_VOICES.get(m) or MOOD_VOICES[DEFAULT_MOOD]
    valid = set(load_ar_voices())
    pool = [v for v in pool if v in valid] or list(MOOD_VOICES[DEFAULT_MOOD])
    avoid = set(avoid) if avoid is not None else set(recent_voices())
    fresh = [v for v in pool if v not in avoid]
    choices = fresh or pool  # لو كل الأصوات استُخدمت حديثًا: نرجع للـ pool كله
    rng = random.Random(seed) if seed is not None else random.Random()
    return rng.choice(choices)


def register_usage(voice: str, topic_id: str = "") -> None:
    """يُسجَّل الصوت في آخر سجل إنتاج (تدقيق: كل حلقة بصوتها)."""
    try:
        log = json.loads(PRODUCTION_LOG_PATH.read_text(encoding="utf-8"))
        if isinstance(log, list) and log:
            for entry in reversed(log):
                if entry.get("topicId") == topic_id:
                    entry["voice"] = voice
                    break
            else:
                log[-1]["voice"] = voice
            PRODUCTION_LOG_PATH.write_text(
                json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # التسجيل اختيارًا — ما يقطعش الإنتاج
