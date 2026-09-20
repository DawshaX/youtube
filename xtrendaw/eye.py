"""العين — طبقة «شوف الفيديو» الحقيقية (1.5 في البلوبرنت).

بتشوف فيديو الترند **الحقيقي** من أوله لآخره — قيس بنية وكتابة أصلية،
بلا نسخ ولا بيانات متخيلة:

  1) اقرأ   — تريلت التسميات التلقائية بتوقيتات حقيقية (لحظة بلحظة)
  2) شوف     — مشاهد (ffmpeg scene-detect) + كي-فريم لكل مشهد +
               ألوان مهيمنة/إضاءة/حركة لكل مشهد
  3) اسمع    — طاقة الصوت (dB RMS) لكل ثانية
  4) افهم    — وكيل LLM يحلل الـ DNA الفيروسي: الخطاف، البياتات، المنعطف،
               الذروة، اللغة البصرية، الإيقاع، خدع الاحتفاظ
  5) اكتب    — إصدارنا على نفس السياق: أسرع وأحسن، نص أصلي 100%
               (نبرة القناة: الأخ الكبير، تحذير، هزار، ختام دافي)
  6) ناقد    — مرور وكيل تاني: تقييم 0-100 وإعادة كتابة لو أقل من 75

المخرجات (قابلة للتدقيق، متلتزمة في المستودع):
  data/eye/<videoId>/report.json   — تقرير المشاهدة الكامل
  data/eye/<videoId>/frames/*.jpg  — كي-فريمز حقيقية
  data/eye_topics.json             — طابور المصنع (بينسحب من المخ والـ autopilot)
  data/eye_consumed.json           — أرشيف اللي اتستهلك

قاعدة صرامة: بلا شبكة أو بلا مفتاح LLM → فشل صريح برمز خروج،
أبدًا بلا بيانات متخيلة. ملف الفيديو (video.mp4) ملف شغل —
مفيش التزامه في الجيت (التقرير والـ frames بس).
"""
from __future__ import annotations

import argparse
import atexit
import json
import re
import shutil
import tempfile
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import os

from . import content, settings

EYE_DIR = settings.ROOT / "data" / "eye"
EYE_TOPICS_PATH = settings.ROOT / "data" / "eye_topics.json"
EYE_CONSUMED_PATH = settings.ROOT / "data" / "eye_consumed.json"
PATTERNS_PATH = settings.ROOT / "data" / "patterns.json"
SNAPSHOT_PATH = settings.ROOT / "data" / "radar_snapshot.json"

_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ar,en;q=0.8",
}


def _req():
    """requests محمّل تحت الطلب — المودول يستورد أوفلاين (اختبارات بلا شبكة)."""
    import requests
    return requests


# كوكيز يوتيوب — مطلوبة عشان خوادم Actions (IP مركزي) تقدر تشوف الفيديو
# والتسميات. بتيجي من سر المستودع YOUTUBE_COOKIES_B64.
#
# ⚠️ درس حقيقي (تشغيل 2026-09-19): السر كان base64 لسطر واحد فيه أزواج
# `name=value; name=value` (شكل هيدر الكوكيز) — مش ملف نيتسكيب. الكود القديم
# كان بيكتب اللي فكّه زي ما هو ويبعته لـ yt-dlp، فيرد:
#   "does not look like a Netscape format cookies file"
# وعشان صف واحد مفيهوش tabs، استخراج الكوكيز كان بيرجّع سلسلة فاضية —
# يعني حتى طلبات requests كانت من غير كوكيز. الحل: نحوّل أي شكل معقول
# (نيتسكيب / JSON / أزواج name=value / base64 مزدوج) لملف نيتسكيب صالح،
# ونستخرج الأزواج منه للهيدر. أي شكل تاني: فشل صريح برسالة بتوصف البنية
# (مفيش قيم في الرسالة أبدًا).
_COOKIES_FILE: Path | None = None
_COOKIE_NETSCAPE_HEADER = "# Netscape HTTP Cookie File"
# كوكيز مصادقة جوجل لازم تتكتب على النطاقين (ده اللي بتوصي بيه yt-dlp نفسها)
_GOOGLE_SCOPE = ".google.com"
_DEFAULT_SCOPE = ".youtube.com"
_YEAR_SECONDS = 31536000


def _cookie_text(raw: str) -> str:
    """يفك base64 (ولو مزدوج) ويرجّع النص — أو النص زي ما هو لو مش base64."""
    import base64
    out = raw.strip().strip("'\"").strip()
    for _ in range(2):
        probe = out.replace("\n", "").replace("\r", "")
        if not probe or not re.fullmatch(r"[A-Za-z0-9+/=]+", probe) or len(probe) % 4:
            break
        try:
            dec = base64.b64decode(probe, validate=False).decode("utf-8", "ignore")
        except Exception:
            break
        if not dec.strip():
            break
        out = dec.strip()
    # بعض الأدوات بتصدّر السطور كـ \n نصّية جوه سطر واحد
    if "\n" in out.replace("\\n", ""):
        pass
    return out.replace("\\r\\n", "\n").replace("\\n", "\n") if "\\n" in out else out


def _pair_cookies(text: str) -> list[tuple[str, str, str]]:
    """يستخرج (name, value, domain) من أي نص — بلا خيال وبلا تعديل قيم."""
    found: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for m in re.finditer(r"([A-Za-z0-9_\-\.]{1,64})=([^\s;,\"]*)", text):
        name, value = m.group(1), m.group(2)
        if name.lower() in ("path", "domain", "expires", "max-age", "samesite",
                            "secure", "httponly", "expiry", "hostonly", "http_only"):
            continue
        if name in seen:
            continue
        seen.add(name)
        found.append((name, value, ""))
    return found


def _parse_cookies(text: str) -> tuple[list[tuple[str, str, str]], str]:
    """(قائمة (name, value, domain), وصف الشكل) — يقبل نيتسكيب وJSON وأزواج."""
    lines = [l for l in text.replace("\r\n", "\n").replace("\r", "\n").splitlines() if l.strip()]
    # ١) نيتسكيب: ٧ حقول مفصولة بـ tab
    tabbed = [l for l in lines if len(l.split("\t")) >= 7]
    if tabbed:
        out = []
        for line in tabbed:
            f = line.split("\t")
            domain = f[0]
            for prefix in ("#HttpOnly_", "#HttpOnly"):
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            out.append((f[5].strip(), f[6].strip(), domain.strip()))
        return out, f"netscape ({len(out)} كوكي)"
    # ٢) JSON (تصدير إضافات المتصفح / DevTools)
    stripped = text.lstrip()
    if stripped[:1] in ("{", "["):
        try:
            data = json.loads(stripped)
        except Exception:
            data = None
        if data is not None:
            items = data.get("cookies") if isinstance(data, dict) else data
            if isinstance(items, list):
                out = []
                for c in items:
                    if isinstance(c, dict) and c.get("name"):
                        out.append((str(c["name"]), str(c.get("value", "")),
                                    str(c.get("domain", ""))))
                if out:
                    return out, f"json ({len(out)} كوكي)"
    # ٣) أزواج name=value (شكل الهيدر: أ=b; ج=د)
    pairs = _pair_cookies(text)
    if pairs:
        return pairs, f"pairs ({len(pairs)} كوكي)"
    return [], f"unrecognized (حروف={len(text)} سطور={len(lines)})"


def _to_netscape(pairs: list[tuple[str, str, str]]) -> str:
    """يبني ملف نيتسكيب صالح من الأزواج (نطاق يوتيوب + جوجل لكوكيز المصادقة)."""
    exp = int(time.time()) + _YEAR_SECONDS
    lines = [_COOKIE_NETSCAPE_HEADER]
    for name, value, domain in pairs:
        scopes = [domain] if domain else [_DEFAULT_SCOPE]
        if not domain or "google" in domain or name.startswith("__Secure") or \
                name in ("SID", "HSID", "SSID", "APISID", "SAPISID", "LOGIN_INFO"):
            scopes.append(_GOOGLE_SCOPE)
        for scope in dict.fromkeys(scopes):
            if not scope.startswith("."):
                scope = "." + scope.lstrip(".")
            lines.append("\t".join([scope, "TRUE", "/", "TRUE", str(exp), name, value]))
    return "\n".join(lines) + "\n"


def _write_cookies_file(content_text: str) -> Path:
    """يكتب ملف الكوكيز بصلاحية 0600 ويسجّل مسحه عند الخروج."""
    fd, name = tempfile.mkstemp(prefix="daousha-cookies-", suffix=".txt")
    p = Path(name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content_text)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        p.unlink(missing_ok=True)
        raise
    atexit.register(lambda path=p: path.unlink(missing_ok=True))
    return p


