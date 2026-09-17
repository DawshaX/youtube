"""رادار الترند — الطبقة ١ من البلوبرنت.

يقيس **بنية** الفيديوهات الرائجة فقط (طول العنوان، سرعة المشاهد، الفئة،
توقيت الظهور الأول) — بلا أي نسخ لمحتوى أو نصوص أو مشاهد (بند ٠/٥).

المصادر:
  * `videos.list` بـ `chart=mostPopular` لبلاد: مصر، السعودية، الإمارات،
    أمريكا، الهند، البرازيل، إندونيسيا.
  * `search.list` (order=viewCount · publishedAfter=آخر 30 يوم) لكلمات الفئة.

المخرج: `data/radar_snapshot.json` — كل فيديو بمعرّفه وتاريخ أول ظهور
(`firstSeenAt`) عشان المحلل يحسب السرعة بين المسحات المتتالية.

محتاج `YOUTUBE_API_KEY` (قراءة فقط). بلا مفتاح: رسالة صريحة ورمز خروج ٢ —
مفيش فشل صامت ولا بيانات متخيلة.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import requests

from . import settings

REGIONS = ("EG", "SA", "AE", "US", "IN", "BR", "ID")
SEARCH_TERMS = ("حقائق", "معلومات", "تحدي", "اغرب", "لن تصدق", "مقارنة")
SNAPSHOT_PATH = settings.ROOT / "data" / "radar_snapshot.json"
API = "https://www.googleapis.com/youtube/v3"


def _get(endpoint: str, **params) -> dict:
    params["key"] = settings.YOUTUBE_API_KEY
    r = requests.get(f"{API}/{endpoint}", params=params, timeout=25)
    r.raise_for_status()
    return r.json()


def _popular(region: str) -> list[dict]:
    data = _get("videos", part="snippet,statistics,contentDetails",
                chart="mostPopular", regionCode=region, maxResults=25)
    return data.get("items", [])


def _search(term: str, region: str) -> list[dict]:
    after = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = _get("search", part="snippet", q=term, type="video",
                order="viewCount", publishedAfter=after,
                regionCode=region, maxResults=15)
    ids = [i["id"]["videoId"] for i in data.get("items", [])
           if i.get("id", {}).get("videoId")]
    if not ids:
        return []
    data = _get("videos", part="snippet,statistics,contentDetails",
                id=",".join(ids), maxResults=50)
    return data.get("items", [])


def _digest(item: dict, region: str, via: str) -> dict:
    sn = item.get("snippet", {})
    st = item.get("statistics", {})
    return {
        "videoId": item.get("id", ""),
        "region": region,
        "via": via,
        "title": sn.get("title", ""),
        "channel": sn.get("channelTitle", ""),
        "publishedAt": sn.get("publishedAt", ""),
        "categoryId": sn.get("categoryId", ""),
        "duration": (item.get("contentDetails") or {}).get("duration", ""),
        "viewCount": int(st.get("viewCount") or 0),
        "likeCount": int(st.get("likeCount") or 0),
    }


def scan() -> dict:
    if not settings.YOUTUBE_API_KEY:
        raise RuntimeError(
            "radar: محتاج YOUTUBE_API_KEY (قراءة فقط) — ضيفه في أسرار "
            "المستودع على الجيت هاب أو في البيئة المحلية.")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    seen: dict[str, dict] = {}

    for region in REGIONS:
        try:
            for it in _popular(region):
                d = _digest(it, region, "mostPopular")
                seen[d["videoId"]] = d
        except Exception as exc:  # بلد واحدة وقعت ما توقفش المسح كله
            print(f"radar: mostPopular({region}) فشلت: {exc}", file=sys.stderr)

    for term in SEARCH_TERMS:
        try:
            for it in _search(term, "EG"):
                d = _digest(it, "EG", f"search:{term}")
                seen.setdefault(d["videoId"], d)
        except Exception as exc:
            print(f"radar: search({term}) فشلت: {exc}", file=sys.stderr)

    # أول ظهور: لو الفيديو متسجل في مسح سابق احتفظ بتاريخه الأصلي
    prev = {}
    if SNAPSHOT_PATH.exists():
        try:
            prev = {v["videoId"]: v for v in
                    json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
                    .get("videos", [])}
        except Exception:
            prev = {}
    for vid, d in seen.items():
        d["firstSeenAt"] = prev.get(vid, {}).get("firstSeenAt", now)
        d["lastSeenAt"] = now

    snapshot = {
        "scannedAt": now,
        "regions": list(REGIONS),
        "videos": sorted(seen.values(), key=lambda v: -v["viewCount"]),
    }
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1),
                             encoding="utf-8")
    return snapshot


if __name__ == "__main__":
    try:
        snap = scan()
        print(f"radar: {len(snap['videos'])} فيديو في المسح — "
              f"{SNAPSHOT_PATH.relative_to(settings.ROOT)}")
    except RuntimeError as exc:
        print(f"radar: {exc}", file=sys.stderr)
        sys.exit(2)
