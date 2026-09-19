"""فحص صحة حي للاعتمادات المطلوبة، بلا طباعة قيم الأسرار."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

from . import eye

REQUIRED = ("GROQ_API_KEY", "GEMINI_API_KEY", "YOUTUBE_API_KEY",
            "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET",
            "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_COOKIES_B64")


def _ok_http(method: str, url: str, **kwargs) -> tuple[bool, str]:
    try:
        r = requests.request(method, url, timeout=25, **kwargs)
        return r.ok, f"HTTP {r.status_code}"
    except Exception as exc:
        return False, type(exc).__name__


def _probe_pexels() -> tuple[bool, str]:
    key = os.getenv("PEXELS_API_KEY") or os.getenv("PEXELS") or ""
    if not key:
        return False, "missing secret (PEXELS_API_KEY / PEXELS)"
    return _ok_http("GET", "https://api.pexels.com/videos/search",
                    params={"query": "nature", "per_page": 1},
                    headers={"Authorization": key})


def _probe_pixabay() -> tuple[bool, str]:
    key = os.getenv("PIXABAY_API_KEY") or ""
    if not key:
        return False, "missing secret (PIXABAY_API_KEY)"
    return _ok_http("GET", "https://pixabay.com/api/videos/",
                    params={"key": key, "q": "nature", "per_page": 3})


def _probe_nasa() -> tuple[bool, str]:
    key = os.getenv("NASA_API_KEY") or os.getenv("NASA") or "DEMO_KEY"
    return _ok_http("GET", "https://api.nasa.gov/planetary/apod",
                    params={"api_key": key})


def _probe_commons() -> tuple[bool, str]:
    return _ok_http("GET", "https://commons.wikimedia.org/w/api.php",
                    params={"action": "query", "generator": "search",
                            "gsrsearch": "filetype:video nature", "gsrlimit": 1,
                            "format": "json"})


def _probe_archive() -> tuple[bool, str]:
    return _ok_http("GET", "https://archive.org/advancedsearch.php",
                    params={"q": "nature", "fl[]": "identifier", "rows": 1,
                            "output": "json"})


def _probe_openverse() -> tuple[bool, str]:
    key = os.getenv("OPENVERSE_API_KEY") or os.getenv("OPENVERSE") or ""
    params = {"q": "nature", "page_size": 1}
    if key:
        params["client_id"] = key
    ok, detail = _ok_http("GET", "https://api.openverse.org/v1/images/",
                          params=params)
    return ok, detail + ("" if key else " (بلا مفتاح — حدود منخفضة)")


def _probe_unsplash() -> tuple[bool, str]:
    key = os.getenv("UNSPLASH_ACCESS_KEY") or ""
    if not key:
        return False, "missing secret (UNSPLASH_ACCESS_KEY) — اختياري"
    return _ok_http("GET", "https://api.unsplash.com/photos",
                    params={"per_page": 1},
                    headers={"Authorization": f"Client-ID {key}"})


def _probe_freesound() -> tuple[bool, str]:
    key = os.getenv("FREESOUND_API_KEY") or ""
    if not key:
        return False, "missing secret (FREESOUND_API_KEY) — مؤثرات الصوت"
    return _ok_http("GET", "https://freesound.org/apiv2/search/text/",
                    params={"query": "whoosh", "fields": "id", "page_size": 1,
                            "token": key})


def _probe_currents() -> tuple[bool, str]:
    key = os.getenv("CURRENTS_API_KEY") or ""
    if not key:
        return False, "missing secret (CURRENTS_API_KEY) — اختياري"
    return _ok_http("GET", "https://api.currentsapi.services/v1/latest-news",
                    params={"apiKey": key, "language": "ar"})


def _probe_gnews() -> tuple[bool, str]:
    key = os.getenv("GNEWS_API_KEY") or ""
    if not key:
        return False, "missing secret (GNEWS_API_KEY) — اختياري"
    return _ok_http("GET", "https://gnews.io/api/v4/top-headlines",
                    params={"token": key, "lang": "ar", "max": 1})


def _probe_quran_text() -> tuple[bool, str]:
    return _ok_http("GET", "https://api.alquran.cloud/v1/surah/108")


def _probe_quran_audio() -> tuple[bool, str]:
    return _ok_http("GET",
                    "https://cdn.islamic.network/quran/audio/128/ar.husary/1.mp3",
                    stream=True)


def _probe_edge_tts() -> tuple[bool, str]:
    try:
        import asyncio

        import edge_tts
        voices = asyncio.run(edge_tts.list_voices())
        ar = [v for v in voices if str(v.get("Locale", "")).startswith("ar")]
        return bool(ar), f"{len(ar)} صوت عربي متاح"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:80]}"


# (الاسم، دالة الفحص، إلزامي؟) — الاختياري بيتسجل بصراحة ومش بيفشّل السير،
# لأن النقص في مزوّد واحد معناه «بديل»، مش توقف المصنع.
MEDIA_SOURCES: tuple[tuple[str, object, bool], ...] = (
    ("PEXELS_API_KEY", _probe_pexels, True),
    ("PIXABAY_API_KEY", _probe_pixabay, False),
    ("NASA_API_KEY", _probe_nasa, False),
    ("WIKIMEDIA_COMMONS", _probe_commons, False),
    ("INTERNET_ARCHIVE", _probe_archive, False),
    ("OPENVERSE", _probe_openverse, False),
    ("UNSPLASH_ACCESS_KEY", _probe_unsplash, False),
    ("FREESOUND_API_KEY", _probe_freesound, False),
    ("CURRENTS_API_KEY", _probe_currents, False),
    ("GNEWS_API_KEY", _probe_gnews, False),
    ("QURAN_TEXT_API", _probe_quran_text, False),
    ("QURAN_AUDIO_CDN", _probe_quran_audio, False),
    ("EDGE_TTS", _probe_edge_tts, False),
)


def run_media_sources() -> dict[str, dict]:
    """فحص حي لكل مزوّد ميديا/صوت/نص — «المفتاح موجود» مش دليل."""
    out: dict[str, dict] = {}
    for name, fn, required in MEDIA_SOURCES:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {str(exc)[:80]}"
        out[name] = {"ok": bool(ok), "detail": detail, "required": required}
    return out


def run() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for name in REQUIRED:
        result[name] = {"ok": bool(os.getenv(name, "").strip()), "detail": "present"}
        if not result[name]["ok"]:
            result[name]["detail"] = "missing"

    if result["GROQ_API_KEY"]["ok"]:
        ok, detail = _ok_http("GET", "https://api.groq.com/openai/v1/models",
                              headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"})
        result["GROQ_API_KEY"] = {"ok": ok, "detail": detail}
    if result["GEMINI_API_KEY"]["ok"]:
        ok, detail = _ok_http("GET", "https://generativelanguage.googleapis.com/v1beta/models",
                              params={"key": os.environ["GEMINI_API_KEY"]})
        result["GEMINI_API_KEY"] = {"ok": ok, "detail": detail}
    if result["YOUTUBE_API_KEY"]["ok"]:
        ok, detail = _ok_http("GET", "https://www.googleapis.com/youtube/v3/videos",
                              params={"part": "id", "chart": "mostPopular", "maxResults": 1,
                                      "key": os.environ["YOUTUBE_API_KEY"]})
        result["YOUTUBE_API_KEY"] = {"ok": ok, "detail": detail}

    oauth_names = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    if all(result[n]["ok"] for n in oauth_names):
        ok, detail = _ok_http("POST", "https://oauth2.googleapis.com/token", data={
            "client_id": os.environ["YOUTUBE_CLIENT_ID"],
            "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
            "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
            "grant_type": "refresh_token"})
        for n in oauth_names:
            result[n] = {"ok": ok, "detail": detail}

    if result["YOUTUBE_COOKIES_B64"]["ok"]:
        result["YOUTUBE_COOKIES_B64"] = _cookie_probe()

    # فحص حي لكل مزوّد لوحده: «المفتاح موجود» مش دليل — لازم الرد ييجي فعلًا
    for name, provider in (("GROQ_API_KEY", "groq"), ("GEMINI_API_KEY", "gemini")):
        if result[name]["ok"]:
            ok, detail = eye.llm_probe(provider)
            result[name] = {"ok": ok, "detail": detail}
    return result


def _cookie_probe() -> dict:
    """يفحص سر الكوكيز **بنفس مُحمِّل العين** (اللي بيحوّل أي شكل لنيتسكيب).

    الدرس: الفحص القديم كان بيكتب الـ base64 زي ما هو ويسأل yt-dlp، فيرجع
    «does not look like a Netscape format» من غير ما يقول السبب الحقيقي
    (السطر الواحد بصيغة أزواج). دلوقتي بنفك، بنحوّل، وبنوصف الشكل.
    """
    path: Path | None = None
    try:
        _, path = eye._load_cookies()
        if path is None:
            return {"ok": False,
                    "detail": "السر مش قابل للقراءة ككوكيز (نيتسكيب/JSON/أزواج)"}
        mode_ok = (path.stat().st_mode & 0o777) == 0o600
        cmd = [sys.executable, "-m", "yt_dlp", "--cookies", str(path),
               "--skip-download", "--playlist-items", "1", "--print", "id",
               "https://www.youtube.com/watch?v=OP3a2qzW5Yk"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if p.returncode == 0:
            return {"ok": mode_ok,
                    "detail": "yt-dlp authenticated probe (مصادقة شغالة)"
                              + ("" if mode_ok else " — صلاحيات الملف مش 0600")}
        err = (p.stderr or "").strip().splitlines()
        hint = next((l for l in err if "ERROR" in l), err[-1] if err else "?")
        return {"ok": False, "detail": "yt-dlp: " + hint[:120]}
    except Exception as exc:
        return {"ok": False, "detail": f"{type(exc).__name__}: {str(exc)[:100]}"}
    finally:
        if path:
            path.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = run()
    report.update(run_media_sources())
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "\n".join(
        f"{'✅' if v['ok'] else '❌'} {k}: {v['detail']}" for k, v in report.items()))
    hard_fail = [k for k, v in report.items()
                 if not v["ok"] and v.get("required", True)]
    if hard_fail:
        print("❌ إلزامي وقع: " + ", ".join(hard_fail), file=sys.stderr)
    return 1 if hard_fail else 0

if __name__ == "__main__":
    raise SystemExit(main())
