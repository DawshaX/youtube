"""رندر حلقة مكتملة: لقطة حية لكل جملة، مونتاج هادي، صوت، كابشن. من غير كارت لو اللقطة وقعت."""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from xtrendaw import footage, textrender
from xtrendaw.noor_look import pick as pick_look

from .palettes import palette_for
from .queries import queries_for
from .timeline import sentences, sacred_text

W, H, FPS = 1080, 1920, 30


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "ffmpeg فشل")[-800:])


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


def _voice(episode: dict, pal: dict) -> tuple[str, str, str]:
    if pal.get("id") == "faith":
        return "ar-SA-HamedNeural", "-12%", "-4Hz"
    voices = ("ar-EG-SalmaNeural", "ar-EG-ShakirNeural")
    seed = str(episode.get("id") or "")
    return voices[sum(ord(c) for c in seed) % 2], pal.get("rate") or "-6%", pal.get("pitch") or "-2Hz"


def _style_clip(src: Path, dst: Path, seconds: float, grade: str) -> None:
    fade = 0.27
    out_st = max(0.2, seconds - fade)
    vf = (
        f"scale={int(W * 1.08)}:{int(H * 1.08)}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:x='(in_w-out_w)*t/{max(seconds, 0.1):.2f}':y='(in_h-out_h)*0.35',"
        f"{grade},fade=t=in:st=0:d={fade},fade=t=out:st={out_st:.2f}:d={fade},"
        "fps=30,format=yuv420p"
    )
    _run([
        "ffmpeg", "-y", "-i", str(src), "-t", f"{seconds:.2f}", "-vf", vf,
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(dst),
    ])


def _caption(text: str, path: Path, y: float) -> None:
    textrender.text_image(
        text, path, canvas=(W, H), font_size=64, fill="#F7F1E6",
        stroke="#14110E", stroke_width=5, y_ratio=y, max_width_ratio=0.72,
    )


def render(episode: dict, work: Path) -> dict | None:
    spoken = (episode.get("spoken") or "").strip()
    if not spoken or sacred_text(spoken):
        return None
    lines = sentences(spoken)
    if len(lines) < 2:
        return None
    pal = palette_for(episode)
    look = pick_look({"id": episode.get("id"), "hook": lines[0], "kind": pal["id"]})
    voice, rate, pitch = _voice(episode, pal)
    work.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    wavs: list[Path] = []
    caps: list[Path] = []
    credits: list[str] = []
    durs: list[float] = []
    scene = str(episode.get("scene") or "")
    for i, line in enumerate(lines):
        raw = work / f"say-{i}.mp3"
        wav = work / f"say-{i}.wav"
        asyncio.run(_speak(line, raw, voice, rate, pitch))
        _run([
            "ffmpeg", "-y", "-i", str(raw),
            "-af", "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.02,"
                   "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.02,"
                   "areverse,apad=pad_dur=0.06",
            "-ar", "48000", "-ac", "2", str(wav),
        ])
        dur = _dur(wav)
        if dur < 0.45:
            return None
        got = None
        for q in queries_for(line, scene):
            got = footage.fetch_clip(q, dur + 0.3, work, f"{episode.get('id')}:{i}:{q}")
            if got:
                break
        if not got:
            print(f"[library] مفيش لقطة للجملة: {line[:40]}", flush=True)
            return None
        from xtrendaw import vault
        rec = vault.record_for(got) or {}
        if rec.get("credit_line"):
            credits.append(rec["credit_line"])
        elif rec.get("source"):
            credits.append(f"{rec.get('source')} · {rec.get('license') or ''}")
        styled = work / f"shot-{i}.mp4"
        _style_clip(got, styled, dur, "," + look.get("grade", "eq=saturation=1.02"))
        png = work / f"cap-{i}.png"
        _caption(line, png, float(look.get("y") or 0.56))
        clips.append(styled)
        wavs.append(wav)
        caps.append(png)
        durs.append(dur)
    lst = work / "v.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
    silent = work / "silent.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
    # الكابشن يتسجل على مدة كل جملة
    cmd = ["ffmpeg", "-y", "-i", str(silent)]
    for png in caps:
        cmd.extend(["-i", str(png)])
    chain = []
    prev = "0:v"
    t = 0.0
    for i, dur in enumerate(durs, 1):
        chain.append(f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{t:.3f},{t + dur:.3f})'[v{i}]")
        prev = f"v{i}"
        t += dur
    over = work / "over.mp4"
    cmd.extend([
        "-filter_complex", ";".join(chain), "-map", f"[{prev}]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(over),
    ])
    _run(cmd)
    alst = work / "a.txt"
    alst.write_text("".join(f"file '{p}'\n" for p in wavs), encoding="utf-8")
    mixed = work / "mixed.wav"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst), "-c:a", "pcm_s16le", str(mixed)])
    normal = work / "normal.wav"
    _run(["ffmpeg", "-y", "-i", str(mixed), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
          "-ar", "48000", "-ac", "2", str(normal)])
    out = work / "episode.mp4"
    _run([
        "ffmpeg", "-y", "-i", str(over), "-i", str(normal),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ])
    return {
        "video": out,
        "duration": _dur(out),
        "look": look.get("name") or look.get("id"),
        "voice": voice,
        "credits": list(dict.fromkeys(credits)),
        "lines": lines,
    }
