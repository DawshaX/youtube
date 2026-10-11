"""شخصيات أصلية للمصنع. مش وجوه ناس حقيقيين، ومش تقليد شيخ أو مشهور."""
from __future__ import annotations

from pathlib import Path

from .palettes import palette_for

ROOT = Path(__file__).resolve().parents[2] / "assets" / "souls"

SOULS = (
    {
        "id": "nour",
        "name": "نور",
        "style": "cartoon",
        "voice": "ar-EG-SalmaNeural",
        "rate": "-6%",
        "pitch": "-2Hz",
        "mark": "#E2B07A",
        "file": "nour.png",
        "neon": False,
        "fits": ("هزار", "حب", "حياة", "مطبخ", "بيت"),
    },
    {
        "id": "siraj",
        "name": "سراج",
        "style": "clay3d",
        "voice": "ar-EG-ShakirNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
        "mark": "#7D9A78",
        "file": "siraj.png",
        "neon": False,
        "fits": ("علم", "وعي", "جد", "مذاكرة"),
    },
    {
        "id": "lama",
        "name": "لمى",
        "style": "neon",
        "voice": "ar-SA-ZariyahNeural",
        "rate": "-4%",
        "pitch": "0Hz",
        "mark": "#7EE0E0",
        "file": "lama.png",
        "neon": True,
        "fits": ("علم", "لحظة"),
    },
    {
        "id": "ward",
        "name": "ورد",
        "style": "cartoon",
        "voice": "ar-EG-SalmaNeural",
        "rate": "-2%",
        "pitch": "+1Hz",
        "mark": "#F0C85A",
        "file": "ward.png",
        "neon": False,
        "child": True,
        "fits": ("طفل",),
        "note": "صوت بالغ هادي، مش تقليد صوت طفل.",
    },
    {
        "id": "sakan",
        "name": "سَكَن",
        "style": "dusk",
        "voice": "ar-JO-SanaNeural",
        "rate": "-10%",
        "pitch": "-3Hz",
        "mark": "#B7A8C9",
        "file": "sakan.png",
        "neon": False,
        "fits": ("حزن", "وعي", "صبر"),
    },
    {
        "id": "fajr",
        "name": "فجر",
        "style": "clay3d",
        "voice": "ar-AE-HamdanNeural",
        "rate": "-6%",
        "pitch": "-1Hz",
        "mark": "#E7B089",
        "file": "fajr.png",
        "neon": False,
        "fits": ("طريق", "سماء", "أمل"),
    },
    {
        "id": "malika",
        "name": "ملكة النور",
        "style": "queen",
        "voice": "ar-LB-LaylaNeural",
        "rate": "-6%",
        "pitch": "-1Hz",
        "mark": "#E7C98A",
        "file": "malika.png",
        "neon": False,
        "court": True,
        "fits": ("جمال", "ملكة", "ضيافة"),
        "note": "ملكة أصلية. مش ملكة جمال حقيقية.",
    },
    {
        "id": "qamar",
        "name": "قمر",
        "style": "queen",
        "voice": "ar-AE-FatimaNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
        "mark": "#D5DDEA",
        "file": "qamar.png",
        "neon": False,
        "court": True,
        "fits": ("قمر", "سماء", "ليل"),
    },
    {
        "id": "yasmin",
        "name": "ياسمين",
        "style": "queen",
        "voice": "ar-KW-NouraNeural",
        "rate": "-5%",
        "pitch": "0Hz",
        "mark": "#C96B7A",
        "file": "yasmin.png",
        "neon": False,
        "court": True,
        "fits": ("ورد", "ضيافة", "رفق"),
    },
    {
        "id": "nada",
        "name": "ندى",
        "style": "queen",
        "voice": "ar-QA-AmalNeural",
        "rate": "-7%",
        "pitch": "-1Hz",
        "mark": "#B7CDB8",
        "file": "nada.png",
        "neon": False,
        "court": True,
        "fits": ("مطر", "ندى", "رفق"),
    },
    {
        "id": "sana",
        "name": "سنا",
        "style": "soul",
        "voice": "ar-MA-MounaNeural",
        "rate": "-10%",
        "pitch": "-2Hz",
        "mark": "#F3E2B8",
        "file": "sana.png",
        "neon": False,
        "court": True,
        "fits": ("روح", "سماء", "لحظة"),
        "note": "روح نور أصلية. مش ملك، ومش بتقرأ قرآن.",
    },
    {
        "id": "bahi",
        "name": "بهي",
        "style": "soul",
        "voice": "ar-LB-RamiNeural",
        "rate": "-8%",
        "pitch": "-3Hz",
        "mark": "#E6D3A8",
        "file": "bahi.png",
        "neon": False,
        "court": True,
        "fits": ("روح", "سماء", "ألوان"),
        "note": "روح نور أصلية. مش شيخ.",
    },
    {
        "id": "layl",
        "name": "ليل",
        "style": "queen",
        "voice": "ar-OM-AyshaNeural",
        "rate": "-7%",
        "pitch": "-2Hz",
        "mark": "#1F6B45",
        "file": "layl.png",
        "neon": False,
        "court": True,
        "fits": ("ليل", "جمال", "ملكة"),
        "note": "ملكة أصلية. مش ملكة جمال حقيقية.",
    },
    {
        "id": "zahr",
        "name": "زهر",
        "style": "queen",
        "voice": "ar-BH-LailaNeural",
        "rate": "-6%",
        "pitch": "-1Hz",
        "mark": "#E07A62",
        "file": "zahr.png",
        "neon": False,
        "court": True,
        "fits": ("زهر", "جمال", "ضيافة"),
        "note": "ملكة أصلية. مش ملكة جمال حقيقية.",
    },
    {
        "id": "lamis",
        "name": "لميس",
        "style": "soul",
        "voice": "ar-TN-ReemNeural",
        "rate": "-9%",
        "pitch": "-2Hz",
        "mark": "#F4E7D4",
        "file": "lamis.png",
        "neon": False,
        "court": True,
        "fits": ("روح", "وهم", "عبرة"),
        "note": "روح نور أصلية. مش بتقرأ قرآن.",
    },
    {
        "id": "sahab",
        "name": "سحاب",
        "style": "soul",
        "voice": "ar-YE-SalehNeural",
        "rate": "-10%",
        "pitch": "-3Hz",
        "mark": "#C9D4EA",
        "file": "sahab.png",
        "neon": False,
        "court": True,
        "fits": ("روح", "سماء", "مطر"),
        "note": "روح نور أصلية. مش شيخ.",
    },
    {
        "id": "falfa",
        "name": "فلفلة",
        "style": "cartoon",
        "voice": "ar-LY-OmarNeural",
        "rate": "-2%",
        "pitch": "+1Hz",
        "mark": "#F0A202",
        "file": "falfa.png",
        "neon": False,
        "wild": True,
        "fits": ("ضحك", "نكشة", "زحمة", "موبايل"),
        "note": "شخصية هزار أصلية. مش شخص حقيقي.",
    },
    {
        "id": "barq",
        "name": "برق",
        "style": "sport",
        "voice": "ar-QA-MoazNeural",
        "rate": "-4%",
        "pitch": "0Hz",
        "mark": "#F2C14E",
        "file": "barq.png",
        "neon": False,
        "wild": True,
        "fits": ("ملعب",),
        "note": "رياضي أصلي. مش لاعب مشهور.",
    },
    {
        "id": "san3a",
        "name": "صنعة",
        "style": "clay3d",
        "voice": "ar-IQ-RanaNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
        "mark": "#C4A46A",
        "file": "san3a.png",
        "neon": False,
        "wild": True,
        "fits": ("حرفة", "شغل"),
    },
    {
        "id": "lughz",
        "name": "لُغز",
        "style": "neon",
        "voice": "ar-DZ-AminaNeural",
        "rate": "-4%",
        "pitch": "0Hz",
        "mark": "#3DDCFF",
        "file": "lughz.png",
        "neon": True,
        "wild": True,
        "fits": ("سؤال", "امتحان"),
    },
    {
        "id": "tina",
        "name": "طينة",
        "style": "clay3d",
        "voice": "ar-DZ-IsmaelNeural",
        "rate": "-6%",
        "pitch": "-1Hz",
        "mark": "#7EB0D6",
        "file": "tina.png",
        "neon": False,
        "open": True,
        "note": "أسلوب طين أزرق. شخصية أصلية، مش منسوخة من بينترست.",
    },
    {
        "id": "mahna",
        "name": "مهنة",
        "style": "flat",
        "voice": "ar-JO-TaimNeural",
        "rate": "-6%",
        "pitch": "-2Hz",
        "mark": "#C46B4A",
        "file": "mahna.png",
        "neon": False,
        "open": True,
        "note": "رسم مسطّح أصلي. مش صورة من بينترست.",
    },
    {
        "id": "mayya",
        "name": "مائي",
        "style": "watercolor",
        "voice": "ar-SY-AmanyNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
        "mark": "#7BA3A0",
        "file": "mayya.png",
        "neon": False,
        "open": True,
        "note": "مائي أصلي. مش لوحة حد تاني.",
    },
    {
        "id": "pastel",
        "name": "باستيل",
        "style": "pastel",
        "voice": "ar-YE-MaryamNeural",
        "rate": "-6%",
        "pitch": "0Hz",
        "mark": "#C9A6D8",
        "file": "pastel.png",
        "neon": False,
        "open": True,
        "note": "باستيل أصلي. مش رسم منسوخ.",
    },
    {
        "id": "mudalla",
        "name": "مُضلّع",
        "style": "lowpoly",
        "voice": "ar-BH-AliNeural",
        "rate": "-5%",
        "pitch": "-1Hz",
        "mark": "#E07A3D",
        "file": "mudalla.png",
        "neon": False,
        "open": True,
        "note": "لو بولي أصلي. مش شخصية محفوظة.",
    },
)