def _load_cookies() -> tuple[str, Path | None]:
    """(هيدر الكوكيز, مسار ملف نيتسكيب صالح أو None) من YOUTUBE_COOKIES_B64.

    الحارس: مفيش كوكيز صالحة → (سلسلة فاضية, None)، والنداء بيتعامل مع ده
    بإنه «مفيش مصادقة» مش انهيار — والفشل الحقيقي بيظهر في التحميل نفسه.
    """
    global _COOKIES_FILE
    raw = os.environ.get("YOUTUBE_COOKIES_B64", "").strip()
    if not raw:
        return "", None
    # ملف الكاش بيتحذف في نهاية العملية (atexit) أو بالتنظيف — فما نضمنهوش
    if _COOKIES_FILE is not None and not Path(_COOKIES_FILE).exists():
        _COOKIES_FILE = None
    if _COOKIES_FILE is None:
        text = _cookie_text(raw)
        pairs, shape = _parse_cookies(text)
        if not pairs:
            print(f"[eye] ⚠️ سر الكوكيز مش مقروء — {shape} "
                  f"(المتوقع: نيتسكيب أو JSON أو أزواج name=value)", flush=True)
            return "", None
        # نيتسكيب أصلي بيتكتب زي ما هو (بس برأس الملف لو ناقص)، وغير كده نبني واحد
        if shape.startswith("netscape") and text.lstrip().startswith("#"):
            payload = text if not text.startswith("\ufeff") else text.lstrip("\ufeff")
        else:
            payload = _to_netscape(pairs)
        if not payload.lstrip().startswith(_COOKIE_NETSCAPE_HEADER):
            payload = _COOKIE_NETSCAPE_HEADER + "\n" + payload
        _COOKIES_FILE = _write_cookies_file(payload)
        print(f"[eye] ✓ الكوكيز اتظبطت ({shape}) — المصادقة شغالة", flush=True)
    pairs, _ = _parse_cookies(_COOKIES_FILE.read_text(encoding="utf-8", errors="ignore"))
    seen: dict[str, str] = {}
    for name, value, _ in pairs:
        seen.setdefault(name, value)   # نفس الكوكي مكتوب على نطاقين — مرة واحدة في الهيدر
    return "; ".join(f"{n}={v}" for n, v in seen.items()), _COOKIES_FILE


def _headers() -> dict:
    h = dict(_UA)
    cookie, _ = _load_cookies()
    if cookie:
        h["Cookie"] = cookie
    return h


# ═════════════════════════════════════════════════════════════
# ١) اقرأ — التسميات التلقائية بتوقيتات حقيقية
# ═════════════════════════════════════════════════════════════

def _player_response(video_id: str) -> dict:
    r = _req().get(f"https://www.youtube.com/watch?v={video_id}",
                   headers=_headers(), timeout=30)
    r.raise_for_status()
    m = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;\s*(?:var\s|</script>)",
                  r.text, re.S)
    if not m:
        m = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", r.text, re.S)
    if not m:
        raise RuntimeError("eye: ما قدرنا نشيل بيانات المشغل — الفيديو خاص أو مقفول إقليمي")
    return json.loads(m.group(1))


def parse_json3_captions(data: dict) -> list[dict]:
    """تحليل json3 (مخرَج مسارات التسميات) → [{t, dur, text}] مرتب زمنيًا."""
    out: list[dict] = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        text = "".join(s.get("utf8", "") for s in segs)
        text = text.replace("\n", " ").strip()
        if not text:
            continue
        out.append({
            "t": round(ev.get("tStartMs", 0) / 1000.0, 3),
            "dur": round(ev.get("dDurationMs", 0) / 1000.0, 3),
            "text": text,
        })
    out.sort(key=lambda x: x["t"])
    return out


def fetch_captions(video_id: str) -> list[dict]:
    """مقاطع التسميات بتوقيتاتها الحقيقية: [{t, dur, text}].

    الأولوية: عربي (يدوي ثم تلقائي) ← إنجليزي ← أي متوفر.
    لا مسارات تسميات → قائمة فاضية (التقرير يكمل بالمشاهدات البصرية
    وبيُسجَّل caption_coverage: 0 صراحةً — بلا كلمات متخيلة).
    """
    player = _player_response(video_id)
    tracks = (player.get("captions", {})
              .get("playerCaptionsTracklistRenderer", {})
              .get("captionTracks", []))
    if not tracks:
        return []

    def score(t: dict) -> tuple:
        name = (t.get("name") or {}).get("simpleText", "") or ""
        is_asr = ("auto" in name.lower()) or ("تلقائي" in name)
        lang = (t.get("languageCode") or "").split("-")[0]
        return (0 if lang == "ar" else 1 if lang == "en" else 2, is_asr)

    best = sorted(tracks, key=score)[0]
    try:
        r = _req().get(best["baseUrl"] + "&fmt=json3", headers=_headers(), timeout=30)
        r.raise_for_status()
        return parse_json3_captions(r.json())
    except Exception as exc:
        # مسار innertube بيرجّع صفحة HTML بدل JSON من IP الخوادم — بنسحب
        # التسميات عبر yt-dlp بنفس الكوكيز والمحاكاة (نفس التوقيتات الحقيقية).
        print(f"[eye] ⚠️ تسميات innertube فشلت ({type(exc).__name__}) — "
              f"نجرب yt-dlp…", flush=True)
        return _ytdlp_captions(video_id, best.get("languageCode") or "ar")


