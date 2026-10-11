"""أدوات المونتاج اللي المصنع بيستخدمها. إضافة على اللي موجود، مش برنامج مسروق."""
from __future__ import annotations

import json
from pathlib import Path

# انتقالات هادية من ffmpeg. الوميض والبكسلة مش هنا.
TRANSITIONS = ("fade", "fadeblack", "smoothleft", "smoothright", "dissolve")

FEELINGS = {
    "هزار": {"caption": "كلمة", "mark": True, "grade": "eq=saturation=1.08:gamma=1.04", "size": 66},
    "علم": {"caption": "سطر", "mark": False, "grade": "eq=saturation=0.96:contrast=1.04", "size": 62},
    "جد": {"caption": "سطر", "mark": False, "grade": "eq=saturation=0.92:gamma=1.02", "size": 64},
    "وعي": {"caption": "واضح", "mark": False, "grade": "eq=contrast=1.05:saturation=1.0", "size": 64},
    "حزن": {"caption": "أهدى", "mark": False, "grade": "eq=saturation=0.82:brightness=-0.02", "size": 62},
    "طفل": {"caption": "كبير", "mark": True, "grade": "eq=saturation=1.06:gamma=1.06", "size": 76},
    "لحظة": {"caption": "كلمة", "mark": False, "grade": "eq=contrast=1.08:saturation=1.04", "size": 66},
    "حب": {"caption": "دافي", "mark": False, "grade": "colorbalance=rs=0.06:gs=0.02,eq=gamma=1.04", "size": 64},
    "حياة": {"caption": "واضح", "mark": False, "grade": "eq=saturation=1.02:contrast=1.03", "size": 64},
}

FRAME = Path(__file__).resolve().parents[2] / "assets" / "ornaments" / "frame.png"


def pick_feeling(episode: dict) -> tuple[str, dict]:
    blob = " ".join(str(episode.get(k) or "") for k in ("emotion", "field", "series_title"))
    for name in FEELINGS:
        if name in blob:
            return name, FEELINGS[name]
    names = list(FEELINGS)
    n = sum(ord(c) for c in str(episode.get("id") or "نور"))
    name = names[n % len(names)]
    return name, FEELINGS[name]


def pick_transition(episode_id: str) -> str:
    n = sum(ord(c) for c in str(episode_id or "نور"))
    return TRANSITIONS[n % len(TRANSITIONS)]


def write_timeline(path: Path, episode: dict, shots: list[dict], feeling: str, transition: str) -> None:
    path.write_text(json.dumps({
        "id": episode.get("id"),
        "series": episode.get("series_title"),
        "feeling": feeling,
        "transition": transition,
        "faces": False,
        "music": None,
        "shots": shots,
        "tools": [
            "خط زمني", "لقطة لكل جملة", "تدريج", "كابشن عربي",
            "انتقال هادي", "إطار", "صوت مضبوط", "ترخيص مع اللقطة",
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def loudnorm(src: Path, dst: Path, run) -> None:
    probe = __import__("subprocess").run(
        ["ffmpeg", "-hide_banner", "-i", str(src),
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    raw = probe.stderr or ""
    start, end = raw.rfind("{"), raw.rfind("}")
    if start < 0 or end < start:
        run(["ffmpeg", "-y", "-i", str(src), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
             "-ar", "48000", "-ac", "2", str(dst)])
        return
    measured = json.loads(raw[start:end + 1])
    af = (
        "loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}"
    )
    run(["ffmpeg", "-y", "-i", str(src), "-af", af, "-ar", "48000", "-ac", "2", str(dst)])


def overlay_frame(video: Path, dst: Path, run) -> None:
    if not FRAME.exists():
        dst.write_bytes(video.read_bytes())
        return
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(FRAME),
        "-filter_complex",
        "[1]scale=1080:1920,format=rgba,colorkey=0x000000:0.12:0.08[fr];"
        "[0][fr]overlay=0:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(dst),
    ])
