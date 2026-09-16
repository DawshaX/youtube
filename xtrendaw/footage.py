"""مكتبة اللقطات الحيّة — فيديو حقيقي متحرك يطابق معنى الكلام (مش صور مركبة).

مصادر مجانية بلا مفاتيح:
  1) Wikimedia Commons video — طبيعة/حيوان/سماء/مساجد/مكة (الأساس)
  2) Internet Archive — صحراء/تاريخ/وثائقيات ملك عام
  3) NASA Video API — كون/أرض/شمس

ضوابط الجودة:
  - رفض أي لقطة عليها نص محروق (كاشف بكسلات أبيض/أصفر في شريطي أعلى/أسفل)
  - رفض عناوين ترويجية (نشرات/مقابلات/إعلانات)
  - القصّة بتتظبط 1080×1920@30 وتتخزن في مكتبة محلية صغيرة (state/videolib)
    عشان تتعاد في حلقات تانية من غير تحميل — المخزون بيتأهل.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from . import settings
from .tts import ffmpeg

UA = {"User-Agent": "XDAW-NOVA-noor/1.0 (free dawah shorts; educational)"}
LIB = settings.STATE / "videolib"
MAX_LIB_MB = 40
NASA = "https://images-api.nasa.gov"
MAX_DL = 30 * 1024 * 1024

# ─────────────────────────────────────────────────────────────
# الخزنة المحلية — لقطات حركة مولّدة برمجيًا 100% داخل المصنع
# (xtrendaw/generate_footage_vault.py) → ملك المشروع بالكامل،
# بلا أي ترخيص خارجي مطلوب. دي الطبقة الافتراضية الوحيدة للقطات
# الحيّة؛ المصادر الشبكية (تحت) مقفولة افتراضيًا ومش بتتفتح غير
# بـ XT_NET_FOOTAGE=1 ولمّا كتالوج التراخيص يكون موثقًا.
# ─────────────────────────────────────────────────────────────
VAULT_DIR = settings.ASSETS / "footage"

# كل لقطة: (الملف, أنواع المشاهد اللي تناسبها, كلمات مفتاحية عربية من النص)
VAULT_INDEX: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    ("01_fire_hook_motion.mp4", ("hook",),
     ("نار", "نيران", "حريق", "لهب", "اشتعل", "يحترق", "حمم")),
    ("02_cash_rain_motion.mp4", ("fact1", "cta"),
     ("فلوس", "مال", "نقود", "دولار", "جائزة", "جوائز", "ثروة", "كاش",
      "مليون", "مبلغ")),
    ("03_blizzard_freeze_motion.mp4", ("fact2",),
     ("تلج", "ثلج", "جليد", "برد", "تجمد", "صقيع", "متجمد")),
    ("04_countdown_hud_motion.mp4", ("fact3",),
     ("وقت", "ثانية", "ثواني", "عد تنازلي", "ساعة", "مهلة", "دقائق")),
    ("05_confetti_winner_motion.mp4", ("outro", "cta"),
     ("فوز", "فائز", "بطل", "انتصار", "احتفال", "كأس", "تويج")),
    ("06_cash_struggle_close.mp4", ("fact1",),
     ("صراع", "معاناة", "مجهود", "تعب", "صمود")),
    ("07_space_warp_cosmic.mp4", ("takeaway", "fact2"),
     ("فضاء", "كون", "نجوم", "مجرة", "كوكب", "مجرة", "سديم")),
    ("08_neon_cyber_grid.mp4", ("fact3", "hook"),
     ("تقنية", "رقمي", "شبكة", "مستقبل", "ذكاء", "روبوت")),
    ("09_lightning_storm_danger.mp4", ("hook",),
     ("برق", "رعد", "عاصفة", "صاعقة", "خطر", "تحذير")),
    ("clip_space_4s.mp4", ("takeaway",),
     ("فضاء", "كون", "نجم")),
]

_VAULT_PROBE: dict[str, float] = {}


def vault_available() -> list[str]:
    """الملفات الموجودة فعليًا في الخزنة."""
    if not VAULT_DIR.exists():
        return []
    return sorted(p.name for p in VAULT_DIR.glob("*.mp4"))


def _vault_duration(name: str) -> float:
    if name not in _VAULT_PROBE:
        _VAULT_PROBE[name] = _probe_dur(VAULT_DIR / name)
    return _VAULT_PROBE[name]


def pick_vault_clip(kind: str, text: str, seed: str,
                    exclude: tuple[str, ...] = ()) -> str | None:
    """اختيار deterministic للقطة الأنسب: نوع المشهد + كلمات النص.

    التعادل في النقاط يتحسم بالـseed. واللقطة المستبعدة (المعروضة في
    القطعة السابقة) بتفتح المجال لبديل غير مستخدم: أولًا لقطة قريبة في
    الصلة (نوع/كلمات)، ثم أي لقطة ذات معنى — عشان القطع كل 2 ثانية
    يبقى فيه تنوع بصري حقيقي بدل تكرار نفس اللقطة.
    """
    present = set(vault_available())
    scored: list[tuple[int, str]] = []
    base_kind = kind if (kind in ("hook", "outro", "takeaway", "cta")
                         or kind.startswith("fact")) else "fact1"
    for fname, kinds, keywords in VAULT_INDEX:
        if fname not in present:
            continue
        score = 2 if base_kind in kinds else 0
        score += sum(1 for k in keywords if k in (text or ""))
        scored.append((score, fname))
    if not scored:
        return None

    def pick(pool: list[str]) -> str:
        idx = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % len(pool)
        return pool[idx]

    best = max(s for s, _ in scored)
    top = [n for s, n in scored if s == best]
    free_top = [n for n in top if n not in exclude]
    if free_top:
        return pick(free_top)
    # اللقطة الأفضل هي نفسها المعروضة في القطعة السابقة → بديل غير مستخدم:
    # أولًا بديل قريب في الصلة، ثم أي لقطة ذات معنى، ثم أي لقطة.
    for tier in ((lambda s, n: n not in exclude and s > 0 and s >= best - 2),
                 (lambda s, n: n not in exclude and s > 0),
                 (lambda s, n: n not in exclude)):
        alt = [n for s, n in scored if tier(s, n)]
        if alt:
            return pick(alt)
    return pick(top)


def prepare_vault_clip(fname: str, seconds: float, out: Path) -> Path | None:
    """لقطة من الخزنة → قطعة بمدة مطلوبة: تكرار سلس + 1080×1920@30 بلا صوت."""
    src = VAULT_DIR / fname
    if not src.exists() or seconds <= 0:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg(), "-y", "-stream_loop", "-1", "-i", str(src),
           "-t", f"{seconds:.3f}",
           "-vf", ("scale=1080:1920:force_original_aspect_ratio=increase,"
                   "crop=1080:1920,fps=30,setsar=1"),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-pix_fmt", "yuv420p", "-an", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists() or out.stat().st_size < 20_000:
        out.unlink(missing_ok=True)
        return None
    return out


def vault_clip(kind: str, text: str, seconds: float, workdir: Path,
               seed: str, exclude: tuple[str, ...] = ()) -> Path | None:
    """الواجهة العامة: لقطة حيّة متحركة مطابقة للمعنى من الخزنة المحلية."""
    fname = pick_vault_clip(kind, text, seed, exclude=exclude)
    if not fname:
        return None
    return prepare_vault_clip(fname, seconds, workdir / fname)


def net_footage_enabled() -> bool:
    """المصادر الشبكية مقفولة افتراضيًا: مفيش وسائط من غير ترخيص موثق."""
    return settings.get("XT_NET_FOOTAGE", "0") == "1"

BAD_TITLES = ("this week", "announce", "briefing", "news", "podcast",
              "interview", "hosted", "narrated", "trailer", "webinar",
              "press", "recap", "episode")


def _dl(url: str, dst: Path) -> bool:
    try:
        if not url:
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=UA, timeout=240, stream=True)
        if not r.ok:
            return False
        n = 0
        with open(dst, "wb") as f:
            for ch in r.iter_content(1 << 16):
                n += len(ch)
                if n > MAX_DL:
                    dst.unlink(missing_ok=True)
                    return False
                f.write(ch)
        return dst.stat().st_size > 50_000
    except Exception:
        return False


def _probe_dur(path: Path) -> float:
    r = subprocess.run([ffmpeg(), "-i", str(path)], capture_output=True,
                       text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", r.stderr)
    if not m:
        return 0.0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def _prep(src: str, seconds: float, out: Path, offset: float = 0.0) -> bool:
    """قص + ضبط 1080×1920@30."""
    cmd = [ffmpeg(), "-y", "-ss", f"{offset:.1f}", "-t", f"{seconds:.2f}",
           "-i", src, "-vf",
           "scale=1080:1920:force_original_aspect_ratio=increase,"
           "crop=1080:1920,fps=30",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-pix_fmt", "yuv420p", "-an", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 30_000


def _has_captions(path: Path) -> bool:
    """نص محروق أبيض/أصفر في أعلى/أسفل اللقطة؟ → مرفوضة."""
    tmp = path.with_suffix(".cap.png")
    try:
        dur = max(2.0, _probe_dur(path))
        for t in (0.4, dur * 0.4, dur * 0.8):
            subprocess.run([ffmpeg(), "-y", "-ss", f"{t:.1f}", "-i", str(path),
                            "-frames:v", "1", str(tmp)],
                           capture_output=True, timeout=30)
            if not tmp.exists():
                continue
            a = np.asarray(Image.open(tmp).convert("RGB"), dtype=int)
            h = a.shape[0]
            for band in (a[0:int(h * 0.13)], a[int(h * 0.78):]):
                frac = ((band[..., 0] > 225) & (band[..., 1] > 175)).mean()
                if frac > 0.02:
                    return True
        return False
    except Exception:
        return True  # فشل الفحص = احتياطًا نرفض
    finally:
        tmp.unlink(missing_ok=True)


def _good_title(title: str) -> bool:
    t = title.lower()
    return not any(b in t for b in BAD_TITLES)


def _relevant(text: str, query: str) -> bool:
    """عنوان اللقطة لازم يشارك الاستعلام كلمة حقيقية — لا وثائقيات عشوائية."""
    t = (text or "").lower()
    words = [w for w in re.split(r"[^a-z]+", query.lower()) if len(w) >= 4]
    return any(w in t for w in words)


def _commons_candidates(query: str) -> list:
    try:
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={"action": "query", "generator": "search",
                    "gsrsearch": f"{query} filetype:video", "gsrnamespace": 6,
                    "gsrlimit": 15, "prop": "imageinfo",
                    "iiprop": "url|mime|size", "format": "json"},
            headers=UA, timeout=20).json()
        pages = (r.get("query") or {}).get("pages") or {}
        out = []
        for p in pages.values():
            ii = (p.get("imageinfo") or [{}])[0]
            if ((ii.get("mime") or "").startswith("video")
                    and 500_000 < ii.get("size", 1 << 30) < MAX_DL
                    and _good_title(p.get("title", ""))
                    and _relevant(p.get("title", ""), query)):
                out.append(ii)
        return sorted(out, key=lambda x: -x.get("size", 0))[:3]
    except Exception:
        return []


def _ia_candidates(query: str) -> list:
    try:
        r = requests.get(
            "https://archive.org/advancedsearch.php",
            params={"q": f"{query} AND mediatype:(movies)",
                    "fl[]": "identifier", "rows": 6, "page": 1,
                    "output": "json"}, headers=UA, timeout=20).json()
        out = []
        for d in r.get("response", {}).get("docs", []):
            if not _good_title(d["identifier"]):
                continue
            meta = requests.get(f"https://archive.org/metadata/{d['identifier']}",
                                headers=UA, timeout=20).json()
            _mt = (meta.get("metadata") or {}).get("title", "")
            if not _relevant(_mt, query) and not _relevant(d["identifier"],
                                                           query):
                continue  # وثائقي عشوائي عن شخص/حدث لا علاقة له بالمشهد
            for f in meta.get("files", []):
                if f["name"].endswith(".mp4") \
                        and 500_000 < int(f.get("size", 1 << 30)) < MAX_DL:
                    out.append({"url": f"https://archive.org/download/"
                                        f"{d['identifier']}/{f['name']}"})
                    break
        return out[:3]
    except Exception:
        return []


def _nasa_candidates(query: str) -> list:
    try:
        r = requests.get(f"{NASA}/search",
                         params={"q": query, "media_type": "video"},
                         headers=UA, timeout=20).json()
        out = []
        for it in r["collection"]["items"][:4]:
            d = it["data"][0]
            if not _good_title(d.get("title", "")) \
                    or not _relevant(d.get("title", ""), query):
                continue
            m = requests.get(
                f"{NASA}/archive/{requests.utils.quote(d['nasa_id'])}",
                headers=UA, timeout=20)
            if not m.ok:
                continue
            vids = [l for l in m.json().get("links", []) if l.endswith(".mp4")]
            if vids:
                out.append({"url": sorted(vids)[0]})
        return out[:3]
    except Exception:
        return []


def fetch_clip(query: str, seconds: float, workdir: Path, seed: str,
               source: str = "auto") -> Path | None:
    """لقطة حيّة مطابقة للمعنى → mp4 مظبوط بلا نص محروق، أو None.

    طبقة شبكية (ويكيميديا/أرشيف الإنترنت/NASA) — مقفولة افتراضيًا
    بقاعدة الترخيص: مش بتشتغل غير لما يكون في كتالوج مصادر موثق
    (docs/MEDIA_VAULT_SOURCES.md) وXT_NET_FOOTAGE=1.
    """
    if not net_footage_enabled():
        return None
    LIB.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{source}:{query}".encode()).hexdigest()[:12]
    cached = LIB / f"{key}.mp4"

    if not cached.exists():
        cands: list = []
        if source in ("auto", "commons"):
            cands += _commons_candidates(query)
        if source in ("auto", "ia"):
            cands += _ia_candidates(query)
        if source in ("auto", "nasa"):
            cands += _nasa_candidates(query)
        raw = workdir / f"raw_{key}.bin"
        bad = _badlist()
        for c in cands:
            url = c.get("url", "")
            if url in bad or not _dl(url, raw):
                continue
            dur = _probe_dur(raw)
            if dur < max(3.0, seconds):
                raw.unlink(missing_ok=True)
                continue
            ok = _prep(str(raw), min(seconds + 1, 12), cached,
                       offset=dur * 0.25)
            if ok and not _has_captions(cached):
                break  # قبلناها
            if ok:
                _mark_bad(url)  # لقطة عليها نص محروق — لن تعود أبدًا
            cached.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)
        _trim_cache()

    if not cached.exists():
        return None
    out = workdir / f"clip_{key}.mp4"
    dur = _probe_dur(cached)
    room = max(1, int(max(0, dur - seconds)))
    off = int(hashlib.sha256(seed.encode()).hexdigest()[:6], 16) % room
    if not _prep(str(cached), seconds, out, offset=off):
        return None
    return out


def _badlist() -> set:
    p = LIB / "_badlist.txt"
    try:
        return set(p.read_text().splitlines()) if p.exists() else set()
    except Exception:
        return set()


def _mark_bad(url: str) -> None:
    p = LIB / "_badlist.txt"
    with open(p, "a") as f:
        f.write(url + "\n")


def _trim_cache() -> None:
    files = sorted(LIB.glob("*.mp4"), key=lambda p: p.stat().st_size)
    total = sum(p.stat().st_size for p in files)
    while total > MAX_LIB_MB * 1024 * 1024 and files:
        p = files.pop(0)
        total -= p.stat().st_size
        p.unlink(missing_ok=True)