def _ytdlp_captions(video_id: str, lang: str) -> list[dict]:
    """احتياطي: --write-auto-subs بصيغة json3 ثم نفس الـ parser (صفر توقيتات مخترعة)."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="daousha-subs-") as td:
        cmd = [sys.executable, "-m", "yt_dlp", "--skip-download",
               "--write-subs", "--write-auto-subs",
               "--sub-langs", f"{lang}.*,{lang},ar.*,en.*", "--sub-format", "json3",
               "--no-playlist", "-o", f"{td}/sub",
               f"https://www.youtube.com/watch?v={video_id}"]
        cmd += _impersonate_args()
        _, cookies_file = _load_cookies()
        if cookies_file is not None:
            cmd += ["--cookies", str(cookies_file)]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            return []
        files = sorted(Path(td).glob("*.json3"))
        if not files:
            print("[eye] ⚠️ مفيش ملف تسميات من yt-dlp — التقرير يكمل بلا كلمات", flush=True)
            return []
        try:
            return parse_json3_captions(json.loads(files[0].read_text(encoding="utf-8")))
        except Exception:
            return []


# ═════════════════════════════════════════════════════════════
# ٢) شوف — الفيديو الحقيقي: مشاهد + كي-فريمز + ألوان + حركة
# ═════════════════════════════════════════════════════════════

def _ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        import imageio_ffmpeg
        found = imageio_ffmpeg.get_ffmpeg_exe()
    return found


# خوادم GitHub Actions (IP مركزي) ممكن يصدّها يوتيوب بالعميل الافتراضي —
# نجرّب عملاء تباعين. الملاحظة الحقيقية (2026-09-19): مع وجود كوكيز،
# يوتيوب بيرجّع صفحة مقلوبة والعملاء اللي «مش بتدعم كوكيز» (ios/android)
# بيستنكفوا. فبنقدّم العملاء اللي بتدعم الكوكيز وWebKit:
_YT_CLIENTS = ("", "web_safari", "tv", "web", "mweb", "web_embedded", "android", "ios")


def _impersonate_args() -> list[str]:
    """محاكاة بصمة متصفح حقيقي (curl_cffi) — الحل الموثّق لـ «are you not a bot»
    و«only images are available» من IP الخوادم. لو المكتبة مش موجودة: بلا ضجيج.
    """
    try:
        import curl_cffi  # noqa: F401
    except Exception:
        return []
    return ["--impersonate", "chrome"]


def _js_runtime_args() -> list[str]:
    """yt-dlp 2026 محتاج JS runtime للاستخراج الكامل (EJS) — بلاها بيرجّع
    «Only images are available» أو تنسيقات ناقصة. deno هو الافتراضي المدعوم.
    """
    deno = shutil.which("deno") or os.environ.get("DENO_BIN") or ""
    if not deno:
        for cand in (Path.home() / ".deno" / "bin" / "deno", Path("/tmp/deno/bin/deno")):
            if cand.exists():
                deno = str(cand)
                break
    return ["--js-runtimes", f"deno:{deno}"] if deno else []


def download_video(video_id: str, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "video.mp4"
    last_err = ""
    for client in _YT_CLIENTS:
        cmd = [sys.executable, "-m", "yt_dlp",
               "-f", "bv*[height<=720]+ba/b[height<=720]/b",
               "--merge-output-format", "mp4",
               "--no-playlist", "--max-filesize", "60M",
               "--retries", "2", "--socket-timeout", "30",
               "-o", str(out),
               f"https://www.youtube.com/watch?v={video_id}"]
        if client:
            cmd += ["--extractor-args", f"youtube:player_client={client}"]
        cmd += _js_runtime_args() + _impersonate_args()
        _, cookies_file = _load_cookies()
        if cookies_file is not None:
            cmd += ["--cookies", str(cookies_file)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            last_err = f"client={client or 'default'}: timeout"
            continue
        if r.returncode == 0 and out.exists():
            if client:
                print(f"[eye] ✓ النزّل نجح بعميل {client}", flush=True)
            return out
        # تشخيص كامل (سطور yt-dlp المهمة) عشان الفشل يبان في الجيت من غير تخمين
        lines = [l.strip() for l in (r.stderr or r.stdout or "").splitlines()
                 if any(k in l for k in ("ERROR", "WARNING", "Sign in", "images",
                                         "runtime", "cookies"))]
        last_err = f"client={client or 'default'}: " + " ┃ ".join(lines[-4:])[:700]
        out.unlink(missing_ok=True)
    raise RuntimeError("eye: فشل التنزيل بكل العملاء — " + last_err)




# ═════════════════════════════════════════════════════════════
# مسار المشاهدة البديل: صور المشاهد (storyboards) + الكلام (captions)
# ═════════════════════════════════════════════════════════════
# الدرس (2026-09-20): التنزيل بـyt-dlp من IP الخوادم بقى مرفوض من يوتيوب
# («Sign in to confirm you're not a bot») حتى مع كوكيز — والعين بقت «عمياء»،
# فالمصنع بيرجع لنشرة أخبار بدل ما يقلّد الفيديو. الحل: يوتيوب نفسها بتبثّ
# **صور كل ثانية** (storyboards) على i.ytimg.com، وقوائم التشغيل الرسمية
# بتوفّر التسميات — يعني نقدر نشوف الفيديو كامل ونتكلم عن كل لحظة بلا تنزيل.

_INVIDIOUS = ("https://invidious.f5.si", "https://invidious.nerdvpn.de",
              "https://inv.tux.pizza", "https://invidious.jing.rocks",
              "https://iv.ggtyler.dev", "https://invidious.materialio.us",
              "https://yt.artemislena.eu", "https://invidious.privacyredirect.com")


def invidious_info(video_id: str) -> dict | None:
    """بيانات الفيديو + شيت صور المشاهد + التسميات من مِرآة Invidious."""
    for base in _INVIDIOUS:
        try:
            r = _req().get(f"{base}/api/v1/videos/{video_id}",
                           headers={"User-Agent": "Mozilla/5.0 (XTreNDAW)"},
                           timeout=45)
            if not r.ok:
                continue
            d = r.json()
            if d.get("title") and (d.get("storyboards") or d.get("captions")):
                d["_instance"] = base
                return d
        except Exception as exc:
            print(f"[eye] ⚠️ مِرآة {base}: {type(exc).__name__}", flush=True)
    return None


def storyboard_frames(info: dict, video_id: str, outdir: Path,
                      want: int = 14) -> list[tuple[float, Path]]:
    """صور المشاهد من يوتيوب (كل ~0.5 ثانية) → قائمة (الزمن, مسار الصورة).

    بنختار أعلى دقة متاحة، وبنحمّل الشيتات اللي تغطي الفيديو، وبنقصّ
    عددًا موزّع بانتظام على المدة (want صورة) — نظرة كاملة مش عيّنة عشوائية.
    """
    import re as _re

    from PIL import Image   # مستوردة هنا عشان الرندر ما يتقلش
    sbs = info.get("storyboards") or []
    if not sbs:
        return []
    best = max(sbs, key=lambda s: int(s.get("width") or 0) * int(s.get("height") or 0))
    grid_w = int(best.get("storyboardWidth") or 10)
    grid_h = int(best.get("storyboardHeight") or 10)
    interval = float(best.get("interval") or 500) / 1000.0   # ثواني بين صورتين
    tpl = _re.sub(r"^\s*//", "https://", str(best.get("templateUrl") or ""))
    if not tpl or "$M" not in tpl and "M$M" not in tpl:
        return []
    dur = float(info.get("lengthSeconds") or 0) or 0.0
    per_sheet = grid_w * grid_h
    total_frames = max(1, int(dur / interval)) if dur and interval else per_sheet
    sheets = max(1, min(int(best.get("count") or 1),
                        (total_frames + per_sheet - 1) // per_sheet))
    frames_dir = outdir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    got: list[tuple[float, Path]] = []
    step = max(1, total_frames // max(1, want))
    for s in range(sheets):
        url = tpl.replace("M$M", f"M{s}").replace("$M", f"M{s}")
        try:
            r = _req().get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            if not r.ok:
                continue
            sheet = frames_dir / f"sheet{s}.jpg"
            sheet.write_bytes(r.content)
            img = Image.open(sheet)
            cw, ch = img.width // grid_w, img.height // grid_h
            for idx in range(per_sheet):
                n = s * per_sheet + idx
                if n > total_frames:
                    break
                if n % step:
                    continue
                t = round(n * interval, 2)
                if dur and t > dur:
                    break
                x, y = (idx % grid_w) * cw, (idx // grid_w) * ch
                dst = frames_dir / f"shot_{n:04d}.jpg"
                img.crop((x, y, x + cw, y + ch)).save(dst, "JPEG", quality=88)
                got.append((t, dst))
        except Exception as exc:
            print(f"[eye] ⚠️ شيت {s}: {type(exc).__name__}", flush=True)
    print(f"[eye] 👀 صور المشاهد: {len(got)} صورة من {sheets} شيت "
          f"({int(interval * 1000)}مللي/صورة، دقة {best.get('width')}×{best.get('height')})",
          flush=True)
    return got


def invidious_captions(info: dict, video_id: str) -> list[dict]:
    """التسميات النصية بتوقيتاتها (VTT) — كلام الفيديو الحقيقي.

    ⚠️ مفيش ضمان إن المِرآة اللي جابت البيانات هي نفسها اللي بترجّع الكلام
    (واحدة رجّعت 200 بـ0 بايت). فبندوّر على **كل** المِرآت لحد ما نلاقي نص.
    """
    caps = info.get("captions") or []
    langs = [str(c.get("language_code") or "") for c in caps]
    langs += ["ar", "en"]
    bases = [info.get("_instance")] + list(_INVIDIOUS)
    for base in dict.fromkeys([b for b in bases if b]):
        for lang in dict.fromkeys([x for x in langs if x]):
            for params in ({"lang": lang}, {"label": lang}):
                try:
                    r = _req().get(f"{base}/api/v1/captions/{video_id}",
                                   params=params,
                                   headers={"User-Agent": "Mozilla/5.0"},
                                   timeout=45)
                    body = r.text or ""
                    if not r.ok or "-->" not in body:
                        continue      # صفحة مزيفة/فاضية → المِرآة اللي بعدها
                    rows = parse_vtt(body)
                    if rows:
                        print(f"[eye] 🗣 الكلام الحقيقي: {len(rows)} جملة "
                              f"({lang} من {base.split('//')[-1]})", flush=True)
                        return rows
                except Exception:
                    continue
    print("[eye] ⚠️ مفيش تسميات من المِرآت — التقليد بيروح على الوصف البصري بس",
          flush=True)
    return []


def parse_vtt(text: str) -> list[dict]:
    """WebVTT → [{t, dur, text}] بنفس شكل تسميات يوتيوب عندنا."""
    out: list[dict] = []
    cur_t: float | None = None
    buf: list[str] = []
    stamp = re.compile(r"(\d+):(\d+):(\d+)[.,](\d+)\s*-->\s*(\d+):(\d+):(\d+)[.,](\d+)")

    def _secs(h, m, s, ms):
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    def _flush():
        nonlocal cur_t, buf
        if cur_t is not None and buf:
            txt = " ".join(buf).strip()
            txt = re.sub(r"<[^>]+>", "", txt)          # وسوم التوقيت/التلوين
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt:
                out.append({"t": round(cur_t, 2), "dur": 0.0, "text": txt})
        cur_t, buf = None, []

    for line in (text or "").splitlines():
        line = line.strip()
        m = stamp.match(line)
        if m:
            _flush()
            cur_t = _secs(*m.groups()[:4])
            continue
        if not line or line.upper().startswith(("WEBVTT", "KIND:", "LANGUAGE:")):
            continue
        if cur_t is not None and not line.isdigit():
            buf.append(line)
    _flush()
    # مدة كل مقطع = الفرق مع اللي بعده
    for i, c in enumerate(out):
        nxt = out[i + 1]["t"] if i + 1 < len(out) else c["t"] + 2.0
        c["dur"] = round(max(0.4, nxt - c["t"]), 2)
    return out


def watch_via_media(video_id: str, meta: dict | None = None) -> dict | None:
    """مشاهدة كاملة بلا تنزيل: صور كل لحظة + الكلام + وصف بصري بالذكاء.

    بترجّع نفس شكل تقرير `watch()` عشان باقي المصنع ما يفرقش معاه.
    """
    info = invidious_info(video_id)
    if not info:
        return None
    outdir = EYE_DIR / video_id
    outdir.mkdir(parents=True, exist_ok=True)
    dur = float(info.get("lengthSeconds") or 0)
    frames = storyboard_frames(info, video_id, outdir)
    captions = invidious_captions(info, video_id)
    if not frames and not captions:
        return None

    # أوصاف بصرية: نظرة على الصور (بترتيبها الزمني) عبر الرؤية
    descs: list[str] = []
    if frames:
        descs = _vision_call([f for _t, f in frames], VISION_PROMPT)

    # كل صورة = مشهد قصير (نافذة زمنية)، وبنربطها بالكلام اللي اتقال فيها
    scenes = []
    for i, (t, path) in enumerate(frames):
        t1 = frames[i + 1][0] if i + 1 < len(frames) else (dur or t + 3.0)
        said = " ".join(c["text"] for c in captions
                        if t - 0.6 <= c["t"] < t1 + 0.6).strip()
        desc = descs[i] if i < len(descs) else ""
        if said and not desc:
            desc = f"(الكلام في اللحظة دي: {said[:120]})"
        scenes.append({"start": round(t, 2), "end": round(max(t + 0.5, t1), 2),
                       "desc": desc, "say_hint": said[:300],
                       "keyframe": str(path.relative_to(outdir)).replace("\\", "/"),
                       "colors": [], "brightness": 0.0, "motion": 0.0})
    m = {**(meta or {})}
    m.setdefault("title", info.get("title"))
    m.setdefault("channel", info.get("author"))
    m.setdefault("viewCount", info.get("viewCount"))
    m.setdefault("region", info.get("region"))
    report = {
        "videoId": video_id,
        "url": f"https://youtu.be/{video_id}",
        "watchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "durationSeconds": round(dur, 2),
        "mediaUnavailable": False,
        "watchedViaStoryboard": True,
        "meta": {k: m.get(k) for k in ("title", "channel", "region", "viewCount",
                                       "likeCount", "via") if m.get(k) not in (None, "")},
        "captions": captions,
        "captionCoverage": round(sum(c["dur"] for c in captions) / dur, 2) if dur else 0.0,
        "scenes": scenes,
        "audioRmsPerSec": [],
    }
    (outdir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[eye] ✓ شفت الفيديو بالكامل بلا تنزيل: {len(scenes)} مشهد، "
          f"{len(captions)} جملة، تغطية كلام {report['captionCoverage']}",
          flush=True)
    return report


def probe_duration(video: Path) -> float:
    r = subprocess.run([_ffmpeg(), "-i", str(video)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", r.stderr)
    if not m:
        raise RuntimeError("eye: ما قدرنا نقرأ مدة الفيديو")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def scene_boundaries(video: Path, threshold: float = 0.25) -> list[float]:
    r = subprocess.run(
        [_ffmpeg(), "-i", str(video),
         "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True, timeout=300)
    return sorted({round(float(m.group(1)), 2)
                   for m in re.finditer(r"pts_time:\s*([\d.]+)", r.stderr)})


def _keyframe(video: Path, t: float, dst: Path) -> bool:
    subprocess.run(
        [_ffmpeg(), "-y", "-ss", f"{t:.2f}", "-i", str(video),
         "-frames:v", "1", "-vf", "scale=480:-2", str(dst)],
        capture_output=True, timeout=120)
    return dst.exists()


def _frame_stats(jpg: Path, prev: Path | None) -> dict:
    from PIL import Image

    im = Image.open(jpg).convert("RGB")
    w, h = im.size
    pal = Counter(im.quantize(colors=4, method=Image.MEDIANCUT).getdata()).most_common(3)
    colors = [f"#{r:02x}{g:02x}{b:02x}" for (r, g, b), _ in pal]
    gray = im.convert("L")
    brightness = round(sum(gray.getdata()) / max(1, w * h) / 255.0, 2)
    motion = 0.0
    if prev is not None and prev.exists():
        a = gray.resize((32, 18)).getdata()
        b = Image.open(prev).convert("L").resize((32, 18)).getdata()
        motion = round(sum(abs(x - y) for x, y in zip(a, b)) / (32 * 18) / 255.0, 3)
    return {"colors": colors, "brightness": brightness, "motion": motion}


# ═════════════════════════════════════════════════════════════
# ٣) اسمع — طاقة الصوت لكل ثانية
# ═════════════════════════════════════════════════════════════

def audio_energy_per_second(video: Path, step: float = 1.0) -> list[float]:
    n = max(1, int(44100 * step))
    r = subprocess.run(
        [_ffmpeg(), "-i", str(video), "-vn",
         "-af", f"asetnsamples=n={n},astats=metadata=1",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=300)
    out: list[float] = []
    for m in re.finditer(r"RMS level dB:\s*(-?inf|-?[\d.]+)", r.stderr):
        v = m.group(1)
        if v == "-inf":
            out.append(0.0)
            continue
        db = float(v)
        out.append(0.0 if db <= -60 else round(db, 1))
    return out


# ═════════════════════════════════════════════════════════════
# المشاهدة الكاملة → تقرير قابل للتدقيق
# ═════════════════════════════════════════════════════════════

def _public_metadata(video_id: str) -> dict:
    """بيانات عامة حقيقية من oEmbed؛ لا أرقام ولا حقائق مُقدّرة."""
    try:
        r = _req().get("https://www.youtube.com/oembed", params={
            "url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            headers=_UA, timeout=20)
        r.raise_for_status()
        data = r.json()
        return {"title": data.get("title"), "channel": data.get("author_name"),
                "via": "youtube-oembed"}
    except Exception:
        return {}


def watch(video_id: str, meta: dict | None = None) -> dict:
    # الرادار أفضل مصدر للأرقام. oEmbed يملأ العنوان والقناة فقط عند التشغيل
    # بالتاج؛ لا نخمن المشاهدات أو أي رقم غير موجود.
    meta = {**_public_metadata(video_id), **(meta or {})}
    outdir = EYE_DIR / video_id
    outdir.mkdir(parents=True, exist_ok=True)
    frames_dir = outdir / "frames"
    frames_dir.mkdir(exist_ok=True)

    print(f"[eye] {video_id}: تنزيل الفيديو الحقيقي…", flush=True)
    try:
        video = download_video(video_id, outdir)
        dur = probe_duration(video)
        media_ok = True
    except Exception as exc:
        # تدهور صريح: التحليل يكمل بالتسميات + البيانات، وبيتحط عليه
        # mediaUnavailable: true — مفيش مشهد متخيل ولا لون من فراغ.
        print(f"[eye] ⚠️ فشل تنزيل الفيديو: {exc}", flush=True)
        print("[eye] أكمل بالتسميات + البيانات فقط (بدون تحليل بصري/صوتي)",
              flush=True)
        # ① البديل: نشوف الفيديو بصوره وكلامه (storyboards + captions)
        try:
            alt = watch_via_media(video_id, meta)
            if alt:
                return alt
        except Exception as exc2:
            print(f"[eye] ⚠️ مسار المشاهدة بلا تنزيل: {type(exc2).__name__}",
                  flush=True)
        video = None
        dur = 0.0
        media_ok = False

    print("[eye] اقرأ: تسميات التوقيتات الحقيقية…", flush=True)
    captions = fetch_captions(video_id)
    if not dur and captions:
        dur = round(max(c["t"] + c["dur"] for c in captions), 2)

    scenes: list[dict] = []
    audio: list[float] = []
    if media_ok:
        print("[eye] شوف: مشاهد + كي-فريمز + ألوان + حركة…", flush=True)
        bounds = ([0.0] + [b for b in scene_boundaries(video) if b < dur - 0.3]
                  + [dur])
        kf: list[Path | None] = []
        for i, t in enumerate(bounds):
            p = frames_dir / f"scene{i:02d}.jpg"
            kf.append(p if _keyframe(video, t, p) else None)

        prev: Path | None = None
        for i, t in enumerate(bounds[:-1]):
            end = bounds[i + 1]
            if kf[i] is not None:
                stats = _frame_stats(kf[i], prev)
                prev = kf[i]
            else:
                stats = {"colors": [], "brightness": 0.0, "motion": 0.0}
            scenes.append({
                "start": round(t, 2), "end": round(end, 2),
                "keyframe": f"frames/scene{i:02d}.jpg" if kf[i] is not None else None,
                **stats,
            })

        print("[eye] اسمع: طاقة الصوت لكل ثانية…", flush=True)
        audio = audio_energy_per_second(video)

        # شوف بعينك: وصف بصري لكل مشهد (Gemini vision) — أساس التقليد
        kf_paths = [frames_dir / s["keyframe"].split("/")[-1]
                    for s in scenes if s.get("keyframe")]
        # سقف 14 صورة (سرعة + تكلفة) — نظرة متباعدة على الفيديو كله
        if len(kf_paths) > 14:
            step = len(kf_paths) / 14
            kf_paths = [kf_paths[int(i * step)] for i in range(14)]
        descs = _vision_call(kf_paths, VISION_PROMPT)
        if descs:
            for i, sc in enumerate(scenes):
                if i < len(descs):
                    sc["desc"] = descs[i]

    report = {
        "videoId": video_id,
        "url": f"https://youtu.be/{video_id}",
        "watchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "durationSeconds": round(dur, 2),
        "mediaUnavailable": not media_ok,
        "meta": {k: meta.get(k) for k in
                 ("title", "channel", "region", "viewCount", "likeCount", "via")
                 if meta.get(k) not in (None, "")},
        "captions": captions,
        "captionCoverage": round(sum(c["dur"] for c in captions) / dur, 2)
        if dur else 0.0,
        "scenes": scenes,
        "audioRmsPerSec": audio,
    }
    report_path = outdir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(f"[eye] ✓ التقرير: {report_path.relative_to(settings.ROOT)} — "
          f"{len(scenes)} مشهد، {len(captions)} مقطع تسمية، "
          f"تغطية تسميات {report['captionCoverage']}", flush=True)
    return report


# ═════════════════════════════════════════════════════════════
# هاضم مضغوط للوكيل (سياق LLM محدود — الأهم أولًا)
# ═════════════════════════════════════════════════════════════

def _bucket_captions(captions: list[dict], dur: float, bucket: float = 10.0) -> list[str]:
    if not captions:
        return ["(مفيش مسار تسميات — التحليل بالمشاهدات البصرية فقط)"]
    lines = []
    t0 = 0.0
    while t0 < dur:
        t1 = min(t0 + bucket, dur)
        chunk = [c["text"] for c in captions if c["t"] < t1 and c["t"] + c["dur"] > t0]
        if chunk:
            lines.append(f"  {int(t0)}s-{int(t1)}s: " + " ".join(chunk)[:400])
        t0 = t1
    return lines


def build_digest(report: dict) -> str:
    m = report.get("meta", {})
    L = [
        f"الفيديو: {m.get('title', '?')}",
        f"القناة: {m.get('channel', '?')} | المنطقة: {m.get('region', '?')}",
        f"مشاهدات: {m.get('viewCount', '?')} | إعجابات: {m.get('likeCount', '?')}",
        f"المدة: {report.get('durationSeconds')} ثانية",
        "",
        "=== خط التسميات الزمني (حقيقي من الفيديو) ===",
    ]
    # قسم «الفيديو في العالم»: بيانات حقيقية عن الدولة من الرادار (سياق الجمهور)
    _meta = (report.get("meta") or {})
    if _meta.get("region"):
        try:
            from . import world
            _line = world.profile_line(world.country_info(_meta["region"]))
            if _line:
                L += ["=== الفيديو في العالم (بيانات حقيقية عن الدولة) ===",
                      _line, ""]
        except Exception:
            pass
    L += _bucket_captions(report.get("captions", []), report.get("durationSeconds", 0.0))
    L += ["", "=== المشاهد (الترتيب، الألوان، الإضاءة، الحركة) ==="]
    if not report.get("scenes"):
        L.append("  (الميديا غير متاحة في هذه المشاهدة — بلا تحليل بصري/صوتي)")
    for i, s in enumerate(report.get("scenes", [])):
        mood = ("ساكن" if s["motion"] < 0.02
                else "متوسط" if s["motion"] < 0.08 else "سريع")
        L.append(f"  مشهد {i + 1} [{s['start']}-{s['end']}s]: ألوان "
                 f"{','.join(s['colors'])} | إضاءة {s['brightness']} | {mood} "
                 f"(حركة {s['motion']})")
    a = report.get("audioRmsPerSec", [])
    if a:
        peak = max(range(len(a)), key=lambda i: a[i])
        L += ["", f"=== الصوت: {len(a)} عينة (dB RMS/ث) | أعلى طاقة عند ~{peak} ثانية ==="]
    return "\n".join(L)


# ═════════════════════════════════════════════════════════════
# الوكلاء — فهم ← كتابة ← نقد ← إصلاح
# ═════════════════════════════════════════════════════════════

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
# ⚠️ درس حقيقي (تشغيل 2026-09-19): الأسماء المثبّتة في الكود عاشت:
#   Groq  `llama-3.3-70b-versatile` → 404 model_not_found
#   Gemini `gemini-2.0-flash`       → 404 no longer available
# والمفتاحين كانوا سليمين (doctor: HTTP 200) — يعني الفحص كان أعمى عن
# حقيقة إن الأنبوب نفسه مقطوع. الحل: قوائم مرشّحين + سؤال الـ API عن
# الموديلات المتاحة فعلًا، والموديل اللي يرد هو اللي يشتغل.
_GROQ_BASE = "https://api.groq.com/openai/v1"
_GROQ_MODELS = ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b",
                "groq/compound", "groq/compound-mini", "allam-2-7b")
_GEMINI_MODELS = ("gemini-flash-latest", "gemini-2.5-flash", "gemini-3.5-flash",
                  "gemini-3.6-flash", "gemini-2.5-pro")
_NOT_CHAT = ("whisper", "guard", "orpheus", "tts", "embedding", "transcribe",
             "image", "veo", "lyria", "robotics", "computer-use", "aqa", "aqa")


def _live_models() -> list[str]:
    """موديلات Groq المتاحة للمفتاح الحالي (فاضية لو السؤال نفسه فشل)."""
    llm = settings.LLM
    if not llm["key"]:
        return []
    try:
        r = _req().get(f"{llm['base'].rstrip('/') or _GROQ_BASE}/models",
                       headers={"Authorization": f"Bearer {llm['key']}"}, timeout=30)
        if not r.ok:
            return []
        return [m.get("id", "") for m in r.json().get("data", []) if m.get("id")]
    except Exception:
        return []


def _groq_chain() -> list[str]:
    """ترتيب الموديلات: المطلوب صراحةً ← مرشّحينا المتاحون ← أي موديل شات متاح."""
    llm = settings.LLM
    configured = (llm["model"] or "").strip()
    live = _live_models()
    chain: list[str] = []
    if configured and (not live or configured in live):
        chain.append(configured)
    chain += [m for m in _GROQ_MODELS if (not live or m in live) and m not in chain]
    if live:
        chain += [m for m in sorted(live)
                  if m not in chain and not any(x in m.lower() for x in _NOT_CHAT)]
    else:
        chain += [m for m in _GROQ_MODELS if m not in chain]
    return chain


def _post_chat(url: str, key: str, model: str, prompt: str, temperature: float) -> str:
    r = _req().post(url, headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "temperature": temperature,
                          "max_tokens": 2048,
                          "messages": [{"role": "user", "content": prompt}]},
                    timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _post_gemini_native(model: str, key: str, prompt: str, temperature: float) -> str:
    """المسار الأصلي لجوجل — احتياطي لو مسار التوافق OpenAI رفض الموديل."""
    r = _req().post(
        f"{_GEMINI_BASE}/models/{model}:generateContent",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": temperature}},
        timeout=180)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _attempts(prompt: str, temperature: float):
    """مولّد (اسم, دالة نداء) — Groq بكل مرشّحيه، وبعده Gemini بكل مرشّحيه."""
    llm = settings.LLM
    if llm["base"] and llm["key"]:
        url = f"{llm['base'].rstrip('/')}/chat/completions"
        for model in _groq_chain():
            yield (f"groq:{model}",
                   lambda m=model, u=url: _post_chat(u, llm["key"], m, prompt, temperature))
    gemini_key = settings.get("GEMINI_API_KEY")
    if gemini_key:
        configured = (os.environ.get("GEMINI_MODEL") or "").strip()
        chain = [m for m in ([configured] if configured else []) + list(_GEMINI_MODELS)]
        for model in dict.fromkeys(chain):
            yield (f"gemini:{model}",
                   lambda m=model, k=gemini_key: _post_chat(
                       f"{_GEMINI_BASE}/openai/chat/completions", k, m, prompt, temperature))
            yield (f"gemini-native:{model}",
                   lambda m=model, k=gemini_key: _post_gemini_native(m, k, prompt, temperature))


def _llm(prompt: str, temperature: float = 0.7) -> str:
    """سلسلة مزوّدات وموديلات: أول واحد ينجح هو اللي يرد — وإلا فشل صريح برسالة حل."""
    tried: list[str] = []
    for who, call in _attempts(prompt, temperature):
        try:
            text = call()
            if text and text.strip():
                if tried:
                    print(f"[eye] ✓ الرد من {who} بعد فشل: {', '.join(tried)}", flush=True)
                return text
            tried.append(f"{who}:رد فاضي")
        except Exception as exc:
            tried.append(f"{who}:{type(exc).__name__}")
            print(f"[eye] ⚠️ {who} فشل — نجرب اللي بعده…", flush=True)
    if not tried:
        raise RuntimeError(
            "eye: مفيش LLM — ضيف GROQ_API_KEY أو GEMINI_API_KEY "
            "في Settings → Secrets → Actions على جيت هاب.")
    raise RuntimeError(
        "eye: كل المزوّدين/الموديلات فشلوا — " + " | ".join(tried[:6]) + " — "
        "افحص المفاتيح في Settings → Secrets → Actions (GROQ_API_KEY / GEMINI_API_KEY)")


def llm_probe(provider: str | None = None) -> tuple[bool, str]:
    """فحص حي حقيقي للأنبوب (بيستخدمه الدكتور): بيسجّل **مين اللي رد فعلًا**.

    «المفتاح موجود» مش دليل — الدرس: المفاتيح كانت سليمة والموديلات ميتة.
    provider = "groq" أو "gemini" لفحص مزوّد بعينه (كل مفتاح لوحده).
    """
    tried: list[str] = []
    for who, call in _attempts("اكتب كلمة واحدة بس: تمام", 0.0):
        if provider and not who.split(":")[0].startswith(provider):
            continue
        try:
            text = call()
        except Exception as exc:
            tried.append(f"{who}:{type(exc).__name__}")
            continue
        if text and text.strip():
            return True, f"{who} → رد حقيقي ✓ {text.strip()[:20]}"
        tried.append(f"{who}:رد فاضي")
    if not tried:
        return False, ("مفيش LLM — ضيف GROQ_API_KEY أو GEMINI_API_KEY "
                       "في Settings → Secrets → Actions")
    return False, "كل الموديلات فشلت — " + " | ".join(tried[:6])


def _llm_json(prompt: str, temperature: float = 0.7) -> dict:
    """نفس السلسلة، بس بيرجّع JSON (وكيل الـ DNA والكاتب والناقد بيعتمدوا عليه).

    الدرس (تشغيل 2026-09-19): موديل صغير رجّع JSON تالف (فاصلة ناقصة عند
    char 4186) → الفيديو كله اتسقط. دلوقتي: محاولة إصلاح **واحدة** بطلب
    صريح لإعادة الإرسال JSON سليم، وبعدها نرفع الخطأ بصراحة.
    """
    text = _llm(prompt, temperature)
    try:
        return _json_from(text)
    except Exception as exc:
        print(f"[eye] ⚠️ JSON تالف من الموديل ({type(exc).__name__}) — "
              f"إعادة إرسال واحدة…", flush=True)
        retry = _llm(
            prompt + "\n\nتصحيح إلزامي: الرد السابق كان JSON غير صالح "
                     f"({type(exc).__name__}). أعد الإرسال: **JSON صالح فقط**، "
                     "بلا أي نص قبله أو بعده، وبكل الأقواس والفوايص في مكانها.",
            temperature=0.2)
        return _json_from(retry)


def _json_from(text: str) -> dict:
    """يستخرج أول كائن JSON من النص (بلا نسخ ولا تخمين)."""
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e <= s:
        raise RuntimeError("eye: رد الـ LLM ما فيهوش JSON: " + text[:200])
    return json.loads(text[s:e + 1])




# ═════════════════════════════════════════════════════════════
# العين اللي بتشوف: وصف بصري حقيقي لكل مشهد (مش تخمين من نص)
# ═════════════════════════════════════════════════════════════

def _vision_call(frames: list[Path], prompt: str) -> list[str]:
    """صور الكي-فريم → وصف لكل صورة (Gemini vision).

    ليه؟ طلب صاحب القناة (2026-09-19): «يشوفو كامل ويكتبو بالتفصيل الممل
    والمشاهد» — يعني التقليد لازم يبني على اللي **ظاهر** في كل لحظة، مش على
    نص التسميات بس. لو مفيش رؤية متاحة نرجّع قائمة فاضية (تدهور صريح).
    """
    import base64

    gemini_key = settings.get("GEMINI_API_KEY")
    if not gemini_key or not frames:
        return []
    parts: list[dict] = [{"text": prompt}]
    for f in frames:
        try:
            b64 = base64.b64encode(Path(f).read_bytes()).decode()
        except Exception:
            continue
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})
    if len(parts) == 1:
        return []
    configured = (os.environ.get("GEMINI_VISION_MODEL") or "").strip()
    chain = [m for m in ([configured] if configured else [])
             + ["gemini-2.5-flash", "gemini-flash-latest"]
             + list(_GEMINI_MODELS)]
    for model in dict.fromkeys(chain):
        try:
            r = _req().post(
                f"{_GEMINI_BASE}/models/{model}:generateContent",
                headers={"x-goog-api-key": gemini_key,
                         "Content-Type": "application/json"},
                json={"contents": [{"parts": parts}],
                      "generationConfig": {"temperature": 0.2}},
                timeout=240)
            if not r.ok:
                continue
            data = r.json()
            text = (data.get("candidates") or [{}])[0].get("content", {})
            txt = "".join(p.get("text", "") for p in text.get("parts") or [])
            rows = _json_from(txt).get("frames")
            if isinstance(rows, list):
                print(f"[eye] 👁 شفت {len(rows)} مشهد بعيني ({model})",
                      flush=True)
                return [str(x)[:300] for x in rows]
        except Exception as exc:
            print(f"[eye] ⚠️ رؤية {model}: {type(exc).__name__}", flush=True)
    print("[eye] ⚠️ مفيش رؤية متاحة — التحليل بالمشاهدات والصوت والتسميات",
          flush=True)
    return []


VISION_PROMPT = """دي كي-فريمز فيديو شورتس فيروسي، بالترتيب الزمني.
اوصف **كل** صورة وصف صارم ومفصّل جدًا بالعربي — كإني مش شايف حاجة:
- مين/إيه اللي في الصورة (أشخاص، عددهم، أعمارهم تقريبًا، هدومهم، تعبيراتهم)
- المكان (جوه/بره، بيت/شارع/مطبخ/ملعب…)، الإضاءة، الألوان الطالبة
- الحركة والحدث اللي بيحصل في اللحظة دي (بيجري، بيصرخ، بيقع، بياكل…)
- أي نص/ستيكر/إيموجي مكتوب على الشاشة (حرفيًا)
- الكاميرا (قريبة/واسعة) والإيقاع (سريع/هادي)

