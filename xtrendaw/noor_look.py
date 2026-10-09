"""🎬 أنماط المونتاج — كل فيديو له شكل، وشخصية بتتكلم، ومشهد يوصف المعنى.

١٢ نمط بصري + ٦ شخصيات بأصوات نيورال مختلفة. النص الديني مش بيتألف هنا.
كلام الله يفضل تلاوة. الشخصية بتتكلم الهوك والمعنى والخاتمة بس.
المشاهد استعلامات إنجليزي لمكتبات حرة (Pexels/Pixabay/NASA/كومنز) عشان اللقطة
توصف المشهد، مش خلفية عشوائية.
"""
from __future__ import annotations

import os
from pathlib import Path

HOSTS = [
    {"name": "نور", "voice": "ar-EG-SalmaNeural", "color": (232, 196, 140), "role": "مضيفة"},
    {"name": "سَكينة", "voice": "ar-SA-ZariyahNeural", "color": (168, 198, 214), "role": "صوت هادي"},
    {"name": "أمل", "voice": "ar-SY-AmanyNeural", "color": (186, 214, 176), "role": "صوت دافي"},
    {"name": "حَكيم", "voice": "ar-SA-HamedNeural", "color": (214, 176, 120), "role": "راوي"},
    {"name": "راوي", "voice": "ar-EG-ShakirNeural", "color": (196, 168, 140), "role": "حكّاء"},
    {"name": "فارس", "voice": "ar-JO-TaimNeural", "color": (160, 176, 204), "role": "معلّق"},
]

# grade = سلسلة فلاتر ffmpeg على الخلفية. بلا موسيقى — التأثير بصري بس.
LOOKS = [
    {"id": "cinema", "name": "سينما عريضة", "y": 0.40,
     "grade": "drawbox=x=0:y=0:w=iw:h=78:color=black:t=fill,drawbox=x=0:y=ih-78:w=iw:h=78:color=black:t=fill,eq=contrast=1.06:saturation=1.08"},
    {"id": "gold", "name": "إطار ذهب", "y": 0.42,
     "grade": "drawbox=x=28:y=28:w=iw-56:h=ih-56:color=0xD4AF37:t=5,eq=saturation=1.12:gamma=1.03"},
    {"id": "host", "name": "شخصية في الكادر", "y": 0.36,
     "grade": "vignette=PI/5,eq=contrast=1.04:saturation=1.1"},
    {"id": "dawn", "name": "فجر دافي", "y": 0.44,
     "grade": "eq=saturation=1.28:gamma=1.06:contrast=1.04,colorbalance=rs=0.08:gs=0.02"},
    {"id": "ink", "name": "ليل حبر", "y": 0.40,
     "grade": "eq=brightness=-0.04:contrast=1.12:saturation=0.9,vignette=PI/4"},
    {"id": "doc", "name": "وثائقي", "y": 0.34,
     "grade": "eq=contrast=1.08:saturation=0.95,drawbox=x=0:y=ih-150:w=iw:h=150:color=black@0.45:t=fill"},
    {"id": "emerald", "name": "زمرد", "y": 0.43,
     "grade": "colorbalance=gs=0.08:bs=0.04,eq=saturation=1.2:contrast=1.05"},
    {"id": "sand", "name": "رمل وقمر", "y": 0.45,
     "grade": "colorbalance=rs=0.1:gs=0.04,eq=gamma=1.05:saturation=1.15"},
    {"id": "moon", "name": "قمر", "y": 0.38,
     "grade": "eq=brightness=-0.02:saturation=1.05:gamma=0.98,vignette=PI/5"},
    {"id": "split", "name": "شريط عنوان", "y": 0.58,
     "grade": "drawbox=x=0:y=ih-420:w=iw:h=420:color=black@0.55:t=fill,eq=contrast=1.05"},
    {"id": "soft", "name": "ضباب ناعم", "y": 0.42,
     "grade": "eq=contrast=0.98:saturation=1.18:gamma=1.08,vignette=PI/6"},
    {"id": "chapter", "name": "فصل", "y": 0.46,
     "grade": "drawbox=x=48:y=120:w=iw-96:h=8:color=0xE8D5A3:t=fill,drawbox=x=48:y=ih-120:w=iw-96:h=8:color=0xE8D5A3:t=fill,eq=saturation=1.1"},
]

