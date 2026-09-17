"""محلل الترند — الطبقة ٢ من البلوبرنت.

يقرا `data/radar_snapshot.json` (مخرَج الرادار) ويطلع `data/patterns.json`:
  * سرعة كل فيديو: `velocity = viewCount / hoursSincePublish`
  * معدل الإعجاب لكل ألف مشاهدة
  * بنية العناوين: طول، سؤال، رقم، إيموجي (قياس بنية فقط — بند ٠/٥)
  * توزيع الفئات (`topicCategories`) على الرائج

مفيش أي حاجة بتتعلم من نصوص الآخرين — أرقام وبنى بس. لو مفيش مسْح
رادار: فشل صريح بدل بيانات متخيلة.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import unicodedata
from collections import Counter

from . import settings

SNAPSHOT_PATH = settings.ROOT / "data" / "radar_snapshot.json"
PATTERNS_PATH = settings.ROOT / "data" / "patterns.json"

_EMOJI_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF" "\u2190-\u21FF" "\u2B00-\u2BFF" "]")


def _hours_since(published_at: str, now: dt.datetime) -> float:
    try:
        pub = dt.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return max(1.0, (now - pub).total_seconds() / 3600.0)
    except Exception:
        return 0.0


def _title_structure(title: str) -> dict:
    return {
        "length": len(title),
        "is_question": ("؟" in title) or ("?" in title),
        "has_number": bool(re.search(r"\d", title)),
        "has_emoji": bool(_EMOJI_RE.search(title)),
        "has_exclaim": ("!" in title) or ("؟!" in title),
    }


def _fastest(videos: list[dict], now: dt.datetime, top: int = 25) -> list[dict]:
    scored = []
    for v in videos:
        hrs = _hours_since(v.get("publishedAt", ""), now)
        if not hrs:
            continue
        velocity = v.get("viewCount", 0) / hrs
        scored.append({
            "videoId": v["videoId"],
            "region": v.get("region"),
            "via": v.get("via"),
            "categoryId": v.get("categoryId"),
            "velocityPerHour": round(velocity),
            "likeRatePer1k": round(
                1000.0 * v.get("likeCount", 0) / max(1, v.get("viewCount", 1)), 2),
            "titleStructure": _title_structure(v.get("title", "")),
        })
    scored.sort(key=lambda s: -s["velocityPerHour"])
    return scored[:top]


def analyze() -> dict:
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError(
            "analyzer: مفيش مسح رادار — شغّل `python -m xtrendaw.radar` الأول.")
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    videos = snap.get("videos", [])
    if not videos:
        raise RuntimeError("analyzer: مسح الرادار فاضي — مفيش حاجة تتحلل.")

    now = dt.datetime.now(dt.timezone.utc)
    fastest = _fastest(videos, now)

    cats = Counter(v.get("categoryId", "") for v in videos if v.get("categoryId"))
    structures = [_title_structure(v.get("title", "")) for v in videos]
    n = max(1, len(structures))

    patterns = {
        "analyzedAt": now.isoformat(timespec="seconds"),
        "snapshotAt": snap.get("scannedAt"),
        "videoCount": len(videos),
        "fastest": fastest,
        "categoryShare": {c: {"count": k, "share": round(k / len(videos), 3)}
                          for c, k in cats.most_common()},
        "titlePatterns": {
            "avgLength": round(sum(s["length"] for s in structures) / n, 1),
            "questionRate": round(sum(s["is_question"] for s in structures) / n, 3),
            "numberRate": round(sum(s["has_number"] for s in structures) / n, 3),
            "emojiRate": round(sum(s["has_emoji"] for s in structures) / n, 3),
            "exclaimRate": round(sum(s["has_exclaim"] for s in structures) / n, 3),
        },
    }
    PATTERNS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PATTERNS_PATH.write_text(json.dumps(patterns, ensure_ascii=False, indent=1),
                             encoding="utf-8")
    return patterns


if __name__ == "__main__":
    try:
        p = analyze()
        print(f"analyzer: {p['videoCount']} فيديو → "
              f"{len(p['fastest'])} أسرع — {PATTERNS_PATH.name}")
        print("titlePatterns:", json.dumps(p["titlePatterns"], ensure_ascii=False))
    except RuntimeError as exc:
        print(f"analyzer: {exc}", file=sys.stderr)
        sys.exit(2)