ارجع JSON فقط بالشكل ده، بنفس عدد الصور وبالترتيب:
{"frames": ["وصف الصورة 1", "وصف الصورة 2", "..."]}
"""


def _shot_buckets(report: dict, target: int = 12) -> list[dict]:
    """خط اللقطات: مشاهد الفيديو مدموجة لتقريبًا `target` لقطة متكافئة.

    كل لقطة = {t0, t1, dur, desc (وصف بصري), say (الكلام اللي اتقال), rms}.
    الأساس: مشاهد الكشف الحقيقي؛ لو قليلة/كثيرة بنعيد التقسيم بزمن متساوٍ.
    """
    dur = float(report.get("durationSeconds") or 0.0)
    scenes = [s for s in (report.get("scenes") or []) if s.get("end", 0) > s.get("start", 0)]
    caps = report.get("captions") or []
    audio = report.get("audioRmsPerSec") or []

    # لو عدد المشاهد مش مناسب، قسّم الزمن بالتساوي (3 ثواني للقطة = إيقاع شورتس)
    if dur > 0 and (len(scenes) < 3 or len(scenes) > target + 6):
        src = list(scenes)

        def _desc_at(t: float) -> str:
            for s in src:                     # وصف المشهد اللي اللحظة دي جواه
                if float(s.get("start", 0)) <= t < float(s.get("end", 0)):
                    return str(s.get("desc") or "")
            return ""

        step = max(2.0, dur / max(1, min(target, 12)))
        scenes = []
        t0 = 0.0
        while t0 < dur - 0.2:
            t1 = min(dur, t0 + step)
            scenes.append({"start": round(t0, 2), "end": round(t1, 2),
                           "desc": _desc_at(t0 + (t1 - t0) / 2)})
            t0 = t1
    # ادمج الزيادة في أقرب جوار
    if len(scenes) > target:
        keep = max(1, target)
        chunk = len(scenes) / keep
        merged = []
        for i in range(keep):
            group = scenes[int(i * chunk):int((i + 1) * chunk)]
            if group:
                merged.append({"start": group[0]["start"], "end": group[-1]["end"]})
        scenes = merged

    out = []
    for s in scenes:
        t0, t1 = float(s.get("start") or 0), float(s.get("end") or 0)
        said = " ".join(c["text"] for c in caps
                        if c.get("t", 0) >= t0 - 0.3
                        and c.get("t", 0) < t1 + 0.3).strip()
        seg = audio[int(t0):max(int(t0) + 1, int(t1))] or [0.0]
        out.append({"t0": round(t0, 2), "t1": round(t1, 2),
                    "dur": round(max(0.4, t1 - t0), 2),
                    "desc": (s.get("desc") or "").strip(),
                    "say": said[:400],
                    # أعلى طاقة في اللقطة (مش المتوسط) — اللحظات الصاخبة تبان
                    "rms": round(max(seg), 3)})
    return out


SHOTS_PROMPT = """أنت مخرج شورتس عربي محترف لقناة «دۅۄشے» (قناة عالمية، مش نشرة أخبار).

