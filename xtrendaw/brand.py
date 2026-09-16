"""غلاف الحلقة — من أفضل فريم في الفيديو الفعلي، مش قالبًا ثابتًا.

المنصات (Shorts/Reels) بتاخد غلاف رأسي. بنسحب فريم حقيقي من الفيديو
المُجمَّع (لحظة الخطاف)، ونضيف عنوان قصير (≤3 كلمات) واسم البراند.
مفيش صور قالب: لو الفريم ما اتسحش، الخلفية تتولّد نيون إجرائيًا.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import settings, textrender
from .tts import ffmpeg

W, H = settings.VIDEO["width"], settings.VIDEO["height"]


def _grab_frame(video: Path, at: float, out_png: Path) -> bool:
    r = subprocess.run(
        [ffmpeg(), "-y", "-ss", f"{max(0.05, at):.2f}", "-i", str(video),
         "-frames:v", "1",
         "-vf", (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                 f"crop={W}:{H},setsar=1"),
         str(out_png)],
        capture_output=True, timeout=120,
    )
    return r.returncode == 0 and out_png.exists()


def compose_cover(topic: dict, out_path: Path, seed: str = "",
                  video: Path | None = None, frame_at: float = 0.4,
                  title: str = "") -> Path:
    """غلاف رأسي سينمائي: فريم حقيقي من الحلقة + عنوان قصير بارز."""
    from . import scenes

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base: Image.Image | None = None
    if video is not None and Path(video).exists():
        frame_tmp = out_path.with_suffix(".frame.png")
        if _grab_frame(Path(video), frame_at, frame_tmp):
            base = Image.open(frame_tmp).convert("RGB")

    if base is None:
        bg = scenes.render_bg(out_path.with_suffix(".bg.png"), "hook",
                              seed or topic["id"])
        base = Image.open(bg).convert("RGB")

    # تدرّج وسط خفيف عشان العنوان يقرا فوق أي فريم
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(grad)
    band = int(H * 0.42)
    top0 = int(H * 0.30)
    for i in range(band):
        t = 1 - abs(i - band / 2) / (band / 2)
        d.line([(0, top0 + i), (W, top0 + i)],
               fill=(8, 2, 4, int(150 * t ** 1.4)), width=1)
    base = Image.alpha_composite(base.convert("RGBA"), grad)

    # العنوان: ≤3 كلمات بخط كبير (قاعدة التغليف في المخطط)
    display = (title or topic.get("title_ar") or topic.get("angle", "")).strip()
    words = display.split()
    short_title = " ".join(words[:3])
    if len(words) > 3:
        short_title += "…"
    if short_title:
        title_layer = textrender.text_image(
            short_title, out_path.with_suffix(".t.png"),
            canvas=(W, H), font_size=118, y_ratio=0.46, max_width_ratio=0.86,
            fill="#ffffff", stroke="#12040a", stroke_width=7,
        )
        base.paste(Image.open(title_layer), (0, 0), Image.open(title_layer))

    if settings.LOGO.exists():
        logo = scenes.load_logo(240)
        base.paste(logo, ((W - 240) // 2, int(H * 0.12)), logo)

    # اسم البراند + التاجلاين تحت — هوية واحدة في كل المخرجات
    for txt, yr, fs, fill in [
        (settings.BRAND["name"], 0.87, 64, "#ffd166"),
        (settings.BRAND["tagline_ar"], 0.925, 38, "#ff9f9f"),
    ]:
        layer = textrender.text_image(
            txt, out_path.with_suffix(".b.png"), canvas=(W, H),
            font_size=fs, fill=fill, y_ratio=yr, max_width_ratio=0.8,
            stroke_width=4,
        )
        base.paste(Image.open(layer), (0, 0), Image.open(layer))

    base.convert("RGB").save(out_path, "PNG")
    for tmp in (".bg.png", ".t.png", ".b.png", ".frame.png"):
        out_path.with_suffix(tmp).unlink(missing_ok=True)
    return out_path
