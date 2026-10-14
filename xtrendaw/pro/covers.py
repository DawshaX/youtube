"""🖼️ محرّك الأغلفة عالية النقر (High-CTR Covers).

الحقيقة المقيسة: الغلاف بيحدّد **نص** قرار المشاهد إنه يدوس.
في الشورتس، أول فريم هو الغلاف — فبيبقى أهم من الغلاف نفسه في الفيديو الطويل.

مبادئ مثبتة (من تحليل قنوات المليون+):
    1. **٣ كلمات كتير** — العين بتقرا ٣ كلمات في نص ثانية.
    2. **تباين عالي** — نص فاتح على خلفية غامقة أو العكس (مفيش نص رمادي).
    3. **عنصر بشري/وجه** بيرفع النقر 30-40% — لكن عنا **ممنوع وجوه حقيقية**،
       فبنستخدم الشخصيات الأصلية أو رمز معبّر.
    4. **مساحة تنفّس** — الغلاف المزحوم بيتجاهله المخ.
    5. **لون واحد قوي** بيميّز الحلقة عن غيرها في الفيد.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920

# لوحات ألوان عالية التباين (خلفية, تعبئة, حافة)
PALETTES = {
    "ذهبي":   ((14, 12, 20), (245, 216, 145), (255, 247, 230)),
    "أخضر":   ((8, 20, 16), (120, 230, 175), (235, 255, 245)),
    "أزرق":   ((9, 14, 30), (130, 190, 255), (235, 245, 255)),
    "بنفسجي": ((18, 10, 30), (200, 155, 255), (245, 238, 255)),
    "أحمر":   ((26, 10, 12), (255, 145, 130), (255, 240, 235)),
    "تركواز": ((6, 22, 26), (120, 240, 235), (235, 255, 255)),
    "وردي":   ((28, 14, 22), (255, 170, 200), (255, 242, 248)),
}

FONT_CANDIDATES = (
    "assets/fonts/Tajawal-Bold.ttf",
    "assets/fonts/Amiri-Bold.ttf",
    "assets/fonts/AmiriQuran-Regular.ttf",
)

# ── شخصيات آمنة للأغلفة: مبدئيًا **بلا وجوه بشرية** (مناسبة للنشر الإسلامي
#    وللقنوات اللي ما بتحبش الوجوه). اللي عايز يفتحها يضبط NOOR_PRO_FACES=1.
SAFE_SOUL_IDS = ("nour", "siraj", "tina", "lughz", "san3a", "mudalla",
                 "mayya", "pastel", "mahna", "lama", "sakan", "fajr")


def _seed(*p) -> int:
    return int(hashlib.sha256("|".join(str(x) for x in p).encode()).hexdigest()[:10], 16)


def _font(size: int):
    from PIL import ImageFont

    root = Path(__file__).resolve().parents[2]
    for rel in FONT_CANDIDATES:
        p = root / rel
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _grab(video: Path, at: float, out: Path, blur: int = 0) -> bool:
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},setsar=1")
    if blur:
        vf += f",boxblur={blur}:1"
    r = subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{max(0.05, at):.2f}", "-i", str(video),
         "-frames:v", "1", "-vf", vf, str(out)],
        capture_output=True, timeout=120,
    )
    return r.returncode == 0 and out.exists()


def _wrap(text: str, font, draw, max_w: int, max_lines: int = 3) -> list[str]:
    words = str(text or "").split()
    lines, cur = [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
            if len(lines) >= max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return lines


def _field_word(title_hook: str, episode_id: str = "") -> str:
    """يختار كلمة الشارة: من نص الهوك لو فيها كلمة مجالية، وإلا كلمة عامة."""
    hay = f"{title_hook} {episode_id}"
    table = (
        (("آية", "قرآن", "سورة", "تلاوة", "اية"), "تدبّر"),
        (("دعاء", "دعوة", "تضرع"), "دعاء"),
        (("حديث", "سنة", "نبوي"), "سنّة"),
        (("قصة", "قصص", "سيرة"), "عبرة"),
        (("صبر", "حزن", "هم", "بلاء"), "سكينة"),
        (("علم", "معلومة", "حقيقة", "سبحان"), "تأمّل"),
        (("ضحك", "هزار", "نكتة"), "خفة"),
        (("صحة", "طب", "جسم"), "صحة"),
        (("مال", "رزق", "فلوس"), "رزق"),
    )
    for keys, word in table:
        if any(k in hay for k in keys):
            return word
    return ("نور", "خير", "أمل", "حكمة", "سكينة")[_seed(episode_id or hay, "fw") % 5]


def _ornament(canvas: Image.Image, accent, bg, *, field: str = "نور") -> None:
    """شارة زخرفية إسلامية (نجمة ثمانية + كلمة المجال) — بديل آمن للوجوه.

    مرسومة كلها بالكود: مفيش صورة خارجية ولا حقوق، وبتتكرر بنفس الهوية.
    """
    R = 168                                   # نصف القطر
    cx, cy = int(W * 0.5), int(H * 0.755)
    pad = 46
    layer = Image.new("RGBA", (R * 2 + pad * 2, R * 2 + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox = oy = R + pad

    # حلقة خارجية مزدوجة
    d.ellipse([ox - R, oy - R, ox + R, oy + R], fill=(*bg, 232),
              outline=(*accent, 245), width=9)
    d.ellipse([ox - R + 18, oy - R + 18, ox + R - 18, oy + R - 18],
              outline=(*accent, 140), width=4)

    # نجمة ثمانية (ختم سليمان) — رمز هندسي إسلامي
    import math

    pts = []
    for i in range(16):
        ang = math.pi / 2 + i * math.pi / 8
        rad = (R - 42) if i % 2 == 0 else (R - 42) * 0.62
        pts.append((ox + rad * math.cos(ang), oy - rad * math.sin(ang)))
    d.polygon(pts, outline=(*accent, 225), width=6)

    # قرص غامق في القلب + كلمة المجال فوقه (وضوح مضمون)
    d.ellipse([ox - 88, oy - 88, ox + 88, oy + 88], fill=(*bg, 245),
              outline=(*accent, 200), width=5)
    font = _font(66)
    tw = d.textlength(field, font=font)
    d.text((ox - tw / 2, oy - 42), field, font=font, fill=(*accent, 255))

    canvas.alpha_composite(layer, (int(W * 0.5 - layer.width / 2),
                                   int(H * 0.755 - layer.height / 2)))


def build(video: Path | None, out_png: Path, *, title_hook: str = "",
          brand: str = "روح الله", episode_id: str = "",
          palette: str = "", at: float = 1.2) -> Path:
    """يبني غلاف احترافي: فريم حقيقي + تدريج + هوك ٣ كلمات + علامة البراند.

    الفشل آمن: لو الفريم ما اتسحش، خلفية متدرّجة بديلة بتتولّد فورًا.
    """
    out_png.parent.mkdir(parents=True, exist_ok=True)
    name = palette or (list(PALETTES)[_seed(episode_id, "pal") % len(PALETTES)])
    bg, accent, light = PALETTES.get(name, PALETTES["ذهبي"])

    base: Image.Image | None = None
    if video and Path(video).exists():
        tmp = out_png.with_suffix(".raw.png")
        # نجرب ٣ لحظات لحد ما نلاقي فريم واضح (مش أسود/أبيض فاضي)
        for moment in (at, max(0.4, at * 0.5), 0.3):
            if not _grab(Path(video), moment, tmp):
                continue
            im = Image.open(tmp).convert("RGB")
            small = im.resize((60, 106))
            px = list(small.getdata())
            lum = sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px) / len(px)
            spread = (max(sum(p) for p in px) - min(sum(p) for p in px)) / 765
            if 22 < lum < 232 and spread > 0.12:
                base = im
                break
        if base is None and tmp.exists():
            base = Image.open(tmp).convert("RGB")
        tmp.unlink(missing_ok=True)

    if base is None:
        # خلفية مولّدة: تدرّج شعاعي + حبيبات (مفيش صورة قالب)
        base = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(base, "RGBA")
        for i in range(46, 0, -1):
            f = i / 46
            r = int(W * 1.15 * f)
            alpha = int(52 * (1 - f))
            d.ellipse([W // 2 - r, H // 3 - r, W // 2 + r, H // 3 + r],
                      fill=(*accent, alpha))
        base = base.filter(ImageFilter.GaussianBlur(34))

    # ── تدريج الغلاف: تغميق قوي + ضباب ناعم في منطقة النص
    #    (مهم: الكابشنز المحروقة في الفريم الأصلي ما تبانش تحت العنوان)
    canvas = base.convert("RGBA")
    band_top, band_bot = int(H * 0.30), int(H * 0.72)
    try:
        region = base.crop((0, band_top, W, band_bot)).filter(ImageFilter.GaussianBlur(26))
        canvas.paste(region, (0, band_top))
    except Exception:
        pass

    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle([0, 0, W, int(H * 0.30)], fill=(*bg, 214))          # فوق
    sd.rectangle([0, band_top, W, band_bot], fill=(*bg, 232))         # شريط النص
    sd.rectangle([0, band_bot, W, H], fill=(*bg, 236))               # تحت
    canvas = Image.alpha_composite(canvas, shade)

    # توهّج خلف الهوك
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-W // 5, int(H * 0.30), W + W // 5, int(H * 0.72)],
               fill=(*accent, 46))
    glow = glow.filter(ImageFilter.GaussianBlur(88))
    canvas = Image.alpha_composite(canvas, glow)

    draw = ImageDraw.Draw(canvas)

    # ── البراند (أعلى اليمين)
    bf = _font(54)
    btw = draw.textlength(brand, font=bf)
    draw.text((W - btw - 54, 62), brand, font=bf, fill=accent,
              stroke_width=3, stroke_fill=(0, 0, 0, 200))
    draw.line([(W - btw - 54, 132), (W - 54, 132)], fill=accent, width=4)

    # ── الهوك (٣ كلمات كتير) — أكبر حاجة في الغلاف
    hook = " ".join(str(title_hook or "").split()[:6]).strip(" .،,|")
    if not hook:
        hook = "آية وسكينة"

    size = 138 if len(hook) < 26 else (118 if len(hook) < 40 else 98)
    for _ in range(4):                       # نصغّر لحد ما يدخل في الشاشة
        font = _font(size)
        lines = _wrap(hook, font, draw, int(W * 0.86), max_lines=3)
        widths = [draw.textlength(l, font=font) for l in lines]
        if max(widths or [0]) <= W * 0.88 or size <= 62:
            break
        size -= 12

    line_h = int(size * 1.34)
    total = len(lines) * line_h
    y0 = int(H * 0.40) - total // 2

    # لوح كامل العرض خلف النص — بيمنع أي حاجة تحته تبان وبيخلي القراءة مضمونة
    plate_top = y0 - int(size * 0.42)
    plate_bot = y0 + total + int(size * 0.26)
    draw.rounded_rectangle(
        [int(W * 0.035), plate_top, int(W * 0.965), plate_bot],
        radius=30, fill=(*bg, 226), outline=(*accent, 120), width=3,
    )

    for i, line in enumerate(lines):
        lw = draw.textlength(line, font=font)
        x = (W - lw) / 2
        y = y0 + i * line_h
        draw.text((x, y), line, font=font, fill=light,
                  stroke_width=8, stroke_fill=(*bg, 255))
        # خط تأكيد تحت أهم سطر
        if i == len(lines) - 1:
            draw.line([(x, y + size + 22), (x + lw, y + size + 22)],
                      fill=accent, width=8)

    # ── الشارة السفلية: زخرفة إسلامية افتراضيًا (بلا وجوه بشرية)
    #    الأغلفة لازم تكون مناسبة للنشر الديني: **مفيش وجوه آدميين** إلا لو
    #    صاحب القناة طلبها صراحةً بـ NOOR_PRO_FACES=1 (للمحتوى غير الديني).
    try:
        import os as _os

        allow_faces = str(_os.environ.get("NOOR_PRO_FACES", "0")) == "1"
        drawn = False
        if allow_faces:
            from xtrendaw.noor_next import souls as _souls

            soul = _souls.pick_soul({"id": episode_id, "kind": "short",
                                     "emotion": "حياة", "field": "حياة"})
            png = _souls.portrait(soul) if soul else None
            if png and Path(png).exists():
                sp = Image.open(png).convert("RGBA")
                side = min(sp.size)
                left = (sp.width - side) // 2
                top = (sp.height - side) // 2
                sp = sp.crop((left, top, left + side, top + side)).resize(
                    (330, 330), Image.Resampling.LANCZOS)
                mask = Image.new("L", (330, 330), 0)
                ImageDraw.Draw(mask).ellipse((2, 2, 327, 327), fill=255)
                sp.putalpha(mask)
                ring = Image.new("RGBA", (362, 362), (0, 0, 0, 0))
                ImageDraw.Draw(ring).ellipse(
                    [0, 0, 361, 361], outline=(*accent, 240), width=12)
                ring.alpha_composite(sp, (16, 16))
                canvas.alpha_composite(ring, (int(W * 0.5 - 181), int(H * 0.735)))
                drawn = True
        if not drawn:
            _ornament(canvas, accent, bg, field=_field_word(title_hook, episode_id))
    except Exception:
        pass

    # ── السهم السفلي (بيقول «استنى… لسه فيه»)
    try:
        ad = ImageDraw.Draw(canvas)
        cx, cy = W // 2, int(H * 0.935)
        for k in range(2):
            yy = cy + k * 30
            ad.polygon([(cx - 42, yy), (cx + 42, yy), (cx, yy + 34)],
                       fill=(*accent, 210 - k * 70))
    except Exception:
        pass

    canvas.convert("RGB").save(out_png, quality=95)
    return out_png


def compose(topic: dict, out_path: Path, *, seed: str = "",
            video: Path | None = None, frame_at: float = 1.2,
            title: str = "") -> Path:
    """واجهة متوافقة مع `brand.compose_cover` القديمة — نفس الشكل، جودة أعلى."""
    return build(video, out_path, title_hook=title or str(topic.get("hook") or ""),
                 episode_id=seed or str(topic.get("id") or ""),
                 at=frame_at)


# كلمات **ما تنفعش** تكون على غلاف: كلام عن الفيديو نفسه، أو حشو، أو ميتاداتا.
COVER_STOP = {
    "الفيديو", "فيديو", "الشورت", "شورت", "short", "shorts", "قناة", "اشترك",
    "تابعنا", "تابعونا", "الحلقة", "حلقة", "الجزء", "جزء", "سلسلة", "اليوم",
    "دلوقتي", "معاكم", "معنا", "تعالوا", "يلا", "ده", "دي", "هذا", "هذه",
    "من", "في", "على", "عن", "إلى", "الى", "اللي", "الذي", "التي", "و",
    "بلا", "مع", "كان", "لو", "أو", "او", "ثم", "قد", "كل", "أي", "اي",
}


def short_title(hook: str, limit: int = 6) -> str:
    """يجهّز كلمات الغلاف — **٣-٦ كلمات معنى**، مش أي كلام في الأول.

    ⚠️ درس حقيقي: النسخة الأولى كانت بتاخد أول ٦ كلمات من العنوان، فطلع
    غلاف مكتوب عليه «نفس الفيديو» — يعني **كلام عن الفيديو مش عن الموضوع**.
    الغلاف لازم يقول **الفايدة** للمشاهد في لمحة، فبنشيل الحشو والميتاداتا.
    """
    raw = str(hook or "")
    # القوس والهاشتاج والرموز بتحرف المعنى على الغلاف — نشيلهم
    raw = re.sub(r"[#﴿﴾«»\[\]()\"'|]", " ", raw)
    words = [w.strip(" .،,:;!?…—–-") for w in raw.split()]
    keep = [w for w in words if w and w not in COVER_STOP and len(w) > 1]
    # لو التنقية شالت كل حاجة (عنوان غريب)، نرجع للكلمات الأصلية بلا حشو القناة
    if not keep:
        keep = [w for w in words if w and w not in COVER_STOP] or words
    out = " ".join(keep[:limit]).strip()
    return out or "آية وسكينة"