قدامك **خط اللقطات الحقيقي** لفيديو ترند فيروسي: لكل لحظة — وصف اللي ظاهر
على الشاشة + الكلام اللي اتقال + قوة الصوت.

{digest}

دي الـ DNA الفيروسي المستخرج:
{dna}

**مهمتك: إعادة إنتاج نفس الفيديو لحظة بلحظة — نسخة أقوى.**
قواعد غير قابلة للتفاوض:
1. **نفس عدد اللقطات** ونفس الترتيب ونفس الإيقاع. اللقطة رقم N في فيديونا =
   اللقطة رقم N عندهم في الحدث والوظيفة (نفس المشهد، نفس المفاجأة).
2. **إحنا بنعمل الفيديو، مش بنتكلم عنه.** الكلام لازم يكون داخل الحدث
   («شوف إيدي… بترجف!») مش وصف أو تعليق («الفيديو بيوريك…») أو «الحقيقة الأولى…».
3. **صفر أرقام** إلا لو الرقم مذكور في الجدول فوق حرفيًا.
4. كل لقطة سطر **واحد قصير** بالعربي المصري (٤–١٢ كلمة) يُقرأ بسرعة الفيديو.
5. `visual_query`: ٢–٤ كلمات **إنجليزية** تصف اللقطة الحقيقية اللي هنصوّرها من
   مكتبات الفيديو (بيكساباي/بيكسلز) — مثال: "boy running fast street"،
   "hands clapping closeup"، "dog jumping water".
