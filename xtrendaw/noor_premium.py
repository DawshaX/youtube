"""نور بريميوم — شورتس إسلامية بجودة عالية، بكل المصادر المجانية وبلا مفاتيح.

ليه جديد؟ (2026-09-20) الفيديوهات القديمة كانت: صوت آلي + لقطات عشوائية + نص
مركّب ⇒ «بايظة ومش مفهومة» و0 مشاهدات. القواعد هنا:

1) **النص مقدّس ومضبوط**: آية بالنص العثماني + تفسير ميسّر من api.alquran.cloud
   (مجاني بلا مفتاح) — صفر تخمين، صفر هلوسة.
2) **التلاوة بشر حقيقي**: cdn.islamic.network — قرّاء معتمدون. ممنوع TTS على
   كلام الله.
3) **فونت قرآني حقيقي**: Amiri Quran (مجاني OFL) — شكل المصحف، مش خط عادي.
4) **مشاهد سينمائية مطابقة للمعنى** + تدريج لوني موحّد (تباين/تشبّع خفيف +
   فينييت + حبيبات فيلم) ⇒ إحساس «فيلم» مش «سلايدات».
5) **مفهومة**: الآية بتظهر سطر سطر مع التلاوة، وبعدها كارت «المعنى» بجملة
   واحدة واضحة ⇒ المشاهد يفهم من غير ما يقرأ تفسير.
6) **بلا موسيقى** — تلاوة بس (احترامًا لجمهور المحتوى الديني).

الاستخدام:
    python -m xtrendaw.noor_premium --surah 13 --ayah 28 --out /tmp/noor.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from . import settings
from .tts import ffmpeg

W, H, FPS = 1080, 1920, 30
FPS_LONG = 25            # الفيديو الطويل: نص ثابت + حركة بطيئة → 25 إطار يكفي
PRESET_LONG = "ultrafast"  # أسرع 3× من veryfast — والفرق مش ظاهر في النص الثابت
CACHE = settings.STATE / "noor_cache"
FONT_Q = settings.FONTS / "AmiriQuran-Regular.ttf"     # الخط القرآني (المصحف)
FONT_DISPLAY = settings.FONTS / "Amiri-Bold.ttf"        # للعرض على الموبايل
FONT_UI = settings.FONTS / "Tajawal-Regular.ttf"
FONT_UI_B = settings.FONTS / "Tajawal-Bold.ttf"
UA = {"User-Agent": "NoorShorts/1.0 (free Islamic shorts; educational)"}
APIQ = "https://api.alquran.cloud/v1"
CDN = "https://cdn.islamic.network/quran/audio"

# قرّاء هادئون مؤثرون (تُختار حكمة كل حلقة)
# ترتيب البدائل لو قارئ ناقص على المصدر (بق حقيقي: الغامدي 404 دايمًا)
RECITER_FALLBACK = ["husary", "minshawi", "shatri", "abdulbasitmurattal"]
# (غامدي متسجّل للتاريخ بس — ملفاته 404 دايمًا، مش داخل التناوب ولا البدائل)
RECITERS = {
    # ترتيب البدائل (RECITER_FALLBACK) بيستخدم المفاتيح دي بالاسم
    "husary":   ("ar.husary", 128, "محمود خليل الحصري"),
    "minshawi": ("ar.minshawi", 128, "محمد صديق المنشاوي"),
    "ghamdi":   ("ar.saadalghamdi", 64, "سعد الغامدي"),
    "shatri":   ("ar.shaatree", 128, "أبو بكر الشاطري"),
    "abdulbasitmurattal": ("ar.abdulbasitmurattal", 64, "عبد الباسط عبد الصمد"),
}

GRADE = ("eq=contrast=1.07:saturation=1.05:brightness=-0.015,"
         "colorbalance=rs=.02:bs=.03,"
         "vignette=PI/5")


# ─────────────────────────── المحتوى ───────────────────────────

def _cached_json(url: str, key: str) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{key}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                timeout=40) as r:
        data = json.load(r)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def ayah_text(surah: int, ayah: int, ayah_to: int | None = None) -> dict:
    """النص العثماني (آية أو نطاق آيات) + الأرقام العالمية للتلاوة.

    الأرقام العالمية (1..6236) مهمة: الـCDN بيرقّم التلاوات بالرقم العالمي،
    مش برقم السورة+الآية (اتكشف بالتجربة: 13:28 = 1735).
    """
    end = int(ayah_to or ayah)
    parts, globals_, nums = [], [], []
    surah_name = surah_en = ""
    for n in range(int(ayah), end + 1):
        d = _cached_json(f"{APIQ}/ayah/{surah}:{n}/quran-uthmani",
                         f"uthmani-{surah}-{n}")["data"]
        parts.append(d["text"].strip())
        globals_.append(int(d["number"]))
        nums.append(int(d["numberInSurah"]))
        surah_name = d["surah"]["name"]
        surah_en = d["surah"]["englishName"]
    return {"text": " ".join(parts), "surah": surah_name, "surah_en": surah_en,
            "number": nums[0], "number_to": nums[-1], "surah_n": int(surah),
            "globals": globals_}


def ayah_tafsir(surah: int, ayah: int) -> str:
    """التفسير الميسّر — معنى واحد واضح يفهمه أي مشاهد."""
    d = _cached_json(f"{APIQ}/ayah/{surah}:{ayah}/ar.muyassar",
                     f"muyassar-{surah}-{ayah}")["data"]
    return (d.get("text") or "").strip()


def _fetch_audio(slug: str, kb: int, num: int, mp3: Path) -> bool:
    """ينزّل ملف آية واحدة للقارئ المحدّد → True/False (مفيش استثناءات)."""
    for kb_ in dict.fromkeys((kb, 128, 64)):
        try:
            url = f"{CDN}/{kb_}/{slug}/{num}.mp3"
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=120) as r:
                body = r.read()
            if len(body) > 1500:
                mp3.write_bytes(body)
                return True
        except Exception:                      # noqa: BLE001
            continue
    return False


def recitation(surah: int, ayah: int, reciter: str, workdir: Path,
               globals_: list[int] | None = None) -> Path:
    """تلاوة حقيقية لقارئ معتمد (آية أو نطاق) → WAV واحد.

    🛡️ إصلاح جذري (بق حقيقي 2026-09-21): بعض القرّاء ملفاتهم ناقصة على
    المصدر (سعد الغامدي مثلًا 404 على كل الجودات) — وكان ده بيوقف الدورة
    كلها في حلقة مكسورة للأبد. دلوقتي: القارئ المطلوب → لو فشل نجرّب باقي
    القرّاء المعتمدين بالترتيب، والمزيج المكسور بيتسجّل في الكاش عشان ما
    نضيّعش وقت فيه تاني. **مفيش دورة تفشل بسبب قارئ ناقص.**
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    if not globals_:
        a = ayah_text(surah, ayah)
        globals_ = a["globals"]

    order = [reciter] + [r for r in RECITER_FALLBACK if r != reciter]
    wavs: list[Path] = []
    used: str | None = None
    for num in globals_:
        got = False
        for r in order:
            slug, kb, _name = RECITERS[r]
            mp3 = CACHE / f"{slug}-{num}.mp3"
            bad = CACHE / f"bad-{slug}-{num}"
            if not mp3.exists():
                if bad.exists() and r == reciter:
                    continue                    # جرّبناه قبل كده وفشل
                if not _fetch_audio(slug, kb, num, mp3):
                    try:
                        bad.touch()
                    except Exception:
                        pass
                    continue
            w = workdir / f"rec_{r}_{num}.wav"
            if not w.exists():
                rr = subprocess.run([ffmpeg(), "-y", "-i", str(mp3), "-ar",
                                     "44100", "-ac", "2", "-c:a", "pcm_s16le",
                                     str(w)], capture_output=True)
                if rr.returncode:
                    mp3.unlink(missing_ok=True)   # كاش فاسد → يتنزّل تاني
                    continue
            wavs.append(w)
            used = r
            got = True
            break
        if not got:
            raise RuntimeError(f"التلاوة مش متاحة لآية {num} عند أي قارئ")
    if used and used != reciter:
        print(f"[noor] ↺ القارئ {reciter} ناقص على المصدر — استخدمت {used}",
              flush=True)
    if len(wavs) == 1:
        return wavs[0]
    lst = workdir / "rec_concat.txt"
    lst.write_text("".join(f"file '{w.resolve()}'\n" for w in wavs),
                   encoding="utf-8")
    out = workdir / f"rec_{surah}_{ayah}_{len(wavs)}.wav"
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
                    str(out)], capture_output=True, check=True)
    return out

