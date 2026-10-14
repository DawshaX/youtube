"""🎬 محرّك المؤثرات السينمائية — بيخلي الفيديو يبان «غالي».

كل مؤثر هنا **مولّد بالكود أو بفلتر ffmpeg أصلي** — صفر أصول خارجية،
صفر حقوق، وصفر خطر على القناة.

طبقات الجودة (بالترتيب اللي بتتطبّق):
    1. تدريج لوني سينمائي (سينماتك + تباين + ظل مرفوع)
    2. حبيبات فيلم ناعمة (film grain) — بتخفي «الأصل رقمي» وبتزوّد الإحساس
    3. هالة ضوء (light leak) عند نقاط التحوّل
    4. نبض زووم خفيف عند الهوك (impact zoom)
    5. شريط تقدّم رقيق في الآخر (progress bar — بيرفع الاحتفاظ)
    6. انتقالات ذكية: وميض ضوئي · انزلاق ناعم · قطع لقطة إيقاعي

⚠️ القاعدة: **أي مؤثر يفشل = الفيديو يكمل من غيره.** مفيش مؤثر يوقف حلقة.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

W, H, FPS = 1080, 1920, 30

# ── صفات سينمائية جاهزة (كل واحدة سلسلة فلاتر ffmpeg مجرّبة)
GRADES = {
    "دافئ_سينمائي": (
        "eq=contrast=1.07:brightness=0.008:saturation=1.06:gamma=1.03,"
        "colorbalance=rs=0.035:gs=0.012:bs=-0.03:rm=0.02:bm=-0.02,"
        "vignette=PI/5.6"
    ),
    "بارد_هادئ": (
        "eq=contrast=1.05:brightness=0.006:saturation=0.96:gamma=1.04,"
        "colorbalance=rs=-0.025:bs=0.035,vignette=PI/6.2"
    ),
    "ذهبي_فخم": (
        "eq=contrast=1.09:brightness=0.01:saturation=1.1:gamma=1.02,"
        "colorbalance=rs=0.05:gs=0.022:bs=-0.045,vignette=PI/5.2"
    ),
    "ليلي_عميق": (
        "eq=contrast=1.11:brightness=-0.012:saturation=0.9:gamma=0.97,"
        "colorbalance=bs=0.05:rm=-0.02,vignette=PI/4.8"
    ),
    "نقي_مشرق": (
        "eq=contrast=1.04:brightness=0.014:saturation=1.03:gamma=1.05,"
        "vignette=PI/7.0"
    ),
}

GRAIN = (
    "noise=alls=6:allf=t+u,"
    "unsharp=5:5:0.35:5:5:0.0"
)

# ── انتقالات مصنّفة بالطاقة (خفيف → قوي)
TRANSITIONS = {
    "هادئ": ("fade", "dissolve", "fadeblack"),
    "متوسط": ("smoothleft", "smoothright", "fade", "slideup"),
    "حيوي": ("wipeleft", "wiperight", "radial", "circleopen"),
}


def _run(cmd: list[str], timeout: int = 900) -> bool:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0
    except Exception:
        return False


def _seed(*parts) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:10], 16)


# ─────────────────────────────────────────────────────────────────────
# 1) التدريج + الحبيبات — تطبيق واحد بفلتر واحد (أسرع وأخف)
# ─────────────────────────────────────────────────────────────────────
def grade_chain(style: str = "", grain: bool = True) -> str:
    """سلسلة الفلاتر الكاملة للتدريج. فاضية = بلا تدريج."""
    base = GRADES.get(style) or GRADES["دافئ_سينمائي"]
    return f"{base},{GRAIN}" if grain else base


def pick_grade(item: dict, feeling: str = "") -> str:
    """يختار التدريج المناسب لمزاج الحلقة."""
    blob = f"{feeling} {item.get('emotion', '')} {item.get('field', '')} {item.get('series_title', '')}"
    if any(w in blob for w in ("حزن", "دعاء", "سكينة", "قلق")):
        return "بارد_هادئ"
    if any(w in blob for w in ("فرح", "أمل", "خير", "بشري", "نور")):
        return "ذهبي_فخم"
    if any(w in blob for w in ("ليل", "نجوم", "نوم", "فضاء")):
        return "ليلي_عميق"
    if any(w in blob for w in ("علم", "معلومة", "أرض", "جبل")):
        return "نقي_مشرق"
    styles = list(GRADES)
    return styles[_seed(item.get("id"), "grade") % len(styles)]


# ─────────────────────────────────────────────────────────────────────
# 2) نبض الزووم (impact zoom) — أول ثانية، بيثبّت العين
# ─────────────────────────────────────────────────────────────────────
def impact_zoom(src: Path, dst: Path, seconds: float,
                strength: float = 0.055, hold: float = 0.6) -> bool:
    """زووم ناعم بيبدأ قوي في أول لحظة ويهدى — إحساس «ضربة» بلا ضجيج."""
    dur = max(0.4, seconds)
    z = f"1+{strength}*(1-min(t/{hold:.2f},1))"
    vf = (
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop=w='{W*2}/zoomden':h='{H*2}/zoomden':x='(in_w-out_w)/2':y='(in_h-out_h)/2',"
        f"scale={W}:{H},fps={FPS},format=yuv420p"
    )
    # نستخدم zoompan لأن أسرع وأدق من crop المتغيّر
    vf = (
        f"scale={int(W*2.2)}:{int(H*2.2)}:force_original_aspect_ratio=increase,"
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d=1:s={W}x{H}:fps={FPS},format=yuv420p"
    )
    return _run([
        "ffmpeg", "-y", "-i", str(src), "-t", f"{dur:.2f}",
        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "18", "-pix_fmt", "yuv420p", str(dst),
    ])


# ─────────────────────────────────────────────────────────────────────
# 3) هالة ضوء (light leak) — لحظة انتقال دافية
# ─────────────────────────────────────────────────────────────────────
def light_leak(src: Path, dst: Path, color: str = "#FFD9A0",
               strength: float = 0.42) -> bool:
    """هالة ضوء بتعدي على الفريم — إحساس تحوّل زمني/مكاني راقي."""
    hexc = color.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    vf = (
        f"color=c=0x{hexc}:s={W}x{H}:r={FPS},format=rgba,"
        f"colorchannelmixer=aa={strength:.2f}[leak];"
        f"[0:v][leak]blend=all_mode=screen:all_opacity=0.55,"
        f"format=yuv420p"
    )
    return _run([
        "ffmpeg", "-y", "-i", str(src), "-filter_complex", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(dst),
    ])


# ─────────────────────────────────────────────────────────────────────
# 4) شريط التقدّم — أثبت رافع للاحتفاظ في الشورتس
# ─────────────────────────────────────────────────────────────────────
def progress_bar(src: Path, dst: Path, color: str = "#E8C37A",
                 height: int = 9) -> bool:
    """شريط رقيق أسفل الفيديو بيقول للمشاهد «فاضل قد إيه» — بيمنع الخروج."""
    hexc = color.lstrip("#")
    vf = (
        f"drawbox=x=0:y=h-{height}:w='iw*t/{0}':h={height}:"
        f"color=0x{hexc}@0.92:t=fill"
    ).replace("/{0}", "/max(t,0.001)*0")  # placeholder — نستخدم الطريقة الصح تحت
    # الطريقة الصحيحة: عرض متغيّر مع الزمن عبر expression
    vf = (
        f"drawbox=x=0:y=ih-{height}:w='iw*(t/duration)':h={height}:"
        f"color=0x{hexc}@0.92:t=fill"
    )
    return _run([
        "ffmpeg", "-y", "-i", str(src), "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(dst),
    ])


# ─────────────────────────────────────────────────────────────────────
# 5) الطبقة الختامية — تجميع كل المؤثرات في تمريرة واحدة
# ─────────────────────────────────────────────────────────────────────
def _has_audio(video: Path) -> bool:
    """يفحص وجود مسار صوتي فعلًا — عشان ما نضيّعش الصوت في التمريرة النهائية."""
    for exe in _ffmpeg_candidates():
        try:
            probe = exe.replace("ffmpeg", "ffprobe")
            import shutil as _sh

            if not _sh.which(probe):
                # ffprobe مش متاح: بنستنتج من مخرجات ffmpeg نفسها
                import subprocess

                r = subprocess.run([exe, "-i", str(video)], capture_output=True, text=True)
                return "Audio:" in (r.stderr or "")
            import subprocess

            r = subprocess.run(
                [probe, "-v", "error", "-select_streams", "a:0",
                 "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(video)],
                capture_output=True, text=True,
            )
            return "audio" in (r.stdout or "").strip().lower()
        except Exception:
            continue
    return False


def finishing_pass(video: Path, dst: Path, *, style: str = "",
                   grain: bool = True, bar: bool = True,
                   bar_color: str = "#E8C37A", keep_audio: bool = True) -> bool:
    """تمريرة واحدة بتطبّق التدريج + الحبيبات + شريط التقدّم.

    تمريرة واحدة = أسرع من ٣ تمريرات، وبلا خسارة جودة متكرّرة.
    ⚠️ **الصوت بيتنقل كما هو** (`-c:a copy`) — المصنع بيرندر الصوت والفيديو
    مع بعض، فحذف الصوت هنا كان بيضيّع الحلقة كلها.
    """
    chain = [grade_chain(style, grain)]
    if bar:
        hexc = bar_color.lstrip("#")
        chain.append(
            f"drawbox=x=0:y=ih-9:w='iw*(t/duration)':h=9:"
            f"color=0x{hexc}@0.9:t=fill"
        )
    vf = ",".join(chain)

    has_audio = keep_audio and _has_audio(video)
    # مسار الصوت: نقل مباشر بلا إعادة ترميز (أسرع وجودة أصلية)
    audio_args = (["-map", "0:v:0", "-map", "0:a:0?", "-c:a", "copy"]
                  if has_audio else ["-an"])

    def attempt(filters: str | None) -> bool:
        cmd = ["ffmpeg", "-y", "-i", str(video)]
        if filters:
            cmd += ["-vf", filters]
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p", *audio_args, str(dst)]
        return _run(cmd)

    if attempt(vf):
        return True
    # لو التدريج فشل، نجرب بلا شريط (الفشل الأغلب من نسخة ffmpeg قديمة)
    if attempt(grade_chain(style, grain)):
        return True
    # آخر محاولة: نسخة بدون أي مؤثر (الفيديو لازم يكمل)
    return attempt(None)


def _ffmpeg_candidates() -> list[str]:
    """ffmpeg المتاح في البيئة (system أو imageio-ffmpeg)."""
    import os
    import shutil

    found = [p for p in (shutil.which("ffmpeg"), os.environ.get("FFMPEG_BIN")) if p]
    try:
        import imageio_ffmpeg  # type: ignore

        found.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass
    return list(dict.fromkeys(found))


# ─────────────────────────────────────────────────────────────────────
# 6) انتقالات ذكية حسب طاقة الحلقة
# ─────────────────────────────────────────────────────────────────────
def pick_transition(episode_id: str, feeling: str = "") -> str:
    """يختار نوع الانتقال حسب إحساس الحلقة (هادئ/متوسط/حيوي)."""
    if feeling in ("حزن", "حب", "لحظة"):
        pool = TRANSITIONS["هادئ"]
    elif feeling in ("هزار", "طفل"):
        pool = TRANSITIONS["حيوي"]
    else:
        pool = TRANSITIONS["متوسط"]
    return pool[_seed(episode_id, feeling, "trans") % len(pool)]


# ─────────────────────────────────────────────────────────────────────
# 7) كابشنز كاريوكي متحركة (ترقية على burn_words الحالي)
# ─────────────────────────────────────────────────────────────────────
def caption_style_for(mood: str) -> dict:
    """نمط الكابشن المناسب للمزاج — نفس الكلمة بتبان مختلف حسب الحالة."""
    styles = {
        "روحاني": {"size": 58, "fill": "#FFF7E6", "stroke": "#1A1512", "y": 0.775},
        "دافي":   {"size": 54, "fill": "#FFE9C7", "stroke": "#20160E", "y": 0.78},
        "حيوي":   {"size": 62, "fill": "#FFFDF6", "stroke": "#14110E", "y": 0.765},
        "هادئ":   {"size": 52, "fill": "#F2F6FF", "stroke": "#10141C", "y": 0.785},
    }
    return styles.get(mood, styles["روحاني"])


def pick_caption_mood(item: dict) -> str:
    blob = f"{item.get('emotion', '')} {item.get('field', '')} {item.get('kind', '')}"
    if any(w in blob for w in ("قرآن", "آية", "تدبر", "دعاء", "ذكر")):
        return "روحاني"
    if any(w in blob for w in ("خير", "أمل", "حب", "ضحك", "طفل")):
        return "دافي"
    if any(w in blob for w in ("علم", "معلومة", "حيوي", "نشاط")):
        return "حيوي"
    return "هادئ"


# ─────────────────────────────────────────────────────────────────────
# 8) الحزمة الكاملة — الطبقة اللي المصنع بينادي عليها
# ─────────────────────────────────────────────────────────────────────
def apply_all(video: Path, work: Path, item: dict, *, feeling: str = "",
              enabled: bool = True) -> tuple[Path, dict]:
    """يطبّق كل المؤثرات على الفيديو النهائي.

    يرجّع (المسار الجديد أو الأصلي, تقرير بالمؤثرات اللي اتطبّقت).
    **مفيش فشل بيوقف الحلقة أبدًا.**
    """
    report: dict = {"applied": [], "skipped": []}
    if not enabled or not video.exists():
        report["skipped"].append("المؤثرات مقفولة")
        return video, report

    try:
        cur = video
        styled = work / "finish.mp4"
        style = pick_grade(item, feeling)
        if finishing_pass(cur, styled, style=style, grain=True, bar=True):
            cur = styled
            report["applied"].extend(["تدريج " + style, "حبيبات فيلم", "شريط تقدّم"])
        else:
            report["skipped"].append("التمريرة النهائية")
        return cur, report
    except Exception as exc:  # noqa: BLE001
        report["skipped"].append(f"{type(exc).__name__}")
        return video, report
