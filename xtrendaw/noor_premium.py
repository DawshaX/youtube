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
CACHE = settings.STATE / "noor_cache"
FONT_Q = settings.FONTS / "AmiriQuran-Regular.ttf"     # الخط القرآني
FONT_UI = settings.FONTS / "Tajawal-Regular.ttf"
FONT_UI_B = settings.FONTS / "Tajawal-Bold.ttf"
UA = {"User-Agent": "NoorShorts/1.0 (free Islamic shorts; educational)"}
APIQ = "https://api.alquran.cloud/v1"
CDN = "https://cdn.islamic.network/quran/audio"

# قرّاء هادئون مؤثرون (تُختار حكمة كل حلقة)
RECITERS = {
    "husary":   ("ar.husary", 128, "محمود خليل الحصري"),
    "minshawi": ("ar.minshawi", 128, "محمد صديق المنشاوي"),
    "ghamdi":   ("ar.saadalghamdi", 64, "سعد الغامدي"),
    "shatri":   ("ar.shaatree", 128, "أبو بكر الشاطري"),
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


def recitation(surah: int, ayah: int, reciter: str, workdir: Path,
               globals_: list[int] | None = None) -> Path:
    """تلاوة حقيقية لقارئ معتمد (آية أو نطاق) → WAV واحد."""
    slug, kbps, _name = RECITERS[reciter]
    CACHE.mkdir(parents=True, exist_ok=True)
    if not globals_:
        a = ayah_text(surah, ayah)
        globals_ = a["globals"]
    wavs: list[Path] = []
    for num in globals_:
        mp3 = CACHE / f"{slug}-{num}.mp3"
        if not mp3.exists():
            last = ""
            for kb in dict.fromkeys((kbps, 128, 64)):
                try:
                    url = f"{CDN}/{kb}/{slug}/{num}.mp3"
                    with urllib.request.urlopen(
                            urllib.request.Request(url, headers=UA),
                            timeout=120) as r:
                        body = r.read()
                    if len(body) > 1500:
                        mp3.write_bytes(body)
                        break
                    last = f"{len(body)} بايت"
                except Exception as exc:      # noqa: BLE001
                    last = f"{type(exc).__name__}"
            else:
                raise RuntimeError(f"تلاوة {slug}:{num} مش متاحة ({last})")
        w = workdir / f"rec_{num}.wav"
        subprocess.run([ffmpeg(), "-y", "-i", str(mp3), "-ar", "44100",
                        "-ac", "2", "-c:a", "pcm_s16le", str(w)],
                       capture_output=True, check=True)
        wavs.append(w)
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


def overlay(lines: list[str], out: Path, *, size: int = 74, y: float = 0.42,
            color=(255, 253, 246, 255), font_path: Path | None = None,
            halo: int = 26, max_w: int | None = None, spacing: float = 1.6,
            tag: str = "") -> Path:
    """نص عربي على شاشة شفافة: هالة ضوء خلف النص (تقرأ على أي خلفية).

    halo = هالة سوداء ناعمة حول الحروف — نفس أسلوب التايتلات السينمائية.
    """
    W_ = W if max_w is None else max_w
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    from . import textrender as _tr
    kw = {"layout_engine": ImageFont.Layout.RAQM} if _tr.HAS_RAQM else {}
    font = ImageFont.truetype(str(font_path or FONT_Q), size, **kw)
    _dir = {"direction": "rtl", "language": "ar"} if _tr.HAS_RAQM else {}
    wrapped: list[str] = []
    for raw in lines:
        wrapped += _lines(raw, font, W_)
    line_h = int(size * spacing)
    total = line_h * len(wrapped)
    y0 = int(H * y) - total // 2
    # ── طبقة تعتيم متدرّجة (scrim) ورا النص: أي خلفية — فاتحة أو غامقة —
    #    والتلاوة تفضل مقروءة. دي الفرق بين «نص واضح» و«نص مبحوح».
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    pad = int(size * 1.6)
    top = max(0, y0 - pad)
    bot = min(H, y0 + total + pad)
    span = max(1, bot - top)
    for yy in range(top, bot):
        dtop = (yy - top) / span
        # منحنى ناعم (جيب) من 0 → 1 → 0: بلا حَواف حادة = إحساس سينمائي
        a = int(135 * (math.sin(math.pi * dtop) ** 1.15))
        sd.line([(0, yy), (W, yy)], fill=(4, 6, 12, a))
    img = Image.alpha_composite(img, scrim)
    # طبقة الهالة (ضباب + تمدّد) خلف النص
    halo_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo_img)
    yy = y0
    for ln in wrapped:
        tw = hd.textlength(_shaped(ln), font=font, **_dir)
        hd.text(((W - tw) // 2, yy), _shaped(ln), font=font,
                fill=(0, 0, 0, 190), **_dir)
        yy += line_h
    halo_img = halo_img.filter(ImageFilter.GaussianBlur(halo))
    img = Image.alpha_composite(img, halo_img)
    d = ImageDraw.Draw(img)
    yy = y0
    for ln in wrapped:
        tw = d.textlength(_shaped(ln), font=font, **_dir)
        d.text(((W - tw) // 2, yy), _shaped(ln), font=font, fill=color, **_dir)
        yy += line_h
    if tag:
        f2 = ImageFont.truetype(str(FONT_UI), 40, **kw)
        tw = d.textlength(_shaped(tag), font=f2, **_dir)
        d.text(((W - tw) // 2, y0 + total + 42), _shaped(tag), font=f2,
               fill=(255, 214, 140, 235), **_dir)
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
    if not ok:
        raise RuntimeError(f"مفيش مشهد لـ«{q}»")
    return _still_clip(base, max(2.0, seconds), workdir / f"s{idx:02d}.mp4",
                       zoom_in=(idx % 2 == 0)), "صورة متحركة"


def grade_and_concat(clips: list[Path], out: Path) -> Path:
    """تدريج لوني موحّد + فينييت + حبيبات خفيفة + دمج في مسار واحد."""
    lst = out.parent / "concat.txt"
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips),
                   encoding="utf-8")
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"setsar=1,fps={FPS},{GRADE},noise=alls=5:allf=t+u,format=yuv420p")
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-vf", vf, "-an", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "20", str(out)],
                   capture_output=True, check=True)
    return out