# كلمات عربية في الهوك/الموضوع → لقطة إنجليزي دقيقة للمكتبات الحرة
SCENE_HINTS = [
    ("نار", ["embers cooling to mist", "desert night fire glow no people", "stone desert dawn"]),
    ("بحر", ["ocean aerial waves", "sea horizon sunrise", "calm deep blue water"]),
    ("حوت", ["deep ocean light rays", "underwater blue calm", "open sea dusk"]),
    ("قمر", ["crescent moon desert", "moon over still water", "night sky stars"]),
    ("مطر", ["rain on leaves close", "rain window glass", "green after rain"]),
    ("فجر", ["sunrise above clouds", "minaret silhouette dawn", "golden hour desert"]),
    ("نج", ["milky way night sky", "stars long exposure", "clear night desert"]),
    ("حمد", ["wheat field sunlight", "sunrise clouds gold", "still life water and fruit"]),
    ("شكر", ["sunflower field light", "morning meadow mist", "hands light no face"]),
    ("نصر", ["dawn after storm", "birds over calm sea", "green valley mist"]),
    ("يسر", ["light breaking through clouds", "path through forest morning", "calm lake sunrise"]),
    ("رحمة", ["soft morning light window", "rain then sun", "olive grove path"]),
    ("مسجد", ["empty mosque courtyard", "mosque arches light", "minaret silhouette"]),
    ("صلا", ["minaret dawn silhouette", "empty prayer hall light", "courtyard fountain calm"]),
    ("كتاب", ["open book pages light", "manuscript closeup", "library sunlight dust"]),
    ("جبل", ["mountain valley mist", "rocky mountain dawn", "cliff and clouds"]),
    ("صحر", ["desert dunes aerial", "sand wind sunrise", "lonely desert path"]),
    ("طائر", ["birds flying sunset", "bird over water", "flock sky gold"]),
    ("ماء", ["clear stream stones", "waterfall mist", "river calm aerial"]),
    ("طفل", ["flower blooming light", "soft morning garden", "sunlight through leaves"]),
]

KIND_SCENES = {
    "quran": ["mosque courtyard empty dawn", "quran pages soft light", "night sky calm"],
    "tafsir": ["open book window light", "arabic geometry gold", "quiet study lamp"],
    "hadith": ["olive tree wind", "courtyard fountain", "old manuscript light"],
    "qissa": ["desert caravan distant aerial", "sea horizon dawn", "mountain path mist"],
    "asma": ["stars milky way", "light through geometric window", "calm lake reflection"],
    "athkar": ["morning mist meadow", "sunrise clouds gold", "prayer beads wood"],
    "dua": ["rain on leaves", "candle light wood", "soft window light"],
    "quiz": ["open book aerial", "geometric pattern gold", "night sky"],
    "spirit": ["forest light rays", "ocean waves slow", "rain window glass"],
    "mujiza": ["ocean aerial light", "moon over water", "desert dawn aerial"],
    "hamd": ["wheat field sunlight", "sunrise above clouds", "fruit and water still"],
    "nasr": ["dawn after storm", "birds over calm sea", "green valley after rain"],
    "salah": ["minaret silhouette dawn", "empty mosque interior", "city sunrise aerial"],
    "hijri": ["crescent moon night", "lantern bokeh warm", "desert night stars"],
    "qfacts": ["open quran pages", "gold light marble", "arabic geometric art"],
    "proverb": ["old alley morning empty", "coffee cup window", "olive grove path"],
}


def scenes_for(item: dict) -> list[str]:
    blob = " ".join(str(item.get(k) or "") for k in ("hook", "who", "theme", "kind", "title"))
    found: list[str] = []
    for word, queries in SCENE_HINTS:
        if word in blob:
            found.extend(queries)
    base = list(KIND_SCENES.get(str(item.get("kind") or item.get("plan_kind") or ""), []) )
    out = []
    for q in found + base + ["calm nature aerial no people", "soft light architecture empty"]:
        if q not in out:
            out.append(q)
        if len(out) >= 4:
            break
    return out