GENRES = (
    (("ضحك", "نكشة", "زحمة", "موبايل"), "falfa"),
    (("ملعب",), "barq"),
    (("حرفة", "شغل"), "san3a"),
    (("سؤال", "امتحان"), "lughz"),
    (("وهم", "عبرة"), "lamis"),
)

COURT_KEYS = ("رفق", "ضيافة", "سماء", "ألوان", "مطر", "لحظة", "جمال", "ملكة", "روح", "قمر")


def face_allowed(episode: dict) -> bool:
    """التلاوة والتذكير الديني من غير وجه. ما فيش شيخ متصنع."""
    pal = palette_for(episode)
    if pal.get("sacred"):
        return False
    blob = " ".join(str(episode.get(k) or "") for k in ("series_title", "field", "emotion", "spoken"))
    blocked = ("تلاوة", "حديث", "آية", "سورة", "قال رسول", "شيخ")
    return not any(mark in blob for mark in blocked)


def pick_soul(episode: dict, feeling: str = "") -> dict | None:
    if not face_allowed(episode):
        return None
    blob = " ".join(
        str(episode.get(k) or "")
        for k in ("series_title", "field", "emotion", "id")
    ) + " " + feeling
    if "طفل" in blob:
        return _ready(SOULS[3])
    # أي نوع حياة يقدر ياخد أي شخصية. التلاوة والطفل بس هم الاستثناء.
    pool = [s for s in SOULS if not s.get("child")]
    n = sum(ord(c) for c in str(episode.get("id") or "نور"))
    return _ready(pool[n % len(pool)])


def _named(sid: str) -> dict:
    for soul in SOULS:
        if soul["id"] == sid:
            return _ready(soul)
    raise KeyError(sid)


def _ready(soul: dict) -> dict:
    out = dict(soul)
    out["path"] = ROOT / out["file"]
    return out


def portrait(soul: dict | None) -> Path | None:
    if not soul:
        return None
    path = ROOT / soul["file"]
    return path if path.exists() else None
