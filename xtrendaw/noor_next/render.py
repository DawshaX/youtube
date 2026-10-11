"""يطلّع فيديو حقيقي من خط الزمن. من غير رفع، ومن غير ما يلمس الحي."""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

from xtrendaw import textrender

from .gate import check
from .timeline import build
from .vault import load, match

W, H, FPS = 1080, 1920, 24
FONT = textrender.FONT_BOLD


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "ffmpeg فشل")[-1200:]
        raise RuntimeError(tail)


def _dur(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip() or 0)


async def _speak(text: str, path: Path, voice: str, rate: str, pitch: str) -> None:
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(path))


def _trim(src: Path, dst: Path) -> None:
    _run([
        "ffmpeg", "-y", "-i", str(src),
        "-af",
        "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.02,"
        "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.02,"
        "areverse,apad=pad_dur=0.08",
        "-ar", "48000", "-ac", "2", str(dst),
    ])


def _silence(dst: Path, seconds: float) -> None:
    _run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", f"{seconds:.3f}", "-c:a", "pcm_s16le", str(dst),
    ])


def _concat_audio(pieces: list[Path], dst: Path) -> None:
    lst = dst.with_suffix(".txt")
    lst.write_text("".join(f"file '{p}'\n" for p in pieces), encoding="utf-8")
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(dst),
    ])


def _loudnorm(src: Path, dst: Path) -> None:
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(src),
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    raw = probe.stderr or ""
    start, end = raw.rfind("{"), raw.rfind("}")
    if start < 0 or end < start:
        _run(["ffmpeg", "-y", "-i", str(src), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
              "-ar", "48000", "-ac", "2", str(dst)])
        return
    measured = json.loads(raw[start:end + 1])
    af = (
        "loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}"
    )
    _run(["ffmpeg", "-y", "-i", str(src), "-af", af, "-ar", "48000", "-ac", "2", str(dst)])


def _caption(text: str, path: Path, pal: dict) -> None:
    size = 68
    max_w = int(W * 0.72)
    while size > 50:
        font = textrender._font(size, bold=True)
        if len(textrender.wrap_ar(text, font, max_w)) <= 2:
            break
        size -= 6
    textrender.text_image(
        text, path, canvas=(W, H), font_size=size,
        fill=pal["text"], stroke=pal["stroke"], stroke_width=5,
        y_ratio=0.56, max_width_ratio=0.72, bold=True,
    )


def _background(dst: Path, seconds: float, pal: dict) -> None:
    frames = max(FPS, int(round(seconds * FPS)))
    wide, tall = int(W * 1.08), int(H * 1.08)
    vf = (
        f"gradients=s={wide}x{tall}:c0={pal['c0']}:c1={pal['c1']}:"
        f"x0=180:y0=120:x1={wide - 80}:y1={tall - 80}:speed=0.004:d={frames}:r={FPS},"
        f"crop={W}:{H}:x='(in_w-out_w)*(0.5+0.12*sin(t/8))':y='(in_h-out_h)*0.42',"
        f"drawbox=x=72:y=240:w=iw-144:h=3:color={pal['line']}@0.40:t=fill,"
        f"drawbox=x=72:y=ih-460:w=iw-144:h=3:color={pal['line']}@0.40:t=fill,"
        "vignette=PI/5,eq=brightness=0.02:saturation=0.92:contrast=1.03,format=yuv420p"
    )
    _run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", vf, "-t", f"{seconds:.3f}",
        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-an", str(dst),
    ])


def _overlay(bg: Path, caps: list[tuple[Path, float, float]], dst: Path, seconds: float) -> None:
    cmd = ["ffmpeg", "-y", "-i", str(bg)]
    for cap, _, _ in caps:
        cmd.extend(["-i", str(cap)])
    chain = []
    prev = "0:v"
    for i, (_, start, end) in enumerate(caps, 1):
        out = f"v{i}"
        chain.append(
            f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})'[{out}]"
        )
        prev = out
    cmd.extend([
        "-filter_complex", ";".join(chain), "-map", f"[{prev}]",
        "-t", f"{seconds:.3f}", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-an", str(dst),
    ])
    _run(cmd)


def render_episode(episode: dict, out_mp4: Path, work: Path, vault_path: Path | None = None) -> dict:
    timeline = build(episode)
    work.mkdir(parents=True, exist_ok=True)
    pal = timeline["palette"]
    index = load(vault_path) if vault_path else {"items": []}
    pieces: list[Path] = []
    caps: list[tuple[Path, float, float]] = []
    t = 0.0
    pause = float(pal.get("pause") or 0.32)
    gap = work / "gap.wav"
    _silence(gap, pause)
    for shot in timeline["shots"]:
        found = match(index, kind="video", palette=pal["id"], query=shot["query"])
        if found:
            shot["visual"] = "vault"
            shot["source"] = found.get("source")
            shot["license"] = found.get("license")
        raw = work / f"say-{shot['i']}.mp3"
        wav = work / f"say-{shot['i']}.wav"
        asyncio.run(_speak(shot["say"], raw, pal["voice"], pal["rate"], pal["pitch"]))
        _trim(raw, wav)
        dur = _dur(wav)
        if dur < 0.4:
            raise RuntimeError("الصوت رجع فاضي")
        shot["audio_s"] = round(dur, 3)
        shot["start"] = round(t, 3)
        shot["end"] = round(t + dur, 3)
        png = work / f"cap-{shot['i']}.png"
        _caption(shot["say"], png, pal)
        caps.append((png, t, t + dur))
        pieces.append(wav)
        t += dur
        if shot["i"] < len(timeline["shots"]) - 1:
            pieces.append(gap)
            t += pause
    tail = work / "tail.wav"
    _silence(tail, 0.12)
    pieces.append(tail)
    t += 0.12
    mixed = work / "mixed.wav"
    normal = work / "normal.wav"
    _concat_audio(pieces, mixed)
    _loudnorm(mixed, normal)
    total = _dur(normal)
    timeline["length_s"] = round(total, 3)
    bg = work / "bg.mp4"
    silent = work / "silent.mp4"
    _background(bg, total, pal)
    _overlay(bg, caps, silent, total)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-i", str(silent), "-i", str(normal),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-t", f"{total:.3f}", str(out_mp4),
    ])
    timeline_path = out_mp4.with_suffix(".timeline.json")
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    report = check(out_mp4, timeline)
    report_path = out_mp4.with_suffix(".gate.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"video": str(out_mp4), "timeline": str(timeline_path), "gate": report}
