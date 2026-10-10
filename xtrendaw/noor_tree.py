"""شجرة التصنيفات — إضافة فقط.

الـ١٢ نوع اليومي ما يتمسحوش. الـ١٠٨ صنف خير يفضلوا رفًا جوّه الروح.
الشجرة دي هي الفهرس الكامل: عيلة، فرع، حالة.
الحالة:
  live   المصنع بينتجها من مصدر موجود
  linked مربوطة بمسار موجود، مش نسخة جديدة
  format شكل بصري، مش موضوع
  hold   تصنيف متسجل، ومقفول لحد ما يبقى مصدر موثوق
ممنوع تأليف آية أو حديث أو فتوى أو حلم أو خبر.
"""
from __future__ import annotations

FAMILIES = [
    {"id": "sacred", "ar": "دين مقدس", "note": "قرآن وتدبر وأسماء. النص لا يتألف."},
    {"id": "sunnah", "ar": "سنة وذكر ودعاء", "note": "حديث وأذكار وأدعية من مصدرها."},
    {"id": "story", "ar": "قصص وتاريخ نور", "note": "الأنبياء موجودة. السيرة والصحابة بمصدر فقط."},
    {"id": "spirit", "ar": "روح وسكينة", "note": "الروح القديمة والـ١٠٨ أصناف خير."},
    {"id": "knowledge", "ar": "علم وإفادة", "note": "سؤال ومعلومة وشرح، بلا خرافة."},
    {"id": "life", "ar": "حياة نافعة", "note": "بيت وصحة وطريق ورفق."},
    {"id": "soul", "ar": "فهم النفس", "note": "راحة وسؤال. الفتوى والحلم والرقية الطبية مقفولة."},
    {"id": "world", "ar": "أخبار وتاريخ عام", "note": "لا يُفتح بلا مصدر وموافقة. لا خناقة."},
    {"id": "format", "ar": "أشكال بصرية", "note": "لبس الفيديو. النيون شكل، مش دين جديد."},
]

# grade هادي: أسود أعمق، خط ذهب، خط أخضر. بلا وميض.
NEON_GRADE = (
    "eq=brightness=-0.14:contrast=1.18:saturation=0.82,"
    "drawbox=x=16:y=16:w=iw-32:h=ih-32:color=0xE8D5A3:t=4,"
    "drawbox=x=30:y=30:w=iw-60:h=ih-60:color=0x1FA97A:t=2"
)
CALM_KINDS = {
    "quran", "tafsir", "qissa", "story", "ayah", "mujiza", "hamd", "nasr", "dua",
}
NEON_KINDS = {"athkar", "asma"}

