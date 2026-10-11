"""لوحة ثابتة لكل سلسلة. العين ترجع لنفس المكان، من غير نيون ومن غير وميض."""
from __future__ import annotations

PALETTES = {
    "kitchen": {
        "keys": ("مطبخ", "طبخ"),
        "c0": "0x2A1A12",
        "c1": "0x8A5A32",
        "text": "#F6E7D4",
        "stroke": "#1A100C",
        "line": "0xE2B07A",
        "voice": "ar-EG-SalmaNeural",
        "rate": "-6%",
        "pitch": "-2Hz",
        "pause": 0.32,
    },
    "home": {
        "keys": ("بيت", "ترتيب"),
        "c0": "0x243028",
        "c1": "0x6E8A72",
        "text": "#F3F6F1",
        "stroke": "#121814",
        "line": "0xC9D7C4",
        "voice": "ar-EG-SalmaNeural",
        "rate": "-6%",
        "pitch": "-2Hz",
        "pause": 0.32,
    },
    "study": {
        "keys": ("مذاكرة", "كتاب"),
        "c0": "0x1C2430",
        "c1": "0x4E6278",
        "text": "#F4F0E6",
        "stroke": "#10141A",
        "line": "0xD7C7A2",
        "voice": "ar-EG-ShakirNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
        "pause": 0.36,
    },
    "family": {
        "keys": ("أهل", "حضور"),
        "c0": "0x2A221C",
        "c1": "0x7A5C48",
        "text": "#F7EDE4",
        "stroke": "#16110E",
        "line": "0xE4C2A8",
        "voice": "ar-EG-SalmaNeural",
        "rate": "-8%",
        "pitch": "-3Hz",
        "pause": 0.38,
    },
    "road": {
        "keys": ("طريق", "شارع"),
        "c0": "0x1A2830",
        "c1": "0x5C7A86",
        "text": "#F2F6F7",
        "stroke": "#101618",
        "line": "0xC5D5DA",
        "voice": "ar-EG-ShakirNeural",
        "rate": "-4%",
        "pitch": "-1Hz",
        "pause": 0.28,
    },
    "money": {
        "keys": ("مال", "أمانة"),
        "c0": "0x1E2420",
        "c1": "0x4E5C50",
        "text": "#F3F1EA",
        "stroke": "#101410",
        "line": "0xC8C2B0",
        "voice": "ar-EG-ShakirNeural",
        "rate": "-6%",
        "pitch": "-2Hz",
        "pause": 0.34,
    },
    "sky": {
        "keys": ("سماء", "نجم"),
        "c0": "0x101828",
        "c1": "0x2E4A68",
        "text": "#F4F7FB",
        "stroke": "#0C1018",
        "line": "0xD5DEEA",
        "voice": "ar-SA-ZariyahNeural",
        "rate": "-10%",
        "pitch": "-2Hz",
        "pause": 0.42,
    },
    "phone": {
        "keys": ("موبايل", "ستر"),
        "c0": "0x1A2030",
        "c1": "0x3E4C68",
        "text": "#F3F5F8",
        "stroke": "#10131A",
        "line": "0xC9D2E4",
        "voice": "ar-EG-SalmaNeural",
        "rate": "-4%",
        "pitch": "-1Hz",
        "pause": 0.28,
    },
    "anger": {
        "keys": ("غضب", "صبر"),
        "c0": "0x1A2428",
        "c1": "0x4A6A72",
        "text": "#F2F7F7",
        "stroke": "#101618",
        "line": "0xC5D8DC",
        "voice": "ar-EG-ShakirNeural",
        "rate": "-10%",
        "pitch": "-3Hz",
        "pause": 0.4,
    },
    "faith": {
        "keys": ("تذكير", "خالق", "توكل", "نور الله"),
        "c0": "0x1A140E",
        "c1": "0x5A4630",
        "text": "#F6E7C8",
        "stroke": "#120E0A",
        "line": "0xD4AF72",
        "voice": "ar-SA-HamedNeural",
        "rate": "-12%",
        "pitch": "-4Hz",
        "pause": 0.48,
        "sacred": True,
    },
    "default": {
        "keys": (),
        "c0": "0x1C2428",
        "c1": "0x5A6E72",
        "text": "#F4F6F5",
        "stroke": "#101416",
        "line": "0xD5DDD8",
        "voice": "ar-EG-SalmaNeural",
        "rate": "-6%",
        "pitch": "-2Hz",
        "pause": 0.34,
    },
}


def palette_for(episode: dict) -> dict:
    blob = " ".join(
        str(episode.get(k) or "")
        for k in ("series_title", "series_id", "field", "emotion")
    )
    for pid, pal in PALETTES.items():
        if pid == "default":
            continue
        if any(key in blob for key in pal["keys"]):
            out = dict(pal)
            out["id"] = pid
            return out
    out = dict(PALETTES["default"])
    out["id"] = "default"
    return out
