"""رندر حلقة مكتملة: لقطة حية لكل جملة، شخصية أصلية، وأسلوب لقطات من المصنع."""
from __future__ import annotations

import subprocess
from pathlib import Path

from xtrendaw import footage, textrender
from xtrendaw.noor_look import pick as pick_look

from .formats import motion_for, pick_format
from .montage import loudnorm, overlay_frame, pick_feeling, pick_transition, write_timeline
from .palettes import palette_for
from .queries import queries_for
from .souls import pick_soul, portrait
from .studio import burn_words, circle, halo, layer, licensed_whoosh, mark, mix_bed, say
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


def _voice(episode: dict, pal: dict, soul: dict | None) -> tuple[str, str, str]:
    if pal.get("sacred") or soul is None and pal.get("id") == "faith":
        return "ar-SA-HamedNeural", "-12%", "-4Hz"
    if soul:
        return soul["voice"], soul.get("rate") or "-6%", soul.get("pitch") or "-2Hz"
    voices = ("ar-EG-SalmaNeural", "ar-EG-ShakirNeural")
    seed = str(episode.get("id") or "")
    return voices[sum(ord(c) for c in seed) % 2], pal.get("rate") or "-6%", pal.get("pitch") or "-2Hz"


def _crop(motion: str, seconds: float) -> tuple[str, str]:
    dur = max(seconds, 0.1)
    if motion == "left":
        return f"(in_w-out_w)*(1-t/{dur:.2f})", "(in_h-out_h)*0.35"
    if motion == "right":
        return f"(in_w-out_w)*t/{dur:.2f}", "(in_h-out_h)*0.35"
    if motion == "hold":
        return "(in_w-out_w)*0.5", "(in_h-out_h)*0.35"
    if motion == "rise":
        return "(in_w-out_w)*0.5", f"(in_h-out_h)*(0.55-0.18*t/{dur:.2f})"
    return f"(in_w-out_w)*t/{dur:.2f}", "(in_h-out_h)*0.35"


def _style_clip(src: Path, dst: Path, seconds: float, grade: str, motion: str) -> None:
    fade = 0.27
    out_st = max(0.2, seconds - fade)
    x, y = _crop(motion, seconds)
    base = (
        f"scale={int(W * 1.08)}:{int(H * 1.08)}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:x='{x}':y='{y}'"
    )
    tail = f"fade=t=in:st=0:d={fade},fade=t=out:st={out_st:.2f}:d={fade},fps=30,format=yuv420p"
    fancy = f"{base},{grade},{tail}" if grade else f"{base},{tail}"
    plain = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,format=yuv420p"

    def encode(vf: str) -> None:
        _run([
            "ffmpeg", "-y", "-i", str(src), "-t", f"{seconds:.2f}", "-vf", vf,
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", str(dst),
        ])

    try:
        encode(fancy)
    except RuntimeError as exc:
        print(f"[studio] التدريج اتخطى: {str(exc)[-180:]}", flush=True)
        encode(plain)