BRANCHES = [
    # ١ دين مقدس — موجود
    {"id": "quran", "ar": "قرآن كريم", "family": "sacred", "status": "live", "engine": "quran",
     "aliases": ["ديني قرآن كريم", "تلاوة"]},
    {"id": "tafsir", "ar": "تدبر", "family": "sacred", "status": "live", "engine": "tafsir"},
    {"id": "asma", "ar": "أسماء الله", "family": "sacred", "status": "live", "engine": "asma"},
    {"id": "mujiza", "ar": "معجزات", "family": "sacred", "status": "live", "engine": "mujiza"},
    {"id": "hamd", "ar": "ولله الحمد", "family": "sacred", "status": "live", "engine": "hamd"},
    {"id": "nasr", "ar": "الله غالب", "family": "sacred", "status": "live", "engine": "nasr"},
    {"id": "qfacts", "ar": "معلومة قرآنية", "family": "sacred", "status": "live", "engine": "qfacts"},
    # ٢ سنة وذكر
    {"id": "hadith", "ar": "أحاديث", "family": "sunnah", "status": "live", "engine": "hadith",
     "aliases": ["ديني أحاديث"]},
    {"id": "athkar", "ar": "أذكار", "family": "sunnah", "status": "live", "engine": "athkar",
     "aliases": ["ديني أذكار"]},
    {"id": "athkar-sabah-masaa", "ar": "أذكار الصباح والمساء", "family": "sunnah",
     "status": "live", "engine": "athkar",
     "aliases": ["ديني أذكار الصباح والمساء"],
     "note": "باب حصن المسلم نفسه، بيتقدّم في خانة الأذكار من غير حذف الباقي."},
    {"id": "dua", "ar": "أدعية", "family": "sunnah", "status": "live", "engine": "dua",
     "aliases": ["ديني أدعية"]},
    {"id": "salah", "ar": "مواقيت الصلاة", "family": "sunnah", "status": "live", "engine": "salah"},
    {"id": "hijri", "ar": "تقويم هجري", "family": "sunnah", "status": "live", "engine": "hijri"},
    # ٣ قصص
    {"id": "qissa", "ar": "قصص الأنبياء", "family": "story", "status": "live", "engine": "qissa",
     "aliases": ["ديني قصص الانبياء"]},
    {"id": "seerah", "ar": "سيرة النبي", "family": "story", "status": "hold", "engine": "",
     "note": "مقفول لحد نص سيرة موثوق. لا حكاية متألفة."},
    {"id": "sahaba", "ar": "قصص الصحابة", "family": "story", "status": "hold", "engine": "",
     "note": "مقفول لحد مصدر. لا تأليف."},
    {"id": "tarikh-ibra", "ar": "تاريخ فيه عبرة", "family": "story", "status": "hold", "engine": "",
     "aliases": ["تاريخ"]},
    # ٤ روح — الـ١٠٨ هنا
    {"id": "spirit", "ar": "روح وسكينة", "family": "spirit", "status": "live", "engine": "spirit",
     "aliases": ["ديني روحي", "راحة نفسية"]},
    {"id": "khair-108", "ar": "١٠٨ صنف خير", "family": "spirit", "status": "live", "engine": "spirit",
     "note": "نفس، خلق، ناس، بيت، عمل، طبيعة، لسان، وقت، نعمة. لا يُحذف."},
    {"id": "khair-nafs", "ar": "فرع النفس", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-khuluq", "ar": "فرع الخلق", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-nas", "ar": "فرع الناس", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-bayt", "ar": "فرع البيت", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-amal", "ar": "فرع العمل", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-tabiaa", "ar": "فرع الطبيعة", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-lisan", "ar": "فرع اللسان والقلب", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-waqt", "ar": "فرع الوقت", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "khair-niama", "ar": "فرع النعمة", "family": "spirit", "status": "linked", "engine": "spirit"},
    # ٥ علم
    {"id": "quiz", "ar": "أسئلة", "family": "knowledge", "status": "live", "engine": "quiz",
     "aliases": ["فهم الروح واسئلة"]},
    {"id": "proverb", "ar": "مثل عربي", "family": "knowledge", "status": "live", "engine": "proverb"},
    {"id": "ilm", "ar": "نور وعلم وإفادة", "family": "knowledge", "status": "linked", "engine": "qfacts",
     "aliases": ["علم وافادة"]},
    {"id": "howto", "ar": "كيف نافع", "family": "knowledge", "status": "hold", "engine": "",
     "note": "يتضاف لما تتكتب خطوات نافعة أصلية، مش نسخ قناة."},
    {"id": "lugha", "ar": "لغة", "family": "knowledge", "status": "hold", "engine": ""},
    {"id": "hirfa", "ar": "حرفة", "family": "knowledge", "status": "hold", "engine": ""},
    # ٦ حياة
    {"id": "seha", "ar": "صحة هادية", "family": "life", "status": "linked", "engine": "spirit",
     "note": "مشي وماء وراحة من أصناف الخير. بلا وعد طبي."},
    {"id": "rifq", "ar": "رفق", "family": "life", "status": "linked", "engine": "spirit"},
    {"id": "safar", "ar": "نظر في المكان", "family": "life", "status": "hold", "engine": "",
     "note": "سفر كعبرة، مش استعراض. مقفول لحد لقطات حرة وموافقة."},
    # ٧ فهم النفس — المقفل يتقفل
    {"id": "raha", "ar": "راحة نفسية", "family": "soul", "status": "linked", "engine": "spirit"},
    {"id": "ruqyah", "ar": "رقية شرعية", "family": "soul", "status": "hold", "engine": "",
     "note": "لا تُؤلَّف ولا تُدَّعى علاجًا. تفتح بنص ثابت فقط."},
    {"id": "fatwa", "ar": "فتوى", "family": "soul", "status": "hold", "engine": "",
     "note": "المصنع لا يفتي."},
    {"id": "hulm", "ar": "تفسير حلم", "family": "soul", "status": "hold", "engine": "",
     "note": "لا يُؤلَّف."},
    # ٨ أخبار
    {"id": "akhbar", "ar": "أخبار نافعة", "family": "world", "status": "hold", "engine": "",
     "aliases": ["اخبار"],
     "note": "لا خبر متألف ولا خناقة. مقفول لحد مصدر وموافقة."},
    {"id": "tarikh-aam", "ar": "تاريخ عام", "family": "world", "status": "hold", "engine": "",
     "note": "غير قصص الأنبياء. مقفول لحد مصدر."},
    # ٩ أشكال
    {"id": "fmt-neon", "ar": "شاشة سوداء مزخرفة", "family": "format", "status": "format",
     "engine": "athkar",
     "aliases": ["نيون", "ديني شاشات سوداء"],
     "note": "شكل على الأذكار وأسماء الله. التلاوة تفضل هادية."},
    {"id": "fmt-calm", "ar": "شكل هادي للتلاوة", "family": "format", "status": "format",
     "engine": "quran"},
    {"id": "fmt-variety", "ar": "شكل مختلف لكل فيديو", "family": "format", "status": "format",
     "engine": "spirit"},
    # أرفف الإنترنت النافعة — مش نسخ قنوات
    {"id": "yt-edu", "ar": "تعليم", "family": "knowledge", "status": "linked", "engine": "quiz",
     "note": "مقابل تصنيف يوتيوب Education. السؤال الموجود، والشرح الجديد مقفول."},
    {"id": "yt-science", "ar": "علم وتقنية نافعة", "family": "knowledge", "status": "linked",
     "engine": "mujiza", "note": "نظر في الخلق. بلا إعجاز متألف."},
    {"id": "yt-howto", "ar": "شرح عملي", "family": "knowledge", "status": "hold", "engine": ""},
    {"id": "yt-people", "ar": "ناس وبيت", "family": "spirit", "status": "linked", "engine": "spirit"},
    {"id": "yt-pets", "ar": "حيوان ورفق", "family": "life", "status": "linked", "engine": "spirit"},
    {"id": "yt-sport", "ar": "حركة ومشي", "family": "life", "status": "linked", "engine": "spirit",
     "note": "صحة هادية، بلا وعد رياضي."},
    {"id": "yt-give", "ar": "عطاء", "family": "life", "status": "linked", "engine": "spirit"},
    {"id": "yt-travel", "ar": "سفر وحدث", "family": "life", "status": "hold", "engine": ""},
    {"id": "yt-film", "ar": "حكاية مصورة", "family": "story", "status": "hold", "engine": "",
     "note": "لا نسخ فيلم."},
    {"id": "yt-music", "ar": "لحن تحت كلام البشر", "family": "format", "status": "hold", "engine": "",
     "note": "ممنوع تحت الشيخ. ما يتفتحش غير من music.py وبعد موافقة."},
    {"id": "yt-comedy", "ar": "مزاح نظيف", "family": "spirit", "status": "hold", "engine": "",
     "note": "بلا سخرية وبلا أذى."},
    {"id": "yt-news", "ar": "خبر", "family": "world", "status": "hold", "engine": ""},
    {"id": "yt-auto", "ar": "معرفة عملية", "family": "knowledge", "status": "hold", "engine": ""},
    {"id": "yt-game", "ar": "لعب نظيف", "family": "knowledge", "status": "linked", "engine": "quiz",
     "note": "سؤال فقط. لا لعبة عنف."},
    {"id": "islamic", "ar": "ديني إسلامي", "family": "sacred", "status": "linked", "engine": "quran",
     "note": "عيلة جامعة للمسارات الموجودة، مش مسار ينسخها."},
    {"id": "khair-1000", "ar": "ألف سيناريو خير", "family": "spirit", "status": "live", "engine": "spirit",
     "note": "إضافة على الـ١٠٨. خانة الروح تمشيهم واحد واحد."},
    {"id": "branch-index", "ar": "فهرس الفروع", "family": "knowledge", "status": "linked", "engine": "spirit",
     "note": "عناوين محسوبة يمشي عليها بوت التنظيم. لا تُنشر وحدها."},
]


def _index() -> dict[str, dict]:
    return {b["id"]: b for b in BRANCHES}


def families() -> list[dict]:
    return [dict(x) for x in FAMILIES]


def branches(status: str | None = None) -> list[dict]:
    out = []
    for b in BRANCHES:
        if status and b["status"] != status:
            continue
        out.append(dict(b))
    return out


def branch(bid: str) -> dict | None:
    b = _index().get(bid)
    return dict(b) if b else None


def is_hold(kind: str) -> bool:
    b = _index().get(kind)
    return bool(b and b["status"] == "hold")


def add_branch(spec: dict) -> dict:
    """إضافة فرع. لو المعرّف موجود، نرفض عشان مفيش استبدال."""
    bid = str(spec.get("id") or "").strip()
    if not bid:
        raise ValueError("فرع بلا معرّف")
    if bid in _index():
        raise ValueError(f"الفرع موجود ولا يُستبدل: {bid}")
    if spec.get("family") not in {f["id"] for f in FAMILIES}:
        raise ValueError("عيلة مجهولة")
    if spec.get("status") not in ("live", "linked", "format", "hold"):
        raise ValueError("حالة مجهولة")
    BRANCHES.append(dict(spec))
    return dict(spec)


def format_for(item: dict) -> str:
    """النيون شكل للكارت الديني. التلاوة تفضل هادية."""
    kind = str(item.get("kind") or "")
    plan = str(item.get("plan_kind") or "")
    if kind in CALM_KINDS or plan in CALM_KINDS or kind == "ayah":
        return "calm"
    if item.get("format") == "neon" and kind not in CALM_KINDS:
        return "neon"
    if kind in NEON_KINDS or plan in NEON_KINDS:
        return "neon"
    return "variety"


def named_present(words: list[str]) -> list[str]:
    blob = " ".join(
        " ".join([b["ar"], b["id"], " ".join(b.get("aliases") or []), b.get("note") or ""])
        for b in BRANCHES
    )
    return [w for w in words if w not in blob]