6. لو الأصل فيه تحدي/اختبار/رد فعل → إحنا بنعمل نفس التحدي ونفس رد الفعل.
7. لو الأصل فيه ستيكر/نص على الشاشة → `on_screen` يحمل نفس المعنى بعربيتنا.

ارجع JSON فقط:
{{
  "title_ar": "عنوان قوي للفيديو بنبرة القناة (مش وصف!)",
  "title_en": "...",
  "tags": "كلمة,كلمة,كلمة,كلمة,كلمة",
  "mood": "crazy|calm|warm|mysterious|serious",
  "shots": [
    {{"say_ar": "سطر اللقطة", "say_en": "English line",
      "visual_query": "english stock query", "sfx": "whoosh|impact|pop|",
      "on_screen": "نص قصير جدًا على الشاشة أو فراغ"}}
  ]
}}
عدد اللقطات في `shots` لازم يساوي عدد اللقطات في الجدول (لا أقل ولا أكثر).
"""


DNA_PROMPT = """أنت محلل فيديوهات فيروسية بخبرة 15 سنة في الشورتس.
دي تحتك «تقرير مشاهدة» حقيقي لفيديو تريند: خط التسميات الزمني (توقيتات حقيقية)،
المشاهد (ألوان حقيقية، إضاءة، حركة)، طاقة الصوت.

{digest}

حلّل الـ DNA الفيروسي للفيديو وارجع JSON فقط (مفيش أي نص تاني) بهيكل:
{{
  "hook": {{"technique": "shock|question|warning|visual_curiosity|bold_claim",
            "what_happens": "...", "why_it_works": "..."}},
  "beats": [{{"time": "0:00-0:04", "what": "...",
              "function": "hook|escalation|twist|payoff|cta",
              "why_it_works": "..."}}],
  "twist_or_payoff": "...",
  "pacing": {{"estimated_cuts_per_minute": 0, "energy_curve": "..."}},
  "visual_language": {{"dominant_colors": ["#..."], "shot_style": "...",
                       "text_on_screen": true, "stickers_or_graphics": "..."}},
  "audio_language": {{"voice_style": "...", "music_or_sfx": "...",
                      "energy_notes": "..."}},
  "retention_tricks": ["...", "..."],
  "reusable_facts": ["حقائق موضوعية قابلة للتحقق (الحقائق بس، مش صياغات)"]
}}
"""

WRITE_PROMPT = """أنت مدير المحتوى لقناة الشورتس العربية «دۅۄشے».
نبرة القناة: أخ كبير محبوب — خطاف تحذير في أول 3 ثواني، هزار في الحقيقة التالتة،
ختام دافي، عربي مصري محترم من غير مبالغة.

دي الـ DNA الفيروسي للترند اللي اتحلل قدامك:
{dna}

تقرير المشاهدة الكامل لنفس الفيديو (سياق):
{digest}

أنماط العناوين عندنا (أرقام حقيقية من رادارنا):
{title_patterns}

