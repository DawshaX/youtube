"""فحص الراحة قبل ما الفيديو يتساب. الرفض مكتوب، مش متشال بهدوء."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path: Path) -> dict:
    r = _run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_streams", "-show_format", str(path),
    ])
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "ffprobe فشل")
    return json.loads(r.stdout)


def loudness(path: Path) -> float | None:
    r = _run([
        "ffmpeg", "-hide_banner", "-i", str(path),
        "-af", "ebur128=framelog=verbose", "-f", "null", "-",
    ])
    text = (r.stderr or "") + (r.stdout or "")
    found = None
    for line in text.splitlines():
        if "I:" in line and "LUFS" in line:
            found = line
    if not found:
        return None
    try:
        return float(found.split("I:")[1].split("LUFS")[0].strip())
    except ValueError:
        return None


def check(video: Path, timeline: dict) -> dict:
    info = probe(video)
    streams = info.get("streams") or []
    video_s = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_s = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(info.get("format", {}).get("duration") or 0)
    width = int(video_s.get("width") or 0)
    height = int(video_s.get("height") or 0)
    kind = timeline.get("kind") or "short"
    checks = {
        "vertical": width == 1080 and height == 1920,
        "has_audio": audio_s is not None,
        "no_faces": timeline.get("faces") is False,
        "no_music": timeline.get("music") is None,
        "card_or_licensed": all(s.get("visual") in ("card", "vault") for s in timeline.get("shots") or []),
        "zoom_calm": all(float(s.get("zoom") or 1) <= 0.08 for s in timeline.get("shots") or []),
        "not_publishing": timeline.get("publish") is False,
    }
    if kind == "short":
        checks["duration"] = 8 <= duration <= 180
    else:
        checks["duration"] = duration > 8
    loud = loudness(video)
    checks["loudness"] = loud is not None and -16.5 <= loud <= -12.5
    failed = [name for name, ok in checks.items() if not ok]
    return {
        "ok": not failed,
        "failed": failed,
        "duration": round(duration, 2),
        "size": f"{width}x{height}",
        "loudness_lufs": loud,
        "checks": checks,
    }
