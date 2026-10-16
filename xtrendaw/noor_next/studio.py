"""طبقات الاستوديو: كلمة بتتلون، شخصية، موسيقى مولّدة، علامة واحدة.

لو طبقة وقعت، الحلقة تكمل. التلاوة مش بتعدي من هنا.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from xtrendaw import textrender

W, H = 1080, 1920


def tts_pitch(pitch: str) -> str:
    """edge-tts يرفض «0Hz». لازم علامة + أو − حتى لو القيمة صفر."""
    match = re.fullmatch(r"([+-]?)(\d+)Hz", (pitch or "").strip())
    if not match:
        return "+0Hz"
    sign = match.group(1) if match.group(1) in ("+", "-") else "+"
    return f"{sign}{int(match.group(2))}Hz"


async def speak_words(text: str, path: Path, voice: str, rate: str, pitch: str) -> list[dict]:
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=tts_pitch(pitch))
    words: list[dict] = []
    with path.open("wb") as handle:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                handle.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "t": float(chunk["offset"]) / 10_000_000,
                    "d": float(chunk["duration"]) / 10_000_000,
                    "w": str(chunk.get("text") or "").strip(),
                })
    return [w for w in words if w["w"]]


def circle(src: Path, dst: Path, size: int = 280) -> bool:
    from PIL import Image, ImageDraw

    im = Image.open(src).convert("RGBA")
    side = min(im.size)
    left = (im.width - side) // 2
    top = (im.height - side) // 2
    inset = int(side * 0.06)
    im = im.crop((left + inset, top + inset, left + side - inset, top + side - inset))
    im = im.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((1, 1, size - 2, size - 2), fill=255)
    im.putalpha(mask)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return dst.exists()


def halo(path: Path, color: str = "#F6E7C8") -> None:
    from PIL import Image, ImageDraw

    size = 340
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.ellipse((10, 10, size - 11, size - 11), outline=color, width=8)
    draw.ellipse((24, 24, size - 25, size - 25), outline=(255, 247, 230, 110), width=4)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def mark(path: Path, color: str) -> None:
    from PIL import Image, ImageDraw

    size = 72
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.ellipse((8, 8, 64, 64), fill=color)
    draw.ellipse((24, 24, 48, 48), fill=(255, 247, 236, 230))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def burn_words(video: Path, words: list[dict], work: Path, fill: str, run) -> Path:
    shown = [w for w in words if w.get("w")][:20]
    if not shown:
        return video
    pngs = []
    for i, word in enumerate(shown):
        png = work / f"word-{i}.png"
        textrender.text_image(
            word["w"], png, canvas=(W, H), font_size=52, fill=fill,
            stroke="#14110E", stroke_width=4, y_ratio=0.78, max_width_ratio=0.46,
        )
        pngs.append(png)
    cmd = ["ffmpeg", "-y", "-i", str(video)]
    for png in pngs:
        cmd.extend(["-i", str(png)])
    chain = []
    prev = "0:v"
    for i, word in enumerate(shown, 1):
        t0 = max(0.0, float(word["t"]))
        t1 = t0 + max(0.12, float(word["d"]))
        chain.append(
            f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})'[w{i}]"
        )
        prev = f"w{i}"
    out = work / "words.mp4"
    cmd.extend([
        "-filter_complex", ";".join(chain), "-map", f"[{prev}]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(out),
    ])
    run(cmd)
    return out


def overlay_rgba(video: Path, png: Path, dst: Path, x: str, y: str, run) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(png),
        "-filter_complex", f"[1]format=rgba[a];[0][a]overlay={x}:{y}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(dst),
    ])


def mix_bed(voice: Path, dst: Path, seconds: float, run) -> str | None:
    from xtrendaw.music import make_music

    bed = voice.parent / "bed.wav"
    make_music(max(1.0, seconds + 0.3), bed, bpm=72, volume=0.16)
    run([
        "ffmpeg", "-y", "-i", str(voice), "-i", str(bed),
        "-filter_complex",
        "[1]volume=0.09,afade=t=in:st=0:d=0.6[b];"
        "[0][b]amix=inputs=2:duration=first:normalize=0:dropout_transition=0[a]",
        "-map", "[a]", "-ar", "48000", "-ac", "2", str(dst),
    ])
    return "موسيقى مولّدة للمصنع، حقوق المصنع."


def licensed_whoosh(work: Path) -> tuple[Path | None, str]:
    try:
        from xtrendaw import sfx
        got = sfx.pick("whoosh", work)
        credits = [c for c in sfx.session_credits() if c]
        return got, (credits[-1] if credits else "")
    except Exception:
        return None, ""


def layer(video: Path, dst: Path, png: Path, x: str, y: str, run) -> Path:
    try:
        overlay_rgba(video, png, dst, x, y, run)
        return dst if dst.exists() else video
    except Exception as exc:
        print(f"[studio] الطبقة اتخطت: {type(exc).__name__}", flush=True)
        return video


def say(text: str, path: Path, voice: str, rate: str, pitch: str) -> list[dict]:
    return asyncio.run(speak_words(text, path, voice, rate, pitch))


# ─────────────── 🧩 طبقات الزينة في **تمريرة واحدة** ───────────────
# ليه: الأفاتار + العلامة + الإطار كانوا **٣ تمريرات ffmpeg كاملة** على
# الفيديو كله (كل واحدة بترمز المدة كلها من الأول). على حلقة ١٠ دقايق ده
# يعني دقايق مهدورة من مهلة الدورة (٤٥ دقيقة) بلا أي فرق في النتيجة:
# الثلاثة مجرد `overlay` على نفس المدخل، وينفع يتعملوا في مرشّح واحد.
# القياس قبل التحسين: دورة الحلقة الطويلة بتفوت المهلة ٤٣ دقيقة وتفشل.
# الأمانة: لو أي حاجة وقعت، بيرجع `None` والمصنع يكمل بالطريقة القديمة.
def decorate(video: Path, dst: Path, *, avatar: Path | None = None,
             badge: Path | None = None, frame: Path | None = None,
             run=None) -> Path | None:
    """يطبّق الأفاتار + العلامة + الإطار في **نداء ffmpeg واحد**.

    يرجّع المسار الجديد عند النجاح، و`None` لو فشل (المصنع يرجّع للطريقة
    القديمة بثلاث تمريرات — مفيش كسر أبدًا).
    """
    try:
        if run is None:
            from .render import run as _r          # noqa: PLC0415
            run = _r
        inputs: list[str] = ["-i", str(video)]
        chain: list[str] = []
        label = "0:v"
        idx = 1
        if avatar is not None and Path(avatar).exists():
            inputs += ["-i", str(avatar)]
            chain.append(f"[{idx}]format=rgba[av{idx}]")
            chain.append(f"[{label}][av{idx}]overlay=46:'1510+5*sin(t)'[v{idx}]")
            label, idx = f"v{idx}", idx + 1
        if badge is not None and Path(badge).exists():
            inputs += ["-i", str(badge)]
            chain.append(f"[{idx}]format=rgba[bd{idx}]")
            chain.append(f"[{label}][bd{idx}]overlay=960:72[v{idx}]")
            label, idx = f"v{idx}", idx + 1
        if frame is not None and Path(frame).exists():
            inputs += ["-i", str(frame)]
            chain.append(f"[{idx}]scale=1080:1920,format=rgba,"
                         f"colorkey=0x000000:0.12:0.08[fr{idx}]")
            chain.append(f"[{label}][fr{idx}]overlay=0:0[v{idx}]")
            label, idx = f"v{idx}", idx + 1
        if idx == 1:                                # مفيش أي طبقة
            return None
        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(chain),
             "-map", f"[{label}]", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(dst)])
        return dst if dst.exists() and dst.stat().st_size > 2048 else None
    except Exception as exc:                        # noqa: BLE001
        print(f"[studio] طبقات الزينة اتخطت ({type(exc).__name__}) — "
              "بنرجع للطريقة القديمة", flush=True)
        return None