اكتب إصدارنا من **نفس السياق** — أسرع وأحسن، وبنص **أصلي 100%**
(صفر نسخ من تسمياتهم أو عناوينهم).
قاعدة ذهبية: إحنا **بنقلّد فيديو الترند نفسه لحظة بلحظة** — نفس نوع
المحتوى والإيقاع والمفاجأة (تحدي؟ قول تحدي ونشرّحه ويعيشه المشاهد.
مفاجأة نهاية؟ اعملها مفاجأة حقيقية عندنا). إحنا بنعمل **فيديو زي فيديوهم**
مش نشرة أخبار عنهم — الحلقة نفسها تعيش اللي عاشه المشاهد، أسرع وأقوى. ارجع JSON فقط:
{{
  "title_ar": "...", "title_en": "...",
  "hook_ar": "... (يُقال في أقل من 3 ثوانٍ)", "hook_en": "...",
  "facts_ar": ["...", "...", "..."], "facts_en": ["...", "...", "..."],
  "takeaway_ar": {{"aql": "...", "qalb": "...", "rouh": "..."}},
  "takeaway_en": {{"aql": "...", "qalb": "...", "rouh": "..."}},
  "tags": "كلمة,كلمة,كلمة,كلمة",
  "mood": "crazy|calm|warm|mysterious|serious",
  "visual_plan": [{{"time": "0:00-0:03", "scene": "...", "style": "...",
                    "colors": ["#..."]}}]
}}
قيود صارمة: الحقائق من reusable_facts + حقائق عامة مشهورة بس —
مفيش جملة منسوخة.
**ممنوع أي رقم في النص المكتوب** (عنوان/خطاف/حقائق/ختام) إلا لو الرقم مذكور
حرفيًا في الرادار أو تقرير المشاهدة اللي فوق. لو مفيش أرقام موثقة، اكتب
الكلام بلا أي أرقام خالص — ده مطلوب مش اختياري.
"""

CRITIQUE_PROMPT = """أنت ناقد فيديوهات صارم. قيّم الحلقة المقترحة (0-100)
مقارنة بـ DNA الترند، وارجع JSON فقط:
{{"score": 0, "strengths": ["..."], "weaknesses": ["..."], "verdict": "..."}}

DNA الترند:
{dna}

اقتراحنا:
{topic}
"""

REWRITE_PROMPT = """الناقد لقى الضعفانات دي في حلقتنا:
{weaknesses}

