"""حلقة مكتوبة تبقى خط زمني. المدة من الكلام، والحركة هادية."""
from __future__ import annotations

import re

from .palettes import palette_for

SACRED_MARKS = ("﴿", "﴾", "قال رسول", "صلى الله", "آية رقم", "سورة ")
W, H, FPS = 1080, 1920, 24
MAX_ZOOM = 0.08
FADE_FRAMES = 10


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.؟!])\s+", (text or "").strip())
    out = []
    for part in parts:
        part = part.strip()
        if part and part not in out:
            out.append(part if part.endswith((".", "؟", "!")) else part + ".")
    return out


def sacred_text(text: str) -> bool:
    return any(mark in (text or "") for mark in SACRED_MARKS)


def build(episode: dict) -> dict:
    spoken = (episode.get("spoken") or "").strip()
    if not spoken:
        raise ValueError("الحلقة من غير كلام")
    if sacred_text(spoken):
        raise ValueError("النص المقدس من مصدره وتلاوته، ومش بيتنطق من هنا")
    pal = palette_for(episode)
    lines = sentences(spoken)
    if not lines:
        raise ValueError("مفيش جمل تتقسم")
    shots = []
    for i, line in enumerate(lines):
        shots.append({
            "i": i,
            "say": line,
            "visual": "card",
            "query": episode.get("scene") or "calm empty scene no people",
            "zoom": MAX_ZOOM,
            "fade_frames": FADE_FRAMES,
            "caption_lines_max": 2,
        })
    return {
        "id": episode.get("id") or "episode",
        "series_id": episode.get("series_id") or "",
        "series_title": episode.get("series_title") or "",
        "kind": episode.get("kind") or "short",
        "benefit": episode.get("benefit") or "",
        "canvas": {"w": W, "h": H, "fps": FPS},
        "palette": {k: pal[k] for k in ("id", "c0", "c1", "text", "stroke", "line", "voice", "rate", "pitch", "pause") if k in pal},
        "sacred_series": bool(pal.get("sacred")),
        "music": None,
        "faces": False,
        "flash_max_per_second": 3,
        "shots": shots,
        "rules": [
            "المدة من الكلام مش من صمت",
            "تقريب أقصاه ٨٪",
            "من غير وجوه ومن غير وميض",
            "الكابشن في الوسط المريح",
            "الموسيقى مش موجودة لحد ما تدخل الخزنة بترخيص",
            "النص المقدس ما يتألفش هنا",
        ],
        "publish": False,
        "factory_live": False,
    }
