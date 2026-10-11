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
    if "حزن" in blob or "صبر" in blob:
        return _ready(SOULS[4])
    series = " ".join(str(episode.get(k) or "") for k in ("series_title", "field", "emotion"))
    if any(key in series for key in COURT_KEYS):
        court = [s for s in SOULS if s.get("court")]
        n = sum(ord(c) for c in str(episode.get("id") or "نور"))
        return _ready(court[n % len(court)])
    pool = [s for s in SOULS if not s.get("child") and not s.get("court") and not (s.get("neon") and "علم" not in blob and "لحظة" not in blob)]
    if not pool:
        pool = [s for s in SOULS if not s.get("child")]
    n = sum(ord(c) for c in str(episode.get("id") or "نور"))
    matched = [s for s in pool if any(k in blob for k in s.get("fits") or ())]
    chosen = matched or pool
    return _ready(chosen[n % len(chosen)])


def _ready(soul: dict) -> dict:
    out = dict(soul)
    out["path"] = ROOT / out["file"]
    return out


def portrait(soul: dict | None) -> Path | None:
    if not soul:
        return None
    path = ROOT / soul["file"]
    return path if path.exists() else None