def dur_of(path: Path) -> float:
    out = subprocess.run([ffmpeg(), "-i", str(path)], capture_output=True,
                         text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


# ─────────────────────────── الصورة ───────────────────────────

def _lines(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    from .textrender import wrap_ar
    return [l for l in wrap_ar(text, font, max_w) if l.strip()]


def _shaped(line: str) -> str:
    """النص كما هو لما فيه raqm (الرسم نفسه بيتشكّل)، وإلا تشكيل يدوي.

    بق حقيقي (2026-09-20): تمرير نص مُشكَّل يدويًا لـPIL اللي عنده raqm
    بيكسر العربي (حروف منفصلة/ترتيب معكوس) — «مش مفهومة» كان جزء منه كده.
    """
    from . import textrender as tr
    return line if tr.HAS_RAQM else tr.shape_ar(line)


def overlay(lines: list[str], out: Path, *, size: int = 84, y: float = 0.42,
            color=(255, 253, 246, 255), font_path: Path | None = None,
            halo: int = 30, max_w: int | None = None, spacing: float = 1.55,
            tag: str = "", max_lines: int = 4, scrim_alpha: int = 170,
            bold_halo: int = 215) -> Path:
    """نص عربي واضح على أي خلفية — للشاشات الصغيرة (شورتس).

    ثلاث طبقات عشان الوضوح (أهم سبب لعدم الفهم قبل كده):
      1) scrim: تعتيم متدرّج واسع ورا منطقة النص (135 → 170).
      2) هالة سوداء سميكة حوالين الحروف (halo + bold).
      3) الحرف نفسه بأبيض دافي — أعلى تباين ممكن.
    + auto-fit: لو النص طلع أكتر من max_lines سطر، الخط بيصغر لحد ما يظبط.
    """
    W_ = W if max_w is None else max_w
    from . import textrender as _tr
    kw = {"layout_engine": ImageFont.Layout.RAQM} if _tr.HAS_RAQM else {}
    _dir = {"direction": "rtl", "language": "ar"} if _tr.HAS_RAQM else {}
    fp = str(font_path or FONT_DISPLAY)

    # auto-fit: نجرّب الحجم، ولو الأسطر كتير نصغّره (بنجرّب لحد 12 مرة)
    sz, wrapped = size, []
    for _ in range(14):
        font = ImageFont.truetype(fp, sz, **kw)
        wrapped = []
        for raw in lines:
            wrapped += _lines(raw, font, W_ - 120)
        if len(wrapped) <= max_lines or sz <= 46:
            break
        sz -= 6
    line_h = int(sz * spacing)
    total = line_h * len(wrapped)
    y0 = int(H * y) - total // 2

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 1) scrim متدرّج بعرض الشاشة بالكامل
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    pad = int(sz * 1.5)
    top, bot = max(0, y0 - pad), min(H, y0 + total + pad)
    span = max(1, bot - top)
    for yy in range(top, bot):
        dtop = (yy - top) / span
        a = int(scrim_alpha * (math.sin(math.pi * dtop) ** 1.15))
        sd.line([(0, yy), (W, yy)], fill=(4, 6, 12, a))
    img = Image.alpha_composite(img, scrim)
    # 2) هالة سميكة (ضباب أسود) خلف كل سطر
    halo_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo_img)
    yy = y0
    for ln in wrapped:
        tw = hd.textlength(_shaped(ln), font=font, **_dir)
        hd.text(((W - tw) // 2, yy), _shaped(ln), font=font,
                fill=(0, 0, 0, bold_halo),
                stroke_width=max(2, sz // 22), stroke_fill=(0, 0, 0, bold_halo),
                **_dir)
        yy += line_h
    img = Image.alpha_composite(img, halo_img.filter(ImageFilter.GaussianBlur(halo)))
    # 3) الحرف الأبيض فوق الكل
    d = ImageDraw.Draw(img)
    yy = y0
    for ln in wrapped:
        tw = d.textlength(_shaped(ln), font=font, **_dir)
        d.text(((W - tw) // 2, yy), _shaped(ln), font=font, fill=color, **_dir)
        yy += line_h
    if tag:
        f2 = ImageFont.truetype(str(FONT_UI_B), max(38, sz // 2), **kw)
        tw = d.textlength(_shaped(tag), font=f2, **_dir)
        ty = y0 + total + int(sz * 0.55)   # مسافة أمان: ما يتلاصقش مع آخر سطر
        d.text(((W - tw) // 2, ty), _shaped(tag), font=f2,
               fill=(255, 214, 140, 240), stroke_width=2,
               stroke_fill=(0, 0, 0, 200), **_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def _still_clip(img: Path, seconds: float, out: Path, zoom_in: bool = True) -> Path:
    """صورة → لقطة متحركة (زوم بطيء 1.0→1.18) بإحساس سينمائي."""
    frames = max(2, int(seconds * FPS))
    z = "min(1.0+0.00065*on,1.18)" if zoom_in else "max(1.18-0.00065*on,1.0)"
    vf = (f"scale={int(W*1.7)}:-2:flags=lanczos,crop={int(W*1.7)}:{int(H*1.7)},"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={frames}:s={W}x{H}:fps={FPS},setsar=1")
    subprocess.run([ffmpeg(), "-y", "-loop", "1", "-i", str(img), "-t",
                    f"{seconds:.2f}", "-vf", vf, "-an", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                    str(out)], capture_output=True, check=True)
    return out


def scene_clip(query: str, seconds: float, workdir: Path, seed: str,
               idx: int) -> tuple[Path, str]:
    """لقطة فيديو حيّة من المصادر الشبكية ← وإلا صورة حقيقية متحركة.

    الاستعلام إنجليزي (بيكساباي/بكسلز/كومنز إنجليزي) والمشهد مطابق للمعنى.
    """
    from . import footage, scenes
    q = query
    clip = None
    try:
        clip = footage.fetch_clip(q, max(2.0, seconds),
                                  workdir / f"v{idx:02d}", f"{seed}:v{idx}")
    except Exception:
        clip = None
    if clip is not None:
        return clip, "فيديو حي"
    base = workdir / f"p{idx:02d}.jpg"
    ok = False
    try:
        ok = bool(scenes.fetch_real_visual(q, base))
    except Exception:
        ok = False
    if ok:
        return _still_clip(base, max(2.0, seconds), workdir / f"s{idx:02d}.mp4",
                           zoom_in=(idx % 2 == 0)), "صورة متحركة"
    # أمان أخير: خلفية مولّدة بالكود — الرندر ما يفشلش أبدًا (ولا حقوق لحد)
    print(f"[noor] ⚠ مفيش لقطة لـ«{q}» — خلفية مولّدة بالكود", flush=True)
    return _procedural_scene(max(2.0, seconds), workdir / f"g{idx:02d}.mp4",
                             idx), "خلفية مولّدة"



def _procedural_scene(seconds: float, out: Path, seed: int = 0) -> Path:
    """خلفية مولّدة محليًا (ffmpeg) — أمان أخير لو الشبكة فشلت.

    مش صورة لحد ولا لقطة من مكتبة: مولّدة بالكود = **صفر خطر حقوق**، وغامقة
    هادية عشان النص يبان. بتتحرّك ببطء (زوم + حبيبات) فتبان حيّة مش ساكنة.
    """
    pal = [("0x101a33", "0x2b1d4a"), ("0x0d2233", "0x1d3b4a"),
           ("0x1a1230", "0x3a2352"), ("0x0a1f2b", "0x24405a"),
           ("0x141026", "0x2d1f45")]
    c0, c1 = pal[seed % len(pal)]
    dur = max(2.0, seconds)
    # طبقة 1: تدرّج لوني متحرك (ffmpeg gradients) — ألوان ليلية هادية
    vf = (f"gradients=s={int(W*1.08)}x{int(H*1.08)}:c0={c0}:c1={c1}:"
          f"x0=200:y0=100:x1={int(W*1.05)}:y1={int(H*1.05)}:speed=0.008:"
          f"d={int(dur*FPS)}:r={FPS},"
          f"crop={W}:{H}:x='(in_w-out_w)*t/{dur:.1f}':y='(in_h-out_h)*0.5',"
          "eq=brightness=0.04:saturation=1.15,vignette=PI/5,format=yuv420p")
    subprocess.run([ffmpeg(), "-y", "-f", "lavfi", "-i", vf, "-t", f"{dur:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", str(out)], capture_output=True,
                   check=True)
    return out


def _mean_luma(clip: Path) -> float:
    """متوسط الإضاءة لمشهد (0–255) — لضبط الإضاءة التلقائي."""
    try:
        o = subprocess.run([ffmpeg(), "-ss", "1", "-i", str(clip), "-frames:v",
                            "1", "-vf", "signalstats,metadata=print:file=-",
                            "-f", "null", "-"], capture_output=True, text=True)
        m = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", o.stdout or "")
        return float(m.group(1)) if m else 90.0
    except Exception:
        return 90.0


def grade_and_concat(clips: list[Path], out: Path) -> Path:
    """تدريج لوني موحّد + إضاءة تلقائية + فينييت + حبيبات + دمج في مسار واحد.

    ✨ إضافة (2026-09-21): لو المشهد غامق (متوسط إضاءة < 60) — زي لقطات
    المسجد بالليل — بنرفع الظلال تلقائيًا عشان النص والتفاصيل تبان، من غير
    ما نفقد المزاج الهادئ.
    """
    lst = out.parent / "concat.txt"
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips),
                   encoding="utf-8")
    luma = min((_mean_luma(c) for c in clips), default=90.0)
    lift = ""
    if luma < 60:                       # غامق → نرفع الظلال بلطف
        b = min(0.10, (60 - luma) / 255 * 0.9)
        lift = f"eq=brightness={b:.3f}:gamma=0.96:saturation=1.05,"
    elif luma > 170:                    # ساطع قوي → نهدّي شويّة
        lift = "eq=brightness=-0.035:contrast=1.03,"
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"setsar=1,fps={FPS},{lift}{GRADE},noise=alls=5:allf=t+u,format=yuv420p")
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-vf", vf, "-an", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "20", str(out)],
                   capture_output=True, check=True)
    return out


# ─────────────────────── الصوت: كل ثانية فيها حياة ───────────────────────
# 🛑 بق حقيقي (2026-09-21 — شكوى صاحب القناة): «باقي الفيديو فاضي مفهوش صوت
# ولا كلام مما يقتل الفيديو». السبب: كارت المعنى (7ث) + الخاتمة (2.6ث) كانوا
# **صامتين تمامًا** — يعني 10 ثواني صمت في فيديو 22 ثانية! الإصلاح:
#   1) كل فصل ليه **تعليق منطوق** (edge-tts، صوت عربي وقور) بطول الفصل نفسه.
#   2) أجواء طبيعية هادئة (هواء/بحر مولّد بالكود) تحت الكلام — **بلا موسيقى**.
#   3) مفيش فصل واحد بلا صوت: لو النص قصير، الفصل يقصر معاه.


def _trim_silence(src: Path, workdir: Path, name: str) -> Path:
    """يشيل الصمت من أول وآخر المقطع الصوتي — صفر فراغ بين الفصول.

    بق حقيقي (2026-09-21): ملفات التلاوة والتعليق بتيجي وفيها صمت في الآخر
    (0.5–2 ثانية لكل مقطع) وده بيعمل فراغات ميتة في الفيديو. التنظيف ده
    بيخلّي كل فصل يبدأ بكلام فورًا وخلاص الفصل اللي قبله.
    """
    out = workdir / f"{name}_trim.wav"
    af = ("silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.06,"
          "areverse,"
          "silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.10,"
          "areverse")
    r = subprocess.run([ffmpeg(), "-y", "-i", str(src), "-af", af, "-c:a",
                        "pcm_s16le", str(out)], capture_output=True, text=True)
    return out if r.returncode == 0 and out.exists() else src


def say(text: str, workdir: Path, name: str, *, rate: str = "+0%",
        pitch: str = "-2Hz", voice: str | None = None,
        gap: float = 0.35) -> tuple[Path, float]:
    """تعليق منطوق → (ملف WAV، مدته + مسافة صغيرة).

    الصوت: edge-tts (نيورال عربي وقور). لو الشبكة وقعت، tts فيها احتياطي محلي.
    """
    from .tts import synthesize_line
    r = synthesize_line(text, "ar", workdir, name=f"v_{name}", rate=rate,
                        pitch=pitch, voice=voice)
    w = _trim_silence(Path(r["wav"]), workdir, f"v_{name}")
    return w, dur_of(w) + gap


def _ambience(seconds: float, out: Path, seed: int = 0) -> Path:
    """أجواء طبيعية مولّدة بالكود (هواء/بحر) — **بلا موسيقى وبلا حقوق** .

    ضوضاء بنّية مقطوعة الترددات العالية = إحساس هواء/بحر، بتتحرك ببطء
    (tremolo) فما بتبانش صناعية. بتتحط تحت التعليق بصوت واطي جدًا.
    """
    dur = max(3.0, seconds)
    # (بق حقيقي: فلتر tremolo بيرفض الترددات الواطية «Numerical result out of
    #  range» — بنستخدم تعديل سعة بالتايم لاين بدلًا منه)
    cut = [900, 700, 1100, 800][seed % 4]
    lfo = [17, 23, 19, 21][seed % 4]
    vf = (f"anoisesrc=r=44100:a=0.32:c=pink:d={dur:.2f},"
          f"lowpass=f={cut},highpass=f=80,"
          f"volume='0.55+0.3*sin(2*PI*t/{lfo})':eval=frame,"
          f"afade=t=in:st=0:d=2.5,afade=t=out:st={max(0.1, dur - 2.5):.2f}:d=2.5,"
          f"volume=0.45")
    subprocess.run([ffmpeg(), "-y", "-f", "lavfi", "-i", vf, "-c:a",
                    "pcm_s16le", str(out)], capture_output=True, check=True)
    return out


def _mix_track(pieces: list[tuple[float, Path, float]], total: float, out: Path,
               ambience: Path | None = None, amb_gain: float = 0.16) -> Path:
    """يركّب المسار الصوتي: كل قطعة في وقتها + الأجواء تحت الكل + ماسترينج.

    pieces: [(بداية بالثواني، ملف، معامل الصوت)] — بيسمح بالتلاقي (crossfade
    ضمني بـamix) فالانتقالات تبقى ناعمة بلا فراغ.
    """
    ins: list[str] = []
    fc: list[str] = []
    idx = 0
    if ambience is not None:
        ins += ["-i", str(ambience)]
        fc.append(f"[{idx}:a]volume={amb_gain},apad,atrim=0:{total:.2f}[amb]")
        idx += 1
    labels = []
    for k, (start, wav, gain) in enumerate(pieces):
        ins += ["-i", str(wav)]
        fc.append(f"[{idx}:a]volume={gain},adelay={int(max(0, start) * 1000)}"
                  f"|{int(max(0, start) * 1000)}[p{k}]")
        labels.append(f"[p{k}]")
        idx += 1
    alls = ("[amb]" if ambience is not None else "") + "".join(labels)
    fc.append(f"{alls}amix=inputs={len(labels) + (1 if ambience is not None else 0)}"
              f":normalize=0:dropout_transition=0,"
              f"loudnorm=I=-15:TP=-1.5:LRA=9,"
              f"afade=t=out:st={max(0.1, total - 0.45):.2f}:d=0.45,"
              f"atrim=0:{total:.2f}[a]")
    cmd = [ffmpeg(), "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[a]",
           "-t", f"{total:.2f}", "-c:a", "aac", "-b:a", "192k", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("تركيب الصوت فشل: " + (r.stderr or "")[-400:])
    return out


# ─────────────────────────── التركيب ───────────────────────────

def render(spec: dict, workdir: Path) -> dict:
    """يبني الفيديو: إثارة (تعليق) → آيات بتلاوة حقيقية → المعنى منطوق → خاتمة.

    ✨ كل فصل فيه **صوت منطوق** وطول الفصل = طول صوته (مفيش ثانية صامتة).
    spec: {surah, ayah, ayah_to, reciter, scenes[], hook, meaning, outro,
           brand, ayahs[] (للريلز: [{surah, ayah, ayah_to}])}
    """
    workdir.mkdir(parents=True, exist_ok=True)
    reciter = spec.get("reciter") or "husary"
    # آيات الفيديو: واحدة للسكوت، أو قائمة (ريلز لحد 3 دقايق)
    wants = spec.get("ayahs") or [{"surah": spec.get("surah"),
                                   "ayah": spec.get("ayah"),
                                   "ayah_to": spec.get("ayah_to")}]
    wants = [w for w in wants if w.get("surah") and w.get("ayah")]

    # ── 1) المادة العلمية + التلاوة (كل آية: نص + تفسير + تلاوة)
    items = []
    for w in wants[:4]:
        s, a1 = int(w["surah"]), int(w["ayah"])
        a2 = int(w.get("ayah_to") or a1)
        ay = ayah_text(s, a1, a2)
        taf = ayah_tafsir(s, a2)
        rec = recitation(s, a1, reciter, workdir, globals_=ay["globals"])
        rec = _trim_silence(rec, workdir, f"rec_{s}_{a1}")
        rd = dur_of(rec)
        if rd <= 1:
            continue
        items.append({"ay": ay, "taf": taf, "rec": rec, "rec_d": rd, "s": s})
    if not items:
        raise RuntimeError("مفيش آيات صالحة للرندر")

    hook = spec.get("hook") or "اسمع الآية دي للآخر… هتغيّر يومك"
    outro = spec.get("outro") or "تابعنا… آية وحديث كل ساعة"
    brand = spec.get("brand") or "نور — قرآن وتدبّر"
    # التفسير المنطوق: أول جملتين (الميسّر بيبدأ بالمعنى المباشر)
    def _spoken_taf(txt: str, limit: int = 260) -> str:
        txt = re.sub(r"\s+", " ", txt or "").strip()
        if len(txt) <= limit:
            return txt
        cut = txt[:limit].rsplit(" ", 1)[0]
        return cut + "."

    # ── 2) الفصول: كل فصل = (نص على الشاشة + صوته + مدته)
    beats: list[dict] = []
    w_hook, d_hook = say(hook, workdir, "hook", rate="+10%")
    beats.append({"lines": [hook], "audio": w_hook, "dur": d_hook + 0.25,
                  "size": 96, "tag": "", "reveal": False, "kind": "hook"})
    for k, it in enumerate(items):
        tag = ("﴿ " + it["ay"]["surah"] + " — " + str(it["ay"]["number"]) + " ﴾")
        beats.append({"lines": [it["ay"]["text"].strip()], "audio": it["rec"],
                      "dur": it["rec_d"] + 0.35, "size": 94, "tag": tag,
                      "reveal": True, "kind": "ayah"})
        spoken = _spoken_taf(spec.get("meaning") if len(items) == 1 else it["taf"])
        w_t, d_t = say(spoken, workdir, f"taf{k}", rate="+2%")
        beats.append({"lines": [spoken], "audio": w_t, "dur": d_t + 0.3,
                      "size": 72, "tag": "المعنى", "reveal": False,
                      "kind": "tafsir"})
    w_out, d_out = say(outro, workdir, "outro", rate="+6%")
    beats.append({"lines": [outro], "audio": w_out, "dur": d_out + 0.55,
                  "size": 80, "tag": brand, "reveal": False, "kind": "outro"})

    total = sum(b["dur"] for b in beats)

    # ── 3) الخلفية: مشاهد للثيم + أجواء طبيعية
    scene_qs = spec.get("scenes") or ["night sky milky way stars",
                                      "calm sea waves sunset",
                                      "clouds sunrise mountains",
                                      "mosque architecture night"]
    per = total / max(1, min(len(scene_qs), 5)) + 0.8
    clips, srcs = [], []
    for i in range(min(len(scene_qs), 5)):
        c, src = scene_clip(scene_qs[i], per, workdir, f"bg{i}", i)
        clips.append(c)
        srcs.append(src)
    bg = grade_and_concat(clips, workdir / "bg.mp4")
    amb = _ambience(total, workdir / "amb.wav", seed=len(hook))

    # ── 4) الفيديو: لكل فصل(فصول) شريحة من الخلفية + طبقة النص
    segs: list[Path] = []
    audio: list[tuple[float, Path, float]] = []
    t0 = 0.0
    for i, b in enumerate(beats):
        lines = b["lines"]
        if b["reveal"]:
            words = lines[0].split()
            groups = [words[j:j + 4] for j in range(0, len(words), 4)] or [words]
            n = len(groups)
            for k in range(1, n + 1):
                png = overlay([" ".join(" ".join(g) for g in groups[:k])],
                              workdir / f"b{i}_{k}.png", size=b["size"], y=0.40,
                              max_lines=4, tag=b["tag"] if k == n else "")
                d_ = b["dur"] / n
                segs.append(_clip_seg(bg, t0, d_, png, workdir, f"s{i}_{k}",
                                      last=False))
                t0 += d_
        else:
            st = b["size"] - (10 if b["kind"] == "tafsir" else 0)
            png = overlay(lines, workdir / f"b{i}.png", size=st, y=0.46,
                          max_lines=5, tag=b["tag"],
                          font_path=FONT_UI_B if b["kind"] != "ayah" else None)
            segs.append(_clip_seg(bg, t0, b["dur"], png, workdir, f"s{i}",
                                  last=(i == len(beats) - 1)))
            t0 += b["dur"]
        audio.append((sum(x["dur"] for x in beats[:i]), b["audio"], 1.0))

    lst = workdir / "segs.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs),
                   encoding="utf-8")
    silent = workdir / "silent.mp4"
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(silent)], capture_output=True, check=True)
    track = _mix_track(audio, total, workdir / "track.m4a", ambience=amb)
    out = workdir / "noor.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-i", str(silent), "-i", str(track),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a",
                        "aac", "-b:a", "192k", "-shortest", "-movflags",
                        "+faststart", str(out)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("دمج الصوت فشل: " + (r.stderr or "")[-400:])
    cover = workdir / "cover.png"
    subprocess.run([ffmpeg(), "-y", "-ss", f"{min(total - 0.5, 2.0):.2f}", "-i",
                    str(out), "-frames:v", "1", str(cover)],
                   capture_output=True, check=True)
    first = items[0]["ay"]
    return {"video": out, "cover": cover, "duration": total,
            "reciter": RECITERS[reciter][2], "surah": first["surah"],
            "ayah": first["number"], "text": first["text"],
            "tafsir": items[0]["taf"], "sources": srcs,
            "rec_duration": sum(i["rec_d"] for i in items),
            "ayahs_count": len(items), "has_voice": True}


def _clip_seg(bg: Path, t0: float, dur: float, png: Path, workdir: Path,
              name: str, last: bool = False) -> Path:
    """شريحة فيديو: جزء من الخلفية + طبقة نص (بتلاشي داخلي/خارجي ناعم)."""
    seg = workdir / f"{name}.mp4"
    d_ = max(0.4, dur)
    fades = "fade=t=in:st=0:d=0.4:alpha=1"
    if last:
        fades += f",fade=t=out:st={max(0.1, d_ - 0.8):.2f}:d=0.8:alpha=1"
    vf = ("[0:v]setsar=1[v0];[1:v]format=rgba," + fades +
          "[ov];[v0][ov]overlay=0:0:format=auto,format=yuv420p[v]")
    r = subprocess.run([ffmpeg(), "-y", "-ss", f"{max(0, t0):.3f}", "-i",
                        str(bg), "-loop", "1", "-t", f"{d_:.3f}", "-i",
                        str(png), "-filter_complex", vf, "-map", "[v]", "-t",
                        f"{d_:.3f}", "-r", str(FPS), "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "20", "-pix_fmt",
                        "yuv420p", "-an", str(seg)], capture_output=True,
                       text=True)
    if r.returncode:
        raise RuntimeError(f"فصل {name} فشل: " + (r.stderr or "")[-300:])
    return seg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surah", type=int, required=True)
    ap.add_argument("--ayah", type=int, required=True)
    ap.add_argument("--ayah-to", type=int, default=None)
    ap.add_argument("--reciter", default="husary")
    ap.add_argument("--out", default="/tmp/noor.mp4")
    ap.add_argument("--work", default="/tmp/noor_work")
    a = ap.parse_args()
    res = render({"surah": a.surah, "ayah": a.ayah, "ayah_to": a.ayah_to,
                  "reciter": a.reciter},
                 Path(a.work))
    subprocess.run(["cp", str(res["video"]), a.out], check=True)
    print(json.dumps({k: str(v) for k, v in res.items() if k != "text"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