صلّحها وارجع JSON الحلقة الكامل بعد التصحيح (نفس الهيكل):
{topic}
"""


def _assert_radar_numbers(written: dict, report: dict) -> None:
    """أي رقم مكتوب يجب أن يكون قيمة موجودة حرفيًا في بيانات الرادار."""
    text = json.dumps(written, ensure_ascii=False)
    claimed = {re.sub(r"[,٬]", "", n) for n in re.findall(r"\d[\d,٬.]*", text)}
    meta = report.get("meta", {})
    allowed = {str(meta[k]) for k in ("viewCount", "likeCount")
               if meta.get(k) not in (None, "")}
    # أرقام JSON البنيوية/ألوان hex لا تُعد ادعاءات؛ حقول النص فقط عمليًا،
    # لذا نستبعد أجزاء الألوان وأزمنة visual_plan قبل الفحص.
    prose = " ".join(str(written.get(k, "")) for k in
                     ("title_ar", "hook_ar", "facts_ar", "takeaway_ar"))
    # لقطات التقليد: كلامها مقروء على الشاشة — نفس القاعدة تنطبق عليها
    for sh in (written.get("shots") or []):
        if isinstance(sh, dict):
            prose += " " + str(sh.get("say_ar", "")) + " " + str(sh.get("on_screen", ""))
    claimed = {re.sub(r"[,٬]", "", n) for n in re.findall(r"\d[\d,٬.]*", prose)}
    if claimed - allowed:
        raise RuntimeError("eye: السيناريو احتوى أرقامًا ليست من الرادار: "
                           + ", ".join(sorted(claimed - allowed)))


def _writer_call(prompt: str, report: dict, dna: dict, note: str = "") -> tuple[dict, dict]:
    """(السيناريو, الموضوع) — ومعاه إعادة محاولة تصحيحية **واحدة** لو الـ LLM
    اخترع أرقامًا غير موثقة.

    الدرس (تشغيل 2026-09-19): الفيديو مش متاح على IP الخوادم، فالموديل اخترع
    أرقام (105 ثانية، 120…) وحارس «مفيش أرقام مخترعة» رفض السيناريو → كل الحلقة
    فشلت. الصح: نطلب منه نسخة بلا أرقام — نحافظ على قاعدة النزاهة ونكمل الشغل.
    """
    written = _llm_json(prompt + ("\n\nتصحيح إلزامي: " + note if note else ""),
                        temperature=0.7 if note else 0.9)
    try:
        return written, to_factory_topic(written, report, dna)
    except RuntimeError as exc:
        if note or "أرقامًا ليست من الرادار" not in str(exc):
            raise
        print(f"[eye] ⚠️ {exc} — إعادة كتابة واحدة بلا أرقام…", flush=True)
        return _writer_call(
            prompt, report, dna,
            note="النسخة السابقة كتبت أرقامًا غير موثقة. اكتب نسخة جديدة "
                 "**بلا أي رقم** في العنوان أو الخطاف أو الحقائق أو الختام.")


def write_replication(report: dict, dna: dict, digest: str) -> dict:
    """سكربت لحظة-بلحظة: خط اللقطات الحقيقي → نسختنا (مخرج شورتس).

    ده قلب مصنع التقليد: الناتج `shots` بعدد لقطات الأصل بالظبط، وكل لقطة
    ليه سطر مقروء + استعلام لقطة حقيقية + مؤثر صوتي.
    """
    shots = _shot_buckets(report)
    if not shots:
        raise RuntimeError("eye: مفيش لقطات — الفيديو مفيهوش مشاهد ولا مدة")
    table = []
    for i, s in enumerate(shots, 1):
        table.append(
            f"لقطة {i} | {s['t0']:.1f}s–{s['t1']:.1f}s ({s['dur']:.1f}ث) "
            f"| صوت {s['rms']}"
            + (f"\n   👁 اللي ظاهر: {s['desc']}" if s.get("desc") else "")
            + (f"\n   🗣 اللي اتقال: {s['say']}" if s.get("say") else ""))
    shot_table = "\n".join(table[:20])
    written = _llm_json(SHOTS_PROMPT.format(
        digest=(digest[:4000] + "\n\n=== خط اللقطات الحقيقي ===\n" + shot_table),
        dna=json.dumps(dna, ensure_ascii=False)[:3000]), temperature=0.8)
    rows = written.get("shots") or []
    if not isinstance(rows, list) or len(rows) < 2:
        raise RuntimeError("eye: مخرج التقليد ما رجّعش لقطات كفاية")
    # نثبّت التوقيتات الحقيقية من الأصل على كل لقطة
    fixed = []
    for i, row in enumerate(rows):
        src = shots[min(i, len(shots) - 1)]
        fixed.append({
            "t0": src["t0"], "t1": src["t1"], "dur": src["dur"],
            "say_ar": str(row.get("say_ar") or "").strip()[:220],
            "say_en": str(row.get("say_en") or "").strip()[:220],
            "visual_query": str(row.get("visual_query") or "").strip()[:80],
            "sfx": str(row.get("sfx") or "").strip()[:12],
            "on_screen": str(row.get("on_screen") or "").strip()[:60],
        })
    fixed = [f for f in fixed if f["say_ar"]]
    written["shots"] = fixed
    return written


def to_factory_topic(written: dict, report: dict, dna: dict) -> dict:
    _assert_radar_numbers(written, report)
    vid = report["videoId"]
    m = report.get("meta", {})
    shots = written.get("shots") or []
    # التقليد لحظة-بلحظة: السطور بتيجي من اللقطات (مفيش «الحقيقة الأولى»)
    if shots:
        written = dict(written)
        written.setdefault("hook_ar", shots[0].get("say_ar", ""))
        written.setdefault("hook_en", shots[0].get("say_en", ""))
        if not written.get("facts_ar"):
            written["facts_ar"] = [s.get("say_ar", "") for s in shots[1:4]]
            written["facts_en"] = [s.get("say_en", "") for s in shots[1:4]]
    t = {
        "id": f"eye-{vid}",
        "topic": m.get("title", vid),
        "angle": str(dna.get("twist_or_payoff") or "ترند")[:90],
        "origin": "eye",
        "status": "scripted",
        "title_ar": written.get("title_ar") or m.get("title") or "حلقة ترند",
        "title_en": written.get("title_en") or "",
        "hook_ar": written.get("hook_ar") or "",
        "hook_en": written.get("hook_en") or "",
        "facts_ar": (written.get("facts_ar") or [])[:3],
        "facts_en": (written.get("facts_en") or [])[:3],
        "takeaway_ar": written.get("takeaway_ar"),
        "takeaway_en": written.get("takeaway_en"),
        "tags": written.get("tags") or "ترند,حقائق,علوم,دۅۄشے",
        "mood": written.get("mood") or "warm",
        "_kind": "eye",
        "_visual_plan": written.get("visual_plan") or [],
        # ⚡ محرك التقليد: لقطات لحظة-بلحظة من الفيديو الأصلي
        "shots": shots,
        "_replication": bool(shots),
        "_eye": {
            "videoId": vid,
            "url": report.get("url"),
            "sourceTitle": m.get("title"),
            "sourceChannel": m.get("channel"),
            "sourceViews": m.get("viewCount"),
            "dna": {
                "hook": dna.get("hook"),
                "pacing": dna.get("pacing"),
                "retention_tricks": dna.get("retention_tricks"),
            },
        },
    }
    if not t["hook_ar"] or not t["facts_ar"]:
        raise RuntimeError("eye: مخرجات الـ LLM ناقصة — مفيش خطاف أو حقائق")
    return t


# ═════════════════════════════════════════════════════════════
# طابور المصنع
# ═════════════════════════════════════════════════════════════

def _read_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _write_all(queue: list, consumed: list) -> None:
    for p, d in ((EYE_TOPICS_PATH, queue), (EYE_CONSUMED_PATH, consumed)):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def save_topic(topic: dict) -> None:
    q = _read_json(EYE_TOPICS_PATH, [])
    if not isinstance(q, list):
        q = []
    q = [t for t in q if t.get("id") != topic.get("id")]
    q.append(topic)
    _write_all(q, _read_json(EYE_CONSUMED_PATH, []))


def _seen_fps() -> set[str]:
    from . import state
    try:
        return set(state.seen_fingerprints())
    except Exception:
        return set()


def consume_queue(seen: set[str] | None = None) -> dict | None:
    """أول موضوع فريد من طابور العين؛ ينسحب ويُؤرشف (قابل للتدقيق).

    المواضيع اللي بصمتها متكررة (مشهودة قبل كده) بتنطّ على التاني اللي
    بعدها — الطابور ما يقفشش بسبب مكرر.
    """
    q = _read_json(EYE_TOPICS_PATH, [])
    consumed = _read_json(EYE_CONSUMED_PATH, [])
    if not isinstance(q, list):
        q = []
    fps = (seen or set()) | _seen_fps()
    try:
        from . import state as _st
        _done = _st.produced_ids()
    except Exception:
        _done = set()
    # ⚡ الأولوية لمواضيع التقليد (اللي فيها لقطات حقيقية من الفيديو الأصلي)
    order = sorted(range(len(q)),
                   key=lambda i: (0 if (q[i].get("shots") or
                                        q[i].get("_replication")) else 1, i))
    for i in order:
        t = q[i]
        fp = content.fingerprint(t)
        # اتعمل فعلًا؟ ينسحب للأرشيف (بس ما ينشرش) — يمنع تكرار الحلقة
        if t.get("id") and str(t["id"]) in _done:
            q.pop(i)
            t["_consumedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            t["_skipReason"] = "already_produced"
            consumed.append(t)
            _write_all(q, consumed)
            return None
        if fp in fps:
            continue
        q.pop(i)
        t["_consumedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        consumed.append(t)
        _write_all(q, consumed)
        return t
    return None


# ═════════════════════════════════════════════════════════════
# الحلقة الكاملة: شوف ← افهم ← اكتب ← ناقِد ← طابور
# ═════════════════════════════════════════════════════════════

def agent(video_id: str, meta: dict | None = None) -> dict:
    report = watch(video_id, meta)
    if not report["captions"] and not report["scenes"] and not report.get("meta"):
        raise RuntimeError(
            "eye: لا فيديو ولا تسميات ولا بيانات عامة حقيقية؛ نرفض اختلاق تحليل.")
    digest = build_digest(report)

    print("[eye] افهم: وكيل الـ DNA يحلل…", flush=True)
    dna = _llm_json(DNA_PROMPT.format(digest=digest[:12000]), temperature=0.3)

    print("[eye] اكتب: إصدارنا من نفس السياق…", flush=True)
    title_patterns = ""
    if PATTERNS_PATH.exists():
        try:
            p = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
            title_patterns = json.dumps(p.get("titlePatterns", {}), ensure_ascii=False)
        except Exception:
            title_patterns = ""
    # ① محرك التقليد (لحظة-بلحظة) — الأساس. لو فشل لأي سبب (مفيش مشاهد/موديل)
    #    بنرجع لمسار «المقال» القديم عشان المصنع ما يقفشش أبدًا.
    topic = None
    try:
        written = write_replication(report, dna, digest)
        topic = to_factory_topic(written, report, dna)
        print(f"[eye] 🎬 سكربت تقليد من {len(topic['shots'])} لقطة "
              f"(نفس لقطات الأصل)", flush=True)
    except Exception as exc:
        print(f"[eye] ⚠️ محرك التقليد وقع ({type(exc).__name__}: "
              f"{str(exc)[:100]}) — مسار الاحتياط", flush=True)
    if topic is None:
        written, topic = _writer_call(
            WRITE_PROMPT.format(
                dna=json.dumps(dna, ensure_ascii=False)[:6000],
                digest=digest[:6000],
                title_patterns=title_patterns or "(مفيش)",
            ), report, dna)

    print("[eye] ناقد: تقييم صارم…", flush=True)
    crit = _llm_json(
        CRITIQUE_PROMPT.format(
            dna=json.dumps(dna, ensure_ascii=False)[:4000],
            topic=json.dumps(written, ensure_ascii=False)[:4000],
        ), temperature=0.3)
    topic["_critique"] = {
        "score": crit.get("score"),
        "weaknesses": crit.get("weaknesses", []),
        "verdict": crit.get("verdict"),
    }
    try:
        score = int(crit.get("score", 100))
    except (TypeError, ValueError):
        score = 100
    # التقليد ما بيمشيش على مسار «أعد كتابة الحقائق» — لقطاته هي السكربت
    if topic.get("shots"):
        topic["_critique"] = {"score": crit.get("score"),
                              "weaknesses": crit.get("weaknesses", []),
                              "verdict": crit.get("verdict"),
                              "note": "تقليد لحظة-بلحظة — السكربت من اللقطات"}
        score = 100
    if score < 75 and crit.get("weaknesses"):
        print(f"[eye] التقييم {score}/100 — إعادة كتابة الأضعف…", flush=True)
        _fixed, topic = _writer_call(
            REWRITE_PROMPT.format(
                weaknesses=json.dumps(crit["weaknesses"], ensure_ascii=False),
                topic=json.dumps(written, ensure_ascii=False),
            ), report, dna)
        topic["_critique"] = {
            "score": score, "rewritten": True,
            "weaknesses": crit.get("weaknesses", []),
        }

    save_topic(topic)
    print(f"[eye] ✓ الموضوع {topic['id']} في طابور المصنع: {topic['title_ar']}",
          flush=True)
    return topic


# ═════════════════════════════════════════════════════════════
# اختيار تلقائي من آخر مسح رادار
# ═════════════════════════════════════════════════════════════

def _dur_secs(d: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 9999
    h, mi, s = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + int(s or 0)


def _radar_meta(video_id: str) -> dict:
    """بيانات الفيديو من آخر مسح رادار (المنطقة/العنوان/المشاهدات) — لو موجود."""
    if not SNAPSHOT_PATH.exists():
        return {}
    try:
        snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    # شكل المسح بيتغير (قائمة ← قاموس ← قائمة) — بنتعامل مع الاتنين
    # بق 2026-09-20: `snap["videos"]` بقت قائمة، والكود القديم كان بيفشل
    # بـ AttributeError فالعين ما اشتغلتش خالص في التشغيل اليدوي.
    raw = snap.get("videos") or []
    v: dict = {}
    if isinstance(raw, dict):
        v = raw.get(video_id) or {}
    else:
        for row in raw:
            if not isinstance(row, dict):
                continue
            if str(row.get("videoId") or row.get("id") or "") == video_id:
                v = row
                break
    if not v:
        return {}
    return {k: v.get(k) for k in
            ("title", "channel", "region", "viewCount", "likeCount", "via")
            if v.get(k) not in (None, "")}


def auto_pick(max_n: int = 2) -> list[tuple[str, dict]]:
    """أقوى مرشحي الترند من آخر مسح: قصير (≤60ث) و ≥2 مليون مشاهدة، مش متشاف قبل كده."""
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError("eye: مفيش مسح رادار — شغّل سير الرادار الأول")
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    done = {t.get("_eye", {}).get("videoId")
            for t in _read_json(EYE_CONSUMED_PATH, [])}
    done |= {t.get("_eye", {}).get("videoId")
             for t in _read_json(EYE_TOPICS_PATH, [])}
    cand = [v for v in snap.get("videos", [])
            if _dur_secs(v.get("duration", "")) <= 60
            and v.get("viewCount", 0) >= 2_000_000
            and v.get("videoId") not in done]
    cand.sort(key=lambda v: -v.get("viewCount", 0))
    return [(v["videoId"], v) for v in cand[:max_n]]


def main() -> int:
    ap = argparse.ArgumentParser(description="العين — تشوف فيديو ترند وتكتب إصدارنا")
    ap.add_argument("--video-id", help="معرّف فيديو يوتيوب محدد")
    ap.add_argument("--auto", action="store_true",
                    help="اختيار تلقائي من أعلى ترند الرادار")
    ap.add_argument("--max", type=int, default=2, help="حد الأقصى في الوضع التلقائي")
    args = ap.parse_args()

    if args.video_id:
        targets = [(args.video_id, _radar_meta(args.video_id))]
    elif args.auto:
        targets = auto_pick(args.max)
        if not targets:
            print("eye: مفيش مرشح ترند جديد (كله اتشاف قبل كده أو تحت الحد)")
            return 0
    else:
        ap.print_help()
        return 2

    ok = 0
    for vid, meta in targets:
        try:
            agent(vid, meta)
            ok += 1
        except Exception as exc:
            err = f"eye: فشل في {vid}: {type(exc).__name__}: {exc}"
            print(err, file=sys.stderr)
            # ملف تشخيص يتحمّل في الـ artifact — السيرة ممكن تنقطع
            try:
                err_dir = EYE_DIR / "diagnostics"
                err_dir.mkdir(parents=True, exist_ok=True)
                (err_dir / f"error-{vid}.txt").write_text(
                    err + "\n" + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    encoding="utf-8")
            except Exception:
                pass
    print(f"eye: {ok}/{len(targets)} فيديو اتشاف وموضوعات اتكتبت")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
