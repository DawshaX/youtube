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
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "\n".join(
        f"{'✅' if v['ok'] else '❌'} {k}: {v['detail']}" for k, v in report.items()))
    return 0 if all(v["ok"] for v in report.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
