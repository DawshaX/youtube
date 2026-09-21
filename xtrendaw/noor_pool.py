"""مخزون محتوى نور — آيات وأذكار وأحاديث صحيحة، بمواضيع ومشاهد جاهزة.

قواعد السلامة (مبنية على سياسات يوتيوب 2026 + شروط مصادر التلاوة):

1) **النص** بيتجيب **لايف** من api.alquran.cloud (عثماني) والتفسير الميسّر —
   ممنوع نكتب آية من الذاكرة. أي خطأ في آية = ذنب + خطر.
2) **الحديث**: من مجموعات صحيحة متاحة بالـAPI (صحيح البخاري/مسلم) بالنص
   الأصلي، ومكتوب معه المصدر والرقم — ممنوع حديث ضعيف أو موضوع.
3) **التلاوة**: من cdn.islamic.network (شروطهم: استخدام تعليمي مجاني، وننسب
   القارئ، وممكن يطلبوا إزالة — عشان كده بننسب القارئ باسمه في الوصف).
4) **بلا موسيقى** — صوت التلاوة/الكلام بس. (خطر Content ID = صفر تقريبًا.)
5) **تنويع مقصود**: النوع + القارئ + الثيم + المشاهد بتتغير كل حلقة —
   سياسة «المحتوى المتشابه/المتكرر» (يوليو 2026) بتحاسب القوالب الثابتة.

كل عنصر: {id, kind, theme, hook, surah, ayah, ayah_to, reciter, scenes[], tags}
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from . import settings

POOL_PATH = settings.STATE / "noor_pool.json"

# مشاهد سينمائية (إنجليزي — المصادر الشبكية إنجليزي) — كل ثيم له مجموعته
SCENES = {
    "رحمة": ["soft rain on green leaves", "clouds sunlight rays sky",
             "calm river nature", "warm light through trees"],
    "صبر": ["desert dunes sunrise", "lone tree on hill wind",
            "mountains clouds time lapse", "rough sea rocks waves"],
    "توحيد": ["galaxy nebula stars", "night sky milky way",
              "earth from space sunrise", "universe cosmos animation"],
    "ذكر": ["mosque minaret sunset silhouette", "mosque architecture night",
            "prayer beads closeup", "sunset silhouette meditation"],
    "قرآن": ["quran book open pages", "mosque interior arches",
             "old holy quran pages", "islamic calligraphy art"],
    "نور": ["sunrise above clouds", "lighthouse night beam",
            "candle flame dark", "stars long exposure"],
    "توبة": ["dawn light horizon", "open road sunrise", "fresh green field rain",
             "light through window curtain"],
    "جنة": ["waterfall lush garden", "flowers meadow sunlight",
            "river paradise nature", "butterfly flowers closeup"],
    # (استعلامات الحديث: طبيعة وعمارة إسلامية — بلا أي وجوه أو مشاهد مش لائقة)
    "حديث": ["mosque interior arches", "prayer beads on wood",
             "rain drops green leaves", "clouds sunset sky",
             "old mosque minaret", "green trees light"],
    "أخلاق": ["green leaves rain drops closeup", "mosque courtyard arches",
              "dates fruit bowl", "trees sunlight path"],
    "وقت": ["hourglass sand closeup", "minaret clock tower",
            "sunset time lapse sky", "old lantern light"],
}

# جملة تطبيق عملية لكل ثيم (نصي أنا — نصيحة عامة، مش حكم شرعي ولا فتوى)
APPLY = {
    "رحمة": "النهاردة: افتح قلبك لحد زعلان منك، وابعت رسالة تطمّن حد بتحبه.",
    "صبر": "النهاردة: حمّلك اللي تعبك… قول «حسبي الله ونعم الوكيل» وكمّل خطوة.",
    "توحيد": "النهاردة: قبل ما تطلب من حد، اطلب من الله الأول — هو الأقرب.",
    "ذكر": "النهاردة: خصّص دقيقة واحدة لسبحان الله وبحمده… وشوف الفرق في قلبك.",
    "قرآن": "النهاردة: عيّن لنفسك صفحة واحدة بعد الفجر، وخلّيها عادة مش مرة.",
    "نور": "النهاردة: كن سبب نور لحد حزين — كلمة طيبة بتغيّر يوم كامل.",
    "توبة": "النهاردة: سيب الذنب اللي بتأجّله، وابدأ من الصلاة الجاية — الباب مفتوح.",
    "جنة": "النهاردة: اعمل عمل صغير خفي، عشان تلاقيه في يوم أنت محتاجه.",
    "أخلاق": "النهاردة: صل رحمك بمكالمة قصيرة، وابدأ بأمك.",
    "وقت": "النهاردة: اكتب أهم حاجة واحدة في يومك، وابدأ بيها قبل أي حاجة تانية.",
}

# عناصر المحتوى: آيات مع ثيمها وهوكها (النص بيتجيب لايف بالـAPI)
AYAHS = [
    # ── رحمة وطمأنينة
    {"kind": "ayah", "theme": "رحمة", "surah": 13, "ayah": 28,
     "hook": "قلبك بيدق ليه؟ ❤️"},
    {"kind": "ayah", "theme": "رحمة", "surah": 39, "ayah": 53,
     "hook": "لو غلطت ألف مرة… اسمع ده 💛"},
    {"kind": "ayah", "theme": "رحمة", "surah": 94, "ayah": 5, "ayah_to": 6,
     "hook": "همّك هينتهي 🕊️"},
    {"kind": "ayah", "theme": "رحمة", "surah": 2, "ayah": 186,
     "hook": "لما تدعي… الدعاء جنبك 🍃"},
    # ── صبر وتفريج
    {"kind": "ayah", "theme": "صبر", "surah": 2, "ayah": 153,
     "hook": "صبرك مش ضايع 🌱"},
    {"kind": "ayah", "theme": "صبر", "surah": 65, "ayah": 3,
     "hook": "خايف من المستقبل؟ ⛅"},
    {"kind": "ayah", "theme": "صبر", "surah": 3, "ayah": 200,
     "hook": "لسه فاضل شوية ويفرجها ⏳"},
    # ── توحيد وعظمة الخالق
    {"kind": "ayah", "theme": "توحيد", "surah": 2, "ayah": 255,
     "hook": "أعظم آية في القرآن 🌌"},
    {"kind": "ayah", "theme": "توحيد", "surah": 67, "ayah": 3, "ayah_to": 4,
     "hook": "بص على السماء… فيه خطأ؟ 🔭"},
    {"kind": "ayah", "theme": "توحيد", "surah": 55, "ayah": 13,
     "hook": "أي نعمة أنكرتها؟ 🌊"},
    # ── ذكر ودعاء
    {"kind": "ayah", "theme": "ذكر", "surah": 33, "ayah": 41, "ayah_to": 42,
     "hook": "دقيقة ذكر تسوى الدنيا ✨"},
    {"kind": "ayah", "theme": "ذكر", "surah": 29, "ayah": 45,
     "hook": "الصلاة مش عادة… 🕌"},
    # ── قرآن: قيام الليل والتدبر
    {"kind": "ayah", "theme": "قرآن", "surah": 73, "ayah": 1, "ayah_to": 4,
     "hook": "سِرّ القيام اللي محدش يقوله 🌙"},
    {"kind": "ayah", "theme": "قرآن", "surah": 17, "ayah": 78, "ayah_to": 79,
     "hook": "قوم الليل… المقام المحمود 🌌"},
    # ── توبة
    {"kind": "ayah", "theme": "توبة", "surah": 25, "ayah": 70,
     "hook": "باب التوبة مفتوح 🚪"},
    {"kind": "ayah", "theme": "توبة", "surah": 39, "ayah": 35,
     "hook": "بداية جديدة من هنا 🌅"},
    # ── جنة
    {"kind": "ayah", "theme": "جنة", "surah": 47, "ayah": 15,
     "hook": "تخيل الجنّة لحظة 🏞️"},
    {"kind": "ayah", "theme": "جنة", "surah": 56, "ayah": 10, "ayah_to": 12,
     "hook": "أقرب الناس لله في الجنّة 👑"},
    # ── أخلاق
    {"kind": "ayah", "theme": "أخلاق", "surah": 49, "ayah": 13,
     "hook": "مين أكرمك؟ مش فلوسك 🤲"},
    {"kind": "ayah", "theme": "أخلاق", "surah": 31, "ayah": 14,
     "hook": "أول وصية… لأمك 💐"},
    # ── وقت
    {"kind": "ayah", "theme": "وقت", "surah": 103, "ayah": 1, "ayah_to": 3,
     "hook": "خسارة العمر… سورة العصر ⏰"},
    {"kind": "ayah", "theme": "وقت", "surah": 21, "ayah": 1,
     "hook": "الحساب قرب 📜"},
]

# أحاديث صحيحة (المصدر بالـAPI — ممنوع أي حديث غير صحيح)
# المتن بيُستخرج تلقائيًا من غير الإسناد، وبيتنطق بالتعليق + بيظهر على الشاشة
HADITHS = [
    {"kind": "hadith", "theme": "أخلاق", "collection": "bukhari", "index": 13,
     "hook": "إيمانك ناقص من غير ده؟ 🤍"},
    {"kind": "hadith", "theme": "رحمة", "collection": "bukhari", "index": 69,
     "hook": "يسّروا… ولا تعسّروا 🕊️"},
    {"kind": "hadith", "theme": "ذكر", "collection": "bukhari", "index": 6407,
     "hook": "الفرق بين قلب حي وقلب ميّت ✨"},
    {"kind": "hadith", "theme": "وقت", "collection": "bukhari", "index": 35,
     "hook": "ليلة القدر… متسيبهاش 🌌"},
    {"kind": "hadith", "theme": "أخلاق", "collection": "bukhari", "index": 55,
     "hook": "مصاريف بيتك… صدقة؟ 💛"},
    {"kind": "hadith", "theme": "توحيد", "collection": "bukhari", "index": 9,
     "hook": "الإيمان 60+ شعبة… شوف أعلاها 🕌"},
    {"kind": "hadith", "theme": "رحمة", "collection": "bukhari", "index": 6011,
     "hook": "المؤمنون زي الجسد الواحد 🤝"},
    {"kind": "hadith", "theme": "قرآن", "collection": "muslim", "index": 4,
     "hook": "قبل ما تنشر حديث… شوف ده ⚠️"},
    {"kind": "hadith", "theme": "صبر", "collection": "bukhari", "index": 38,
     "hook": "شهر ويفرجها… رمضان 🕌"},
]


def _load() -> list[dict]:
    try:
        d = json.loads(POOL_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    POOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    POOL_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=1),
                         encoding="utf-8")


def history() -> list[dict]:
    return _load()


def _broken() -> set[str]:
    """العناصر اللي فشلت قبل كده (من ذاكرة المشغّل) — ما نرجّعش لها."""
    try:
        d = json.loads((settings.STATE / "noor_state.json").read_text(
            encoding="utf-8"))
        return {str(x) for x in (d.get("broken") or [])}
    except Exception:
        return set()


def pick(item_id: str | None = None) -> dict:
    """يختار عنصر ما اتعملش قبل كده (وما اتكررش في آخر 60 حلقة).

    التنويع: الثيم + القارئ + النوع بيتغيروا بالتناوب — عشان القناة ما تبقاش
    «قالب ثابت» (سياسة المحتوى المتشابه) ولأن الجمهور بيمل من نفس الصوت.
    """
    used = {str(h.get("id")) for h in history()} | _broken()
    candidates = [c for c in (AYAHS + HADITHS) if c.get("id") or True]
    fresh = []
    for c in candidates:
        key = f"{c['kind']}-{c.get('collection', c.get('surah'))}-" \
              f"{c.get('index', c.get('ayah'))}"
        c = dict(c)
        c["id"] = key
        if key in used:
            continue
        fresh.append(c)
    if item_id:
        for c in fresh:
            if c["id"] == item_id:
                return _finish(c)
    if not fresh:
        # خلص المخزون: نبدأ من الأول مع تنويع أكبر
        for c in candidates:
            key = f"{c['kind']}-{c.get('collection', c.get('surah'))}-" \
                  f"{c.get('index', c.get('ayah'))}"
            c = dict(c)
            c["id"] = key
            fresh.append(c)
    # اختيار حتمي متدرّج (بلا عشوائية محضة) عشان التنويع مضمون
    n = len(history())
    return _finish(fresh[n % len(fresh)])


def _finish(item: dict) -> dict:
    """يضيف المشاهد + القارئ بالتناوب + الثيم (+ ريلز كل ٣ حلقات)."""
    # ⚠️ الغامدي مستثنى: ملفاته ناقصة على المصدر (404) — مش قارئ معتمد عمليًا
    reciters = ["husary", "minshawi", "shatri", "abdulbasitmurattal"]
    n = len(history())
    item["reciter"] = reciters[n % len(reciters)]
    if item.get("kind") == "hadith":
        item["scenes"] = SCENES["حديث"]
    else:
        item["scenes"] = SCENES.get(item.get("theme", ""), SCENES["نور"])
    # 🎬 كل ثالث حلقة ريلز (٣ آيات بنفس الثيم + تعليق + تطبيق) لحد 3 دقايق
    if n % 3 == 2 and item.get("kind") == "ayah":
        ay = reel_ayahs(item.get("theme", ""), 3)
        if len(ay) >= 2:
            item["kind"] = "reel"
            item["ayahs"] = [{"surah": x["surah"], "ayah": x["ayah"],
                              "ayah_to": x.get("ayah_to")} for x in ay]
    return item


def reel_ayahs(theme: str, n: int = 3) -> list[dict]:
    """آيات الريل: كل آيات الثيم (بدون اللي فشلت قبل كده) لحد n آيات."""
    bad = _broken()
    out = []
    for a in AYAHS:
        if a.get("theme") != theme:
            continue
        key = f"ayah-{a['surah']}-{a['ayah']}"
        if key in bad:
            continue
        out.append(dict(a, id=key))
    return out[:max(2, n)]


def mark_done(item: dict, video: str = "", url: str = "") -> None:
    items = _load()
    items.append({"id": item.get("id"), "kind": item.get("kind"),
                  "theme": item.get("theme"), "at": __import__("time").strftime(
                      "%Y-%m-%d %H:%M", __import__("time").gmtime()),
                  "video": video, "url": url})
    _save(items[-500:])