def _caption(text: str, path: Path, y: float, fill: str, size: int) -> None:
    textrender.text_image(
        text, path, canvas=(W, H), font_size=size, fill=fill,
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
    feeling, feel = pick_feeling(episode)
    soul = None if pal.get("sacred") else pick_soul(episode, feeling)
    fmt_name, fmt = pick_format(episode, feeling, neon=bool(soul and soul.get("neon")))
    transition = pick_transition(str(episode.get("id") or ""))
    voice, rate, pitch = _voice(episode, pal, soul)
    work.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    wavs: list[Path] = []
    caps: list[Path] = []
    credits: list[str] = []
    durs: list[float] = []
    words: list[dict] = []
    scene = str(episode.get("scene") or "")
    cursor = 0.0
    for i, line in enumerate(lines):
        raw = work / f"say-{i}.mp3"
        wav = work / f"say-{i}.wav"
        spoken_words = say(line, raw, voice, rate, pitch)
        _run([
            "ffmpeg", "-y", "-i", str(raw),
            "-af", "apad=pad_dur=0.06",
            "-ar", "48000", "-ac", "2", str(wav),
        ])
        dur = _dur(wav)
        if dur < 0.45:
            return None
        origin = spoken_words[0]["t"] if spoken_words else 0.0
        for word in spoken_words:
            words.append({
                "t": cursor + max(0.0, word["t"] - origin),
                "d": word["d"],
                "w": word["w"],
            })
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
        grades = [feel["grade"], look.get("grade") or "eq=saturation=1.02"]
        if fmt.get("neon"):
            grades.append("eq=saturation=1.12")
        if soul and soul.get("style") in ("queen", "soul"):
            grades.append("eq=gamma=1.05:saturation=1.04")
        grade = ",".join(part.strip(",") for part in grades if part)
        _style_clip(got, styled, dur, grade, motion_for(fmt, i))
        png = work / f"cap-{i}.png"
        _caption(line, png, float(look.get("y") or 0.56), pal.get("text") or "#F7F1E6", int(feel["size"]))
        clips.append(styled)
        wavs.append(wav)
        caps.append(png)
        durs.append(dur)
        cursor += dur
    lst = work / "v.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
    silent = work / "silent.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
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
    try:
        over = burn_words(over, words, work, pal.get("text") or "#F7F1E6", _run)
    except Exception as exc:
        print(f"[studio] تلوين الكلمة اتخطى: {type(exc).__name__}", flush=True)
    face = portrait(soul)
    if face:
        avatar = work / "avatar.png"
        if circle(face, avatar):
            soft = bool(soul)
            floated = "'1510+5*sin(t)'" if soft else "1510"
            if soul and soul.get("style") in ("queen", "soul"):
                ring = work / "halo.png"
                halo(ring, soul.get("mark") or "#F6E7C8")
                over = layer(over, work / "halo.mp4", ring, "16", "'1480+5*sin(t)'" if soft else "1480", _run)
            over = layer(over, work / "avatar.mp4", avatar, "46", floated, _run)
    badge = work / "mark.png"
    mark(badge, (soul or {}).get("mark") or "#E2B07A")
    over = layer(over, work / "marked.mp4", badge, "960", "72", _run)
    framed = work / "framed.mp4"
    overlay_frame(over, framed, _run)
    alst = work / "a.txt"
    alst.write_text("".join(f"file '{p}'\n" for p in wavs), encoding="utf-8")
    mixed = work / "mixed.wav"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst), "-c:a", "pcm_s16le", str(mixed)])
    music_credit = None
    voiced = mixed
    if not pal.get("sacred"):
        try:
            bedded = work / "bedded.wav"
            music_credit = mix_bed(mixed, bedded, cursor, _run)
            if music_credit and bedded.exists():
                voiced = bedded
                credits.append(music_credit)
        except Exception as exc:
            print(f"[studio] الموسيقى اتخطت: {type(exc).__name__}", flush=True)
        if feeling in ("هزار", "لحظة") and not (soul and soul.get("child")):
            whoosh, sfx_credit = licensed_whoosh(work)
            if whoosh and sfx_credit:
                try:
                    hit = work / "hit.wav"
                    _run([
                        "ffmpeg", "-y", "-i", str(voiced), "-i", str(whoosh),
                        "-filter_complex",
                        "[1]volume=0.04,afade=t=out:st=0.35:d=0.25[s];"
                        "[0][s]amix=inputs=2:duration=first:normalize=0[a]",
                        "-map", "[a]", "-ar", "48000", "-ac", "2", str(hit),
                    ])
                    if hit.exists():
                        voiced = hit
                        credits.append(sfx_credit)
                except Exception as exc:
                    print(f"[studio] المؤثر اتخطى: {type(exc).__name__}", flush=True)
    normal = work / "normal.wav"
    loudnorm(voiced, normal, _run)
    out = work / "episode.mp4"
    _run([
        "ffmpeg", "-y", "-i", str(framed), "-i", str(normal),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ])
    shots = [
        {"i": i, "say": line, "dur": durs[i], "visual": "footage", "motion": motion_for(fmt, i)}
        for i, line in enumerate(lines)
    ]
    write_timeline(work / "timeline.json", episode, shots, feeling, transition, {
        "format": fmt_name,
        "rights": fmt["rights"],
        "copied_video": False,
        "soul": None if not soul else soul["name"],
        "soul_style": None if not soul else soul["style"],
        "faces": bool(face),
        "face_kind": "شخصية أصلية" if face else "من غير وجه",
        "music": music_credit,
        "tools": [
            "خط زمني", "لقطة لكل جملة", "أسلوب لقطات أصلي", "كابشن عربي",
            "كلمة بتتلون", "انتقال هادي", "إطار", "صوت مضبوط",
            "شخصية كرتون أو طين أو نيون", "موسيقى مولّدة", "ترخيص مع اللقطة",
        ],
    })
    return {
        "video": out,
        "duration": _dur(out),
        "look": look.get("name") or look.get("id"),
        "feeling": feeling,
        "transition": transition,
        "format": fmt_name,
        "soul": None if not soul else soul["name"],
        "voice": voice,
        "credits": list(dict.fromkeys(credits)),
        "lines": lines,
    }