# ─────────────────────────── التركيب ───────────────────────────

def render(spec: dict, workdir: Path) -> dict:
    """يبني شورت كامل: تلاوة + آية سطرًا سطرًا + المعنى + الخاتمة.

    spec: {surah, ayah, reciter, scenes[], brand, hook_tag, meaning_lines}
    """
    workdir.mkdir(parents=True, exist_ok=True)
    surah, ay = int(spec["surah"]), int(spec["ayah"])
    ay_to = int(spec.get("ayah_to") or ay)
    reciter = spec.get("reciter") or "husary"
    a = ayah_text(surah, ay, ay_to)
    taf = ayah_tafsir(surah, ay_to)
    rec = recitation(surah, ay, reciter, workdir, globals_=a["globals"])
    rec_d = dur_of(rec)
    if rec_d <= 1:
        raise RuntimeError("مدة التلاوة صفر")

    lead, gap, meaning_d, outro_d = 0.8, 1.4, float(spec.get("meaning_d", 7.0)), 2.6
    total = lead + rec_d + gap + meaning_d + outro_d

    # مشاهد مطابقة للمعنى (٣ مشاهد على الأقل، وكل مشهد يخدم جزء من التلاوة)
    scene_qs = spec.get("scenes") or [
        "night sky milky way stars", "calm sea waves sunset",
        "clouds sunrise mountains", "mosque architecture night"]
    n_sc = max(3, min(len(scene_qs), int(spec.get("scenes_n", 4))))
    body = total - outro_d
    per = body / n_sc
    clips, srcs = [], []
    for i in range(n_sc):
        c, src = scene_clip(scene_qs[i % len(scene_qs)], per + 0.6,
                            workdir, f"{surah}:{ay}:{i}", i)
        clips.append(c)
        srcs.append(src)
    bg = grade_and_concat(clips, workdir / "bg.mp4")

    # نص الآية: يظهر سطر سطر مع التلاوة (بلا ادّعاء توقيت كلمة بكلمة)
    cues: list[tuple[float, float, Path]] = []
    words = a["text"].split()
    groups = [words[i:i + 4] for i in range(0, len(words), 4)] or [words]
    reveal_t0 = lead + 0.15
    for k in range(1, len(groups) + 1):
        t0 = reveal_t0 + (rec_d * (k - 1) / len(groups))
        t1 = reveal_t0 + (rec_d * k / len(groups))
        png = overlay([" ".join(" ".join(g) for g in groups[:k])],
                      workdir / f"a{k}.png", size=76, y=0.40,
                      tag=("﴿ " + a["surah"] + " — " + str(a["number"]) + " ﴾")
                      if k == len(groups) else "")
        cues.append((t0, t1, png))
    # كارت المعنى (مقصود ومختصر — يفهمه أي مشاهد)
    mean_txt = spec.get("meaning") or taf
    mean_txt = re.sub(r"\s+", " ", mean_txt)
    if len(mean_txt) > 190:
        mean_txt = mean_txt[:187].rsplit(" ", 1)[0] + "…"
    mp = overlay([mean_txt], workdir / "mean.png", size=58, y=0.46,
                 color=(255, 250, 238, 255), font_path=FONT_UI,
                 halo=22, spacing=1.65, tag="المعنى")
    cues.append((lead + rec_d + gap, lead + rec_d + gap + meaning_d, mp))
    # خاتمة هادئة
    op = overlay([spec.get("outro") or "لا تنسَ ذكر الله 🤍"],
                 workdir / "outro.png", size=64, y=0.47,
                 color=(255, 236, 200, 255), font_path=FONT_UI_B, halo=24,
                 tag=spec.get("brand", ""))
    cues.append((lead + rec_d + gap + meaning_d, total, op))

    # ── التركيب: كل «فصل» = شريحة من نفس الخلفية + نص واحد فوقها
    # (كده النص بيتغيّر سطر سطر والخلفية مستمرة بلا قطع — وكل فصل overlay واحد
    #  بس، فالسّرعة معقولة بدل ٦ طبقات في نفس اللحظة.)
    segs: list[Path] = []
    for i, (t0, t1, png) in enumerate(cues):
        seg = workdir / f"seg{i:02d}.mp4"
        d_ = max(0.5, t1 - t0)
        fades = "fade=t=in:st=0:d=0.45:alpha=1"
        if i == len(cues) - 1:
            fades += (f",fade=t=out:st={max(0.1, d_ - 0.8):.2f}:d=0.8:alpha=1")
        vf = ("[0:v]setsar=1[v0];[1:v]format=rgba," + fades +
              "[ov];[v0][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        r = subprocess.run(
            [ffmpeg(), "-y", "-ss", f"{t0:.3f}", "-i", str(bg), "-loop", "1",
             "-t", f"{d_:.3f}", "-i", str(png), "-filter_complex", vf,
             "-map", "[v]", "-t", f"{d_:.3f}", "-r", str(FPS),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", str(seg)],
            capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"ffmpeg فصل {i} فشل: " + (r.stderr or "")[-400:])
        segs.append(seg)
    lst = workdir / "segs.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs),
                   encoding="utf-8")
    silent = workdir / "silent.mp4"
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-c", "copy", str(silent)],
                   capture_output=True, check=True)
    # الصوت: تلاوة (بلا موسيقى) بتوقيت البداية + ماسترينج -15 LUFS
    cmd = [ffmpeg(), "-y", "-i", str(silent), "-i", str(rec),
           "-filter_complex",
           f"[1:a]adelay={int(lead*1000)}|{int(lead*1000)},apad,"
           f"atrim=0:{total:.2f},loudnorm=I=-15:TP=-1.5:LRA=9[a]",
           "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", str(workdir / "noor.mp4")]
    rm = subprocess.run(cmd, capture_output=True, text=True)
    if rm.returncode:
        raise RuntimeError("دمج الصوت فشل: " + (rm.stderr or "")[-400:])
    out = workdir / "noor.mp4"
    cover = workdir / "cover.png"
    subprocess.run([ffmpeg(), "-y", "-ss", f"{lead + rec_d * 0.6:.2f}", "-i",
                    str(out), "-frames:v", "1", str(cover)],
                   capture_output=True, check=True)
    return {"video": out, "cover": cover, "duration": total,
            "reciter": RECITERS[reciter][2], "surah": a["surah"],
            "ayah": a["number"], "text": a["text"], "tafsir": taf,
            "sources": srcs, "rec_duration": rec_d}


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
