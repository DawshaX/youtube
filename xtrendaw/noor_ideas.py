"""💡 مكتبة الأفكار — بتكبر من مصادر حرة، ومش بتؤلّف نصًا دينيًا.

طبقتين:
  ١) بذور المصنع (زوايا ودعوات) — تأليف المصنع، مش اقتباس كتاب.
  ٢) حصاد بحث القرآن من alquran.cloud: كل نتيجة بطاقة (سورة:آية + مقتطف).
     البطاقة «محكمة» بس لو الكلمة واقفة لوحدها، مش قطعة من كلمة تانية.
     الحصاد مادة أفكار للاستوديو. النشر بياخد النص من الـAPI وقت الرندر.

الذكاء (Groq/Gemini) لو المفتاح موجود: يقترح جمل بحث مشاهد بالإنجليزي فقط.
ممنوع يكتب آية أو حديث أو حكم شرعي.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "NoorFactory/1.0 (idea library; free sources)"}
# كلمات البحث — كلها عامة ومفيدة، والحصاد بيتفلتر
KEYWORDS = [
    "الحمد", "نعمة", "رحمة", "شكر", "صبر", "سكينة", "خير", "فرج",
    "توكل", "هداية", "نور", "سلام", "بر", "إحسان", "تقوى", "ذكر",
    "يغفر", "يهدي", "يرزق", "رحيم", "عليم", "حكيم", "توبوا", "استغفر",
]
# محتوى عقابي/عنيف ما يدخلش مكتبة الأفكار العالمية
BLOCK = ("قتل", "اقتل", "رجم", "جلد", "سبي", "زنا", "سيف", "جهاد",
         "لعن", "قاتل", "دما", "حد ")

SEEDS = [
    {"kind": "quran", "angle": "آية تفتح بيها اليوم", "scenes": "sunrise clouds"},
    {"kind": "quran", "angle": "آية قبل النوم", "scenes": "night sky calm"},
    {"kind": "tafsir", "angle": "معنى آية الناس بتقرأها وبتعدّي", "scenes": "open book light"},
    {"kind": "hadith", "angle": "حديث قصير يغيّر معاملة اليوم", "scenes": "olive tree"},
    {"kind": "qissa", "angle": "قصة نبي من غير قطع", "scenes": "desert dawn"},
    {"kind": "qissa", "angle": "عبرة القصة في جملة واحدة آخر الفيديو", "scenes": "mountain path"},
    {"kind": "asma", "angle": "اسم من الأسماء ودليله من القرآن", "scenes": "stars milky way"},
    {"kind": "athkar", "angle": "ذكر الصباح بجملة تحسها", "scenes": "morning mist"},
    {"kind": "dua", "angle": "دعاء قرآني… اكتب آمين", "scenes": "rain on leaves"},
    {"kind": "quiz", "angle": "من أي سورة؟ التعليق هو الإجابة", "scenes": "geometric gold"},
    {"kind": "spirit", "angle": "دقيقة سكينة لكل الناس", "scenes": "forest light"},
    {"kind": "spirit", "angle": "امتنان من غير وعظ", "scenes": "wheat field"},
    {"kind": "mujiza", "angle": "معجزة من نص الآية فقط", "scenes": "moon over water"},
    {"kind": "hamd", "angle": "نعمة واحدة… والحمد لله", "scenes": "fruit still life"},
    {"kind": "nasr", "angle": "مع العسر يسر — من غير مبالغة", "scenes": "dawn after storm"},
    {"kind": "nasr", "angle": "الله لطيف… خيره دائم", "scenes": "green valley rain"},
]


def _bare(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.replace("ٱ", "ا").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ة", "ه").replace("ى", "ي")
    return t


def tight(text: str, keyword: str) -> bool:
    """الكلمة واقفة لوحدها، مش جوه كلمة تانية (فرج ≠ فرجالا)."""
    hay = _bare(text)
    needle = _bare(keyword)
    if not needle or needle not in hay:
        return False
    return re.search(rf"(^|[^\u0600-\u06FF]){re.escape(needle)}($|[^\u0600-\u06FF])", hay) is not None


def blocked(text: str) -> bool:
    b = _bare(text)
    return any(_bare(w) in b for w in BLOCK)


def harvest(keywords: list[str] | None = None, limit_per: int = 40,
            timeout: int = 25) -> list[dict]:
    """بطاقات من بحث القرآن. الفاشل يتجاهل الكلمة ويكمل."""
    out = []
    for kw in (keywords or KEYWORDS):
        url = ("https://api.alquran.cloud/v1/search/"
               + urllib.parse.quote(kw) + "/all/quran-uthmani")
        try:
            req = urllib.request.Request(url, headers=UA)
            data = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
            matches = (data.get("data") or {}).get("matches") or []
        except Exception:
            continue
        kept = 0
        for m in matches:
            text = str(m.get("text") or "")
            if blocked(text) or not tight(text, kw):
                continue
            surah = (m.get("surah") or {}).get("number")
            ayah = m.get("numberInSurah")
            if not surah or not ayah:
                continue
            out.append({
                "kind": "quran-lead",
                "keyword": kw,
                "surah": int(surah),
                "ayah": int(ayah),
                "tight": True,
                "snippet": text[:140],
                "source": "api.alquran.cloud",
            })
            kept += 1
            if kept >= limit_per:
                break
    # إزالة التكرار
    seen = set()
    uniq = []
    for c in out:
        k = (c["surah"], c["ayah"], c["keyword"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return uniq


def suggest_scenes(theme: str) -> list[str] | None:
    """اقتراح ٣ جمل بحث مشاهد. None لو مفيش مفتاح أو الرد مش ظابط."""
    key = os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY")
    base = os.environ.get("LLM_API_BASE") or "https://api.groq.com/openai/v1"
    model = os.environ.get("LLM_MODEL") or "llama-3.3-70b-versatile"
    if not key:
        gkey = os.environ.get("GEMINI_API_KEY")
        if not gkey:
            return None
        return _gemini_scenes(gkey, theme)
    prompt = (
        "Return a JSON array of 3 short English stock-video search queries. "
        "Theme: " + theme + ". "
        "Rules: nature, sky, water, light, empty architecture. "
        "No faces, no text, no weapons, no blood, no music. "
        "No religious quotes. JSON only."
    )
    body = json.dumps({
        "model": model,
        "temperature": 0.4,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "NoorFactory/1.0"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=12).read())
        text = data["choices"][0]["message"]["content"]
        arr = json.loads(text[text.find("["): text.rfind("]") + 1])
        scenes = [str(x).strip() for x in arr if str(x).strip()][:3]
        return scenes or None
    except Exception:
        return None


def _gemini_scenes(key: str, theme: str) -> list[str] | None:
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-2.0-flash:generateContent?key=" + urllib.parse.quote(key))
    prompt = (
        "JSON array of 3 English nature video search queries for theme "
        + theme + ". No faces, no weapons, no quotes. JSON only."
    )
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "NoorFactory/1.0"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=12).read())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        arr = json.loads(text[text.find("["): text.rfind("]") + 1])
        return [str(x).strip() for x in arr if str(x).strip()][:3] or None
    except Exception:
        return None


def build_library(harvested: list[dict] | None = None) -> dict:
    cards = list(SEEDS)
    leads = harvested if harvested is not None else []
    return {
        "types": 12,
        "seeds": len(SEEDS),
        "leads": len(leads),
        "rule": "النص الديني من الـAPI وقت الرندر. البطاقة فكرة ومشهد بس.",
        "seeds_list": cards,
        "leads_list": leads,
    }


def save(path: Path, harvested: list[dict] | None = None) -> dict:
    lib = build_library(harvested)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lib, ensure_ascii=False), encoding="utf-8")
    return lib
