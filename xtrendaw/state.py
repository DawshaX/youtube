"""الذاكرة الخفيفة — إيه اللي اتنتج، وبصمات ضد التكرار.

مش قاعدة بيانات؛ ملف JSON صغير في state/ (مهمل من git إلا .gitkeep).
الهدف الوحيد دلوقتي: ما ننتجش نفس الحلقة مرتين، ونعرف نختار "التالي".
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import content, settings

STATE_FILE = settings.STATE / "produced.json"


def _read() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"episodes": {}, "fingerprints": []}


def _write(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def is_produced(topic_id: str) -> bool:
    return topic_id in _read()["episodes"]


def fingerprint_seen(topic: dict) -> bool:
    fp = content.fingerprint(topic)
    return fp in _read()["fingerprints"]


def seen_fingerprints() -> set:
    return set(_read()["fingerprints"])


def mark_produced(topic: dict, video: str, duration: float, urls: dict | None = None) -> None:
    data = _read()
    fp = content.fingerprint(topic)
    data["episodes"][topic["id"]] = {
        "title": topic.get("title_ar") or topic.get("angle", ""),
        "fingerprint": fp,
        "video": video,
        "duration": round(duration, 2),
        "at": time.strftime("%Y-%m-%d %H:%M"),
        "urls": urls or {},
    }
    if fp not in data["fingerprints"]:
        data["fingerprints"].append(fp)
    _write(data)


def produced_ids() -> list[str]:
    return list(_read()["episodes"].keys())


def last_kind() -> str:
    """نوع آخر حلقة اتنشرت ("trend"/"know"/"request") — عشان التناوب."""
    return _read().get("last_kind", "know")


def set_last_kind(kind: str) -> None:
    data = _read()
    data["last_kind"] = kind
    _write(data)


def next_topic(topics: list[dict]) -> dict | None:
    """أول موضوع لسه ما اتنتجش ومش مكرر بالبصمة."""
    seen_fps = set(_read()["fingerprints"])
    for t in topics:
        if is_produced(t["id"]):
            continue
        if content.fingerprint(t) in seen_fps:
            continue
        return t
    return None


def yt_pending() -> list:
    return _read().get("yt_pending", [])


def push_yt_pending(item: dict) -> None:
    data = _read()
    data.setdefault("yt_pending", []).append(item)
    _write(data)


def pop_yt_pending() -> None:
    data = _read()
    if data.get("yt_pending"):
        data["yt_pending"].pop(0)
        _write(data)


BADLIST_FILE = settings.STATE / "reciter_badlist.json"
YT_RECENT_FILE = settings.STATE / "yt_recent.json"


def _rw(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _wr(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                    encoding="utf-8")


MEDIA_FILE = settings.STATE / "media_used.json"


def media_used() -> dict:
    """كل أصل بصري/صوتي اتستخدم، بأي حلقة — ضد تكرار الوسائط بين الفيديوهات.

    الدرس (2026-09-19): نفس الصور طلعت في 4 فيديوهات مختلفة لأن مفيش ذاكرة
    وسائط بين الحلقات. الملف ده محفوظ على git، فالدورة الجديدة بتفتكر.
    """
    d = _rw(MEDIA_FILE, {})
    return d if isinstance(d, dict) else {}


def media_seen(key: str) -> bool:
    return bool(key) and key in media_used()


def mark_media_used(key: str, source: str = "", episode: str = "") -> None:
    if not key:
        return
    d = media_used()
    d[key] = {"source": source, "episode": episode,
              "at": time.strftime("%Y-%m-%d %H:%M")}
    if len(d) > 5000:   # احتفظ بالأحدث — الملف يفضل خفيف للأبد
        d = dict(sorted(d.items(),
                        key=lambda kv: str(kv[1].get("at", "")))[-5000:])
    _wr(MEDIA_FILE, d)


def media_summary_for(episode: str) -> dict:
    """ملخص ميديا حلقة: {فيديو: N, صور: M, مخزون: K} — دليل قابل للتدقيق.

    الدرس (شكوى المستخدم 2026-09-19): الفيديو كان بيطلع بصور مركبة/مخزون
    قديم من غير ما حد ياخد باله. السطر ده بيفضح الحقيقة في لوج كل دورة.
    """
    video = images = static = other = 0
    for key, rec in media_used().items():
        if str((rec or {}).get("episode")) != str(episode):
            continue
        src = str((rec or {}).get("source") or "")
        if src.startswith("video:"):
            video += 1
        elif src.startswith("image:"):
            images += 1
        elif src.startswith("vault:") or src == "internal":
            static += 1
        else:
            other += 1
    return {"video": video, "images": images, "static": static,
            "other": other, "total": video + images + static + other}


def media_used_by_source(source: str) -> int:
    return sum(1 for v in media_used().values()
               if (v or {}).get("source") == source)


PUBLISHED_FILE = settings.STATE / "published.json"


def published_log() -> list:
    """سجل كل نشر ناجح — أساس حارس الكوتة اليومي."""
    d = _rw(PUBLISHED_FILE, [])
    return d if isinstance(d, list) else []


def push_published(item: dict) -> None:
    d = published_log()
    d.append(item)
    _wr(PUBLISHED_FILE, d[-500:])


def published_last_24h(now: float | None = None) -> int:
    """كام حلقة اتنشرت في آخر 24 ساعة (يوتيوب: 6 رفعات = 10,000 وحدة)."""
    now = now or time.time()
    n = 0
    for x in published_log():
        if not isinstance(x, dict):
            continue
        try:
            if now - float(x.get("ts") or 0) < 86400:
                n += 1
        except (TypeError, ValueError):
            continue
    return n


def reciter_badlist() -> list:
    return _rw(BADLIST_FILE, [])


def add_reciter_badlist(rid: str) -> None:
    bl = reciter_badlist()
    if rid and rid not in bl:
        bl.append(rid)
        _wr(BADLIST_FILE, bl)


def yt_recent() -> list:
    return _rw(YT_RECENT_FILE, [])


def push_yt_recent(item: dict) -> None:
    lst = [x for x in yt_recent() if x.get("id") != item.get("id")]
    lst.append(item)
    _wr(YT_RECENT_FILE, lst[-30:])


def pop_yt_recent(vid: str) -> None:
    _wr(YT_RECENT_FILE, [x for x in yt_recent() if x.get("id") != vid])


PROVEN_FILE = settings.STATE / "reciter_proven.json"


def reciter_proven() -> list:
    return _rw(PROVEN_FILE, [])


def add_reciter_proven(rid: str) -> None:
    lst = reciter_proven()
    if rid and rid not in lst:
        lst.append(rid)
        _wr(PROVEN_FILE, lst)


IG_TOKEN_FILE = settings.STATE / "ig_token.json"


def set_ig_token(tok: str) -> None:
    import time as _t
    _wr(IG_TOKEN_FILE, {"token": tok, "ts": _t.time()})
    settings.INSTAGRAM["token"] = tok


TIKTOK_TOKEN_FILE = settings.STATE / "tiktok_token.json"


def _cipher():
    if not settings.TOKEN_KEY:
        return None
    try:
        import base64 as _b
        import nacl.bindings as _nb
        return _b.b64decode(settings.TOKEN_KEY)
    except Exception:
        return None


def set_tiktok_tokens(access_token: str, refresh_token: str) -> None:
    import time as _t
    payload = {"access_token": access_token, "refresh_token": refresh_token,
               "ts": _t.time()}
    key = _cipher()
    if key:
        import base64 as _b
        import nacl.secret as _ns
        box = _ns.SecretBox(key)
        payload = {"enc": _b.b64encode(box.encrypt(
            __import__("json").dumps(payload).encode())).decode()}
    _wr(TIKTOK_TOKEN_FILE, payload)
    settings.TIKTOK["access_token"] = access_token
    settings.TIKTOK["refresh_token"] = refresh_token