def pick(item: dict) -> dict:
    seed = str(item.get("id") or item.get("hook") or item.get("kind") or "noor")
    n = sum(ord(c) for c in seed) + len(seed) * 17
    look = dict(LOOKS[n % len(LOOKS)])
    if look["id"] == os.environ.get("NOOR_LOOK_LAST"):
        look = dict(LOOKS[(n + 3) % len(LOOKS)])
    host = HOSTS[(n // 3) % len(HOSTS)]
    look["host"] = host["name"]
    look["voice"] = host["voice"]
    look["host_color"] = host["color"]
    look["role"] = host["role"]
    os.environ["NOOR_LOOK_LAST"] = look["id"]
    return look


def bind(item: dict, workdir: Path | None = None) -> dict:
    """يثبّت نمط الحلقة: صوت الشخصية، مشاهد مطابقة، وإطار بصري."""
    if item.get("_look_bound") and item.get("_look"):
        look = item["_look"]
    else:
        look = pick(item)
        item["_look"] = look
        item["_look_bound"] = True
        item["scenes"] = scenes_for(item)
        hook = str(item.get("hook") or "").strip()
        host = look["host"]
        if hook and not hook.startswith("معاكم"):
            item["hook"] = f"معاكم {host}. {hook}"
        outro = str(item.get("outro") or "").strip()
        sign = f"أنا {host}، من نور."
        if outro and sign not in outro:
            item["outro"] = outro + " " + sign
    os.environ["NOOR_LOOK_ID"] = look["id"]
    os.environ["NOOR_LOOK_NAME"] = look["name"]
    os.environ["NOOR_LOOK_VOICE"] = look["voice"]
    os.environ["NOOR_LOOK_HOST"] = look["host"]
    os.environ["NOOR_LOOK_Y"] = str(look["y"])
    os.environ["NOOR_LOOK_GRADE"] = look["grade"]
    try:
        from . import settings
        settings.VOICE_AR = look["voice"]
    except Exception:
        pass
    if workdir is not None:
        frame = Path(workdir) / "look_frame.png"
        try:
            draw_frame(look, frame)
            os.environ["NOOR_LOOK_FRAME"] = str(frame)
        except Exception:
            os.environ.pop("NOOR_LOOK_FRAME", None)
    return look


def draw_frame(look: dict, out: Path) -> Path:
    """إطار وبطاقة شخصية — رسم أصلي، مش صورة شخص حقيقي."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = tuple(look.get("host_color") or (220, 190, 140))
    # بطاقة الشخصية تحت شمال — واضحة إنها بتتكلم
    d.rounded_rectangle((36, 1680, 520, 1868), radius=28, fill=(8, 10, 16, 190))
    d.ellipse((58, 1704, 186, 1832), fill=col + (255,))
    d.ellipse((96, 1736, 148, 1788), fill=(255, 248, 236, 230))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
        small = font
    d.text((206, 1724), look.get("host") or "", font=font, fill=(255, 248, 236, 255))
    d.text((206, 1772), "يتكلم الآن · " + str(look.get("name") or ""), font=small,
           fill=(255, 214, 140, 230))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def compose_seg(ffmpeg_bin: str, bg: Path, png: Path, out: Path, *,
                ss: float, dur: float, fades: str, fps: int = 30) -> None:
    """يركب الخلفية + النمط + النص. لو النمط وقع، يرجع للتركيب العادي."""
    import subprocess
    grade = os.environ.get("NOOR_LOOK_GRADE") or ""
    frame = os.environ.get("NOOR_LOOK_FRAME") or ""
    frame_ok = bool(frame) and Path(frame).exists()

    def _run(use_grade: bool, use_frame: bool) -> subprocess.CompletedProcess:
        chain = "setsar=1" + (("," + grade) if use_grade and grade else "")
        cmd = [ffmpeg_bin, "-y", "-ss", f"{max(0.0, ss):.3f}", "-i", str(bg),
               "-loop", "1", "-t", f"{dur:.3f}", "-i", str(png)]
        if use_frame and frame_ok:
            cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", frame]
            vf = (f"[0:v]{chain}[v0];[1:v]format=rgba,{fades}[ov];"
                  f"[2:v]format=rgba[fr];[v0][fr]overlay=0:0:format=auto[vf];"
                  f"[vf][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        else:
            vf = (f"[0:v]{chain}[v0];[1:v]format=rgba,{fades}[ov];"
                  f"[v0][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        cmd += ["-filter_complex", vf, "-map", "[v]", "-t", f"{dur:.3f}",
                "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(out)]
        return subprocess.run(cmd, capture_output=True, text=True)

    r = _run(True, True)
    if r.returncode and grade:
        r = _run(False, True)
    if r.returncode and frame_ok:
        r = _run(False, False)
    if r.returncode:
        raise RuntimeError("فصل النمط فشل: " + (r.stderr or "")[-300:])
