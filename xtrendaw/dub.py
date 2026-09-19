# الدبلجة العالمية — حلقة واحدة صوتها لغة العالم كله (مجاني 100% بـedge-tts)
# الإنجليزي جاهز فورًا (كل حلقة ليها سطور إنجليزية أصلية) —
# باقي اللغات: ترجمة ذكية بـLLM (Groq/Gemini على السحابة) ثم نطق بصوت اللغة.
from __future__ import annotations

import json

# لغات العالم المستهدفة — صوت edge الرسمي لكل لغة (رجال، طاقة عالية للشورتس)
DUB_VOICES: dict[str, tuple[str, str]] = {
    "en": ("en-US-AndrewNeural", "English"),
    "es": ("es-ES-AlvaroNeural", "Español"),
    "fr": ("fr-FR-HenriNeural", "Français"),
    "hi": ("hi-IN-MadhurNeural", "हिन्दी"),
    "pt": ("pt-BR-AntonioNeural", "Português"),
    "de": ("de-DE-ConradNeural", "Deutsch"),
    "tr": ("tr-TR-AhmetNeural", "Türkçe"),
    "id": ("id-ID-ArdiNeural", "Indonesia"),
    "ru": ("ru-RU-DmitryNeural", "Русский"),
}
DUB_ORDER = list(DUB_VOICES)

# لغات ليها نص أصلي جاهز في كل حلقة (بلا ترجمة) — تشتغل في أي مكان فورًا
NATIVE_LANGS = ("ar", "en")

_TRANSLATE_PROMPT = """ترجم عناصر الحلقة دي إلى {lang_name} بروح شورتس طبيعية
(مش ترجمة حرفية — نفس الطاقة والخطاف). ارجع JSON فقط:
{{"title_ar_dub": "...", "hook": "...", "facts": ["...", "...", "..."],
  "takeaway": {{"aql": "...", "qalb": "...", "rouh": "..."}}}}

العنوان: {title}
الخطاف: {hook}
الحقائق: {facts}
الخلاصة: {takeaway}
"""


def voice_for(lang: str) -> str:
    """صوت edge الرسمي للغة — لغة مش مدعومة = خطأ واضح مش صوت غلط."""
    if lang == "ar":
        raise ValueError("ar أصلًا لغة الحلقة الأم — مفيش دبلجة")
    try:
        return DUB_VOICES[lang][0]
    except KeyError:
        raise ValueError(f"دبلجة {lang} مش مدعومة بعد — المتاح: {', '.join(DUB_ORDER)}")


def rotate(status_langs: list[str]) -> str:
    """الدورة العالمية: كل رندر دبلجة بلغة مختلفة (بلا تكرار داخل النافذة)."""
    done = set(status_langs[-len(DUB_ORDER):])
    for lang in DUB_ORDER:
        if lang not in done:
            return lang
    return DUB_ORDER[0]


def _llm_ok() -> bool:
    from . import settings
    return settings.has_llm()


def translate_topic(topic: dict, lang: str) -> dict | None:
    """ترجمة ذكية لعناصر الحلقة للغة الدبلجة — بلا LLM = بلا ترجمة (بأمانة)."""
    if lang in NATIVE_LANGS:
        return topic  # نص أصلي جاهز
    if not _llm_ok():
        return None
    from . import eye
    tk = topic.get("takeaway_ar") or {}
    raw = eye._llm_json(_TRANSLATE_PROMPT.format(
        lang_name=DUB_VOICES[lang][1],
        title=topic.get("title_ar", ""), hook=topic.get("hook_ar", ""),
        facts=json.dumps(topic.get("facts_ar", []), ensure_ascii=False),
        takeaway=json.dumps(tk, ensure_ascii=False)))
    if not raw or not raw.get("hook") or not raw.get("facts"):
        return None
    dubbed = dict(topic)
    dubbed["id"] = f"{topic['id']}-{lang}"
    dubbed["title_ar"] = raw.get("title_ar_dub") or topic.get("title_en", "")
    dubbed["hook_ar"] = raw["hook"]
    dubbed["facts_ar"] = raw["facts"][:3]
    if isinstance(raw.get("takeaway"), dict):
        dubbed["takeaway_ar"] = raw["takeaway"]
    dubbed["_dub_of"] = topic.get("id")
    dubbed["_dub_lang"] = lang
    return dubbed


def dub_topic_for(topic: dict, lang: str) -> dict | None:
    """موضوع جاهز للرندر باللغة المطلوبة — None = اللغة دي مش جاهزة النهاردة."""
    if lang == "ar":
        return None
    if lang == "en":
        t = dict(topic)
        t["id"] = f"{topic['id']}-en"
        t["_dub_of"] = topic.get("id")
        t["_dub_lang"] = "en"
        return t
    return translate_topic(topic, lang)
