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
    ("10_ocean_deep_waves.mp4", ("fact2", "takeaway"),
     ("بحر", "محيط", "موجة", "موج", "ماء", "مياة", "مياه", "غرق", "سباحة",
      "عمق", "أعماق")),
    ("11_desert_dunes_gold.mp4", ("fact1", "fact3"),
     ("صحراء", "رمل", "رمال", "جمل", "واحة", "عطش", "حر", "شمس", "قيظ")),
    ("12_gold_treasure_rain.mp4", ("fact1", "cta"),
     ("ذهب", "كنز", "ثروة", "كنوز", "ثمين", "غني", "ثري", "معدن")),
    ("13_green_energy_pulse.mp4", ("fact3", "takeaway"),
     ("طاقة", "كهرباء", "نبض", "قوة", "حيوية", "بيئة", "أخضر", "شحن")),
    ("14_lava_embers_flow.mp4", ("hook", "fact2"),
     ("حمم", "بركان", "جمر", "لهب", "انفجار", "حرارة", "نيران")),
    ("15_blue_city_nights.mp4", ("fact3", "takeaway"),
     ("مدينة", "مدن", "شارع", "شوارع", "أضواء", "ليل", "زحام", "عاصمة",
      "ناطحات")),
    ("16_red_alert_siren.mp4", ("hook",),
     ("إنذار", "خطر", "تحذير", "طوارئ", "كارثة", "فخ", "ممنوع")),
    ("17_purple_galaxy_swirl.mp4", ("takeaway", "fact2"),
     ("مجرة", "سديم", "درب التبانة", "ثقوب", "ثقب أسود")),
    ("18_aurora_night_sky.mp4", ("fact2", "outro"),
     ("سماء", "ليل", "شفق", "نجوم", "قطب", "قمر")),
    ("19_bronze_gears_machine.mp4", ("fact1", "fact3"),
     ("آلة", "تروس", "مصنع", "صناعة", "اختراع", "ميكانيكا", "محرك",
      "ساعة")),
    ("20_white_light_reveal.mp4", ("takeaway", "cta"),
     ("كشف", "سر", "حقيقة", "نور", "إعلان", "اكتشاف", "ظهور")),
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
                    exclude: tuple[str, ...] = (),
                    used: dict[str, int] | None = None,
                    max_uses: int = 2) -> str | None:
    """اختيار deterministic للقطة الأنسب: نوع المشهد + كلمات النص.

    القواعد بالترتيب:
      ١) اللقطة الأقوى صلة (نوع + كلمات) اللي لسه ما اتعرضتش مرتين
         ومش معروضة في القطعة السابقة.
      ٢) لو خلاص، أي لقطة ذات معنى تحت سقف الاستخدام.
      ٣) سقف الاستخدام اتستنفد في الخزنة كلها → نسمح بإعادة الاستخدام
         (الأقوى صلة أولًا) بدل ما المشهد يفضل بلا لقطة.
    """
    used = used or {}
    present = set(vault_available())
    # استبعاد أي لقطة ظهرت في حلقة سابقة (ذاكرة الوسائط المحفوظة على git)
    try:
        from . import state as _state
        _seen = _state.media_used()
        fresh = {n for n in present if f"vault:{n}" not in _seen}
        if fresh:
            present = fresh
    except Exception:
        pass
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

    def under_cap(n: str) -> bool:
        return used.get(n, 0) < max_uses

    def pick_least_used(pool: list[str]) -> str:
        # عند استنفاد السقف: نوزع على الأقل استخدامًا عشان ما تتكررش لقطة
        # 5 مرات وزميلتها مرة — الاتزان أهم من الصلة هنا.
        least = min(used.get(n, 0) for n in pool)
        return pick([n for n in pool if used.get(n, 0) == least])

    best = max(s for s, _ in scored)
    for pool in (
        [n for s, n in scored if s == best and n not in exclude and under_cap(n)],
        [n for s, n in scored if s > 0 and n not in exclude and under_cap(n)],
        [n for s, n in scored if n not in exclude and under_cap(n)],
    ):
        if pool:
            return pick(pool)
    # السقف اتستنفد في الخزنة كلها → الأقل استخدامًا (مع استبعاد القطعة
    # السابقة لو فيه بدائل)، مش الأقوى صلة اللي هيتحرق تكرارًا.
    pool = [n for _, n in scored if n not in exclude] or [n for _, n in scored]
    return pick_least_used(pool)


def prepare_vault_clip(fname: str, seconds: float, out: Path) -> Path | None:
    """لقطة من الخزنة → قطعة بمدة مطلوبة: تكرار سلس + 1080×1920@30 بلا صوت.

    حارس الترخيص (بند 0/4): اللقطة لازم تكون مسجلة في `vault/index.json`
    وإلا فشل صريح — مفيش أصل بيرندَر من غير سجل ترخيص.
    """
    from . import vault

    src = VAULT_DIR / fname
    if not src.exists() or seconds <= 0:
        return None
    vault.require_license(src)
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
               seed: str, exclude: tuple[str, ...] = (),
               used: dict[str, int] | None = None) -> Path | None:
    """الواجهة العامة: لقطة متحركة مطابقة للمعنى من الخزنة المحلية المرخّصة."""
    if not settings.ALLOW_STATIC_VAULT:
        print("[footage] ⛔ المخزون الثابت (صور تجربة) مقفول — "
              "بنكمل من المصادر الشبكية/المولّدة بس", flush=True)
        return None
    fname = pick_vault_clip(kind, text, seed, exclude=exclude, used=used)
    if not fname:
        return None
    return prepare_vault_clip(fname, seconds, workdir / fname)


def clip_origin(path: Path | None) -> Path | None:
    """الأصل المسجل في الفهرس وراء قطعة معادة التحضير (للاعتبارات)."""
    if path is None:
        return None
    src = VAULT_DIR / path.name
    return src if src.exists() else path


def net_footage_enabled() -> bool:
    """المصادر الشبكية مفعلة افتراضيًا؛ القيمة 0 هي مفتاح الإيقاف الصريح."""
    return settings.get("XT_NET_FOOTAGE", "1") == "1"

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
                    "iiprop": "url|mime|size|extmetadata",
                    "format": "json"},
            headers=UA, timeout=20).json()
        pages = (r.get("query") or {}).get("pages") or {}
        out = []
        for p in pages.values():
            ii = (p.get("imageinfo") or [{}])[0]
            lic = _commons_license(ii.get("extmetadata") or {})
            if ((ii.get("mime") or "").startswith("video")
                    and 500_000 < ii.get("size", 1 << 30) < MAX_DL
                    and lic is not None
                    and _good_title(p.get("title", ""))
                    and _relevant(p.get("title", ""), query)):
                ii["_license"] = lic
                ii["_title"] = p.get("title", "")
                ii["_source"] = "Wikimedia Commons"
                out.append(ii)
        return sorted(out, key=lambda x: -x.get("size", 0))[:3]
    except Exception:
        return []


def _commons_license(extmeta: dict) -> str | None:
    """رخصة ويكيميديا الفعلية للملف — غير المسموح بيتهمل بالكامل."""
    short = ((extmeta.get("LicenseShortName") or {}).get("value") or "").strip()
    name = ((extmeta.get("License") or {}).get("value") or "").strip().lower()
    artist = ((extmeta.get("Artist") or {}).get("value") or "")
    artist = re.sub(r"<[^>]+>", "", artist).strip()
    s = short.lower()
    if s in ("cc0", "cc-0") or "zero" in s or name == "public domain":
        return "CC0"
    if s.startswith("cc by-sa 4") or s == "cc by-sa 4.0":
        return "CC-BY-SA-4.0"
    if s.startswith("cc by 4") or s == "cc by 4.0":
        return "CC-BY-4.0"
    if s.startswith("cc by 3") or s == "cc by 3.0":
        return "CC-BY-3.0"
    return None  # أي رخصة تانية (NC/مخصصة/مش واضحة) → مرفوضة


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
            lic = _ia_license(meta.get("metadata") or {})
            if lic is None:
                continue  # رخصة مش مسموحة أو مش واضحة → مرفوضة
            for f in meta.get("files", []):
                if f["name"].endswith(".mp4") \
                        and 500_000 < int(f.get("size", 1 << 30)) < MAX_DL:
                    out.append({"url": f"https://archive.org/download/"
                                        f"{d['identifier']}/{f['name']}",
                                "_license": lic, "_title": d["identifier"],
                                "_source": "Internet Archive"})
                    break
        return out[:3]
    except Exception:
        return []


def _ia_license(meta: dict) -> str | None:
    """رخصة أرشيف الإنترنت من صفحة العنصر — غير المسموح بيتهمل."""
    url = (meta.get("licenseurl") or "").lower()
    if "creativecommons.org/publicdomain" in url or "cc0" in url:
        return "CC0"
    if "creativecommons.org/licenses/by-sa/4" in url:
        return "CC-BY-SA-4.0"
    if "creativecommons.org/licenses/by/4" in url:
        return "CC-BY-4.0"
    if "creativecommons.org/licenses/by/3" in url:
        return "CC-BY-3.0"
    return None


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
                # NASA Media Usage: حر مع قيود ترويجية بس — مسموح في الفهرس
                out.append({"url": sorted(vids)[0],
                            "_license": "NASA-Media-Usage",
                            "_title": d.get("title", d["nasa_id"]),
                            "_source": "NASA"})
        return out[:3]
    except Exception:
        return []


def _pixabay_candidates(query: str) -> list:
    """Pixabay Videos API — رخصة Pixabay (بلا إسناد). محتاج `PIXABAY_API_KEY`."""
    key = settings.PIXABAY_API_KEY
    if not key or not query:
        return []
    try:
        r = requests.get("https://pixabay.com/api/videos/",
                         params={"key": key, "q": query, "per_page": 8,
                                 "safesearch": "true"},
                         headers=UA, timeout=25)
        if not r.ok:
            return []
        out = []
        for h in r.json().get("hits", []):
            vids = h.get("videos") or {}
            # medium ≈ 1280 بكسل — كفاية لـ1080 وأخف من large
            f = vids.get("medium") or vids.get("small") or vids.get("tiny")
            if not f or not f.get("url"):
                continue
            out.append({
                "url": f["url"],
                "_license": "Pixabay-License",
                "_source": "pixabay",
                "_title": f"Pixabay user {h.get('user', 'unknown')}",
            })
        return out
    except Exception:
        return []


def _pexels_candidates(query: str) -> list:
    """Pexels Videos API — رخصة Pexels (بلا إسناد). محتاج `PEXELS_API_KEY`."""
    key = settings.PEXELS_API_KEY
    if not key or not query:
        return []
    try:
        r = requests.get("https://api.pexels.com/videos/search",
                         params={"query": query, "per_page": 8, "size": "medium"},
                         headers={**UA, "Authorization": key}, timeout=25)
        if not r.ok:
            return []
        out = []
        for v in r.json().get("videos", []):
            files = sorted((f for f in v.get("video_files", [])
                            if f.get("link") and (f.get("width") or 0) >= 640),
                           key=lambda f: f.get("width") or 0)
            if not files:
                continue
            out.append({
                "url": files[0]["link"],
                "_license": "Pexels-License",
                "_source": "pexels",
                "_title": f"Pexels video #{v.get('id', '?')}",
            })
        return out
    except Exception:
        return []


def fetch_clip(query: str, seconds: float, workdir: Path, seed: str,
               source: str = "auto") -> Path | None:
    """لقطة حيّة مطابقة للمعنى → mp4 مظبوط بلا نص محروق، أو None.

    طبقة شبكية (بيكساباي/بكسلز/ويكيميديا/أرشيف الإنترنت/NASA) — مقفولة
    افتراضيًا بقاعدة الترخيص: مش بتشتغل غير لما يكون في كتالوج مصادر موثق
    (docs/MEDIA_VAULT_SOURCES.md) وXT_NET_FOOTAGE=1.
    ترتيب السلسلة زي البلوبرنت: بيكساباي ← بكسلز ← كومنز ← الأرشيف ← ناسا.
    """
    if not net_footage_enabled():
        return None
    LIB.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{source}:{query}".encode()).hexdigest()[:12]
    cached = LIB / f"{key}.mp4"

    # ⚠️ الكاش لوحده بيخلّي نفس اللقطة تظهر في حلقة تانية (شكوى المستخدم:
    # «نفس الصور في 4 فيديوهات»). فلازم نتأكد إن نسخة الكاش دي ما استُخدمتش
    # قبل كده — لو استُخدمت، بنتجاهلها ونجيب لقطة جديدة من الشبكة.
    try:
        from . import state as _st
        if cached.exists() and _st.media_seen(f"clipcache:{key}"):
            print("[footage] ↺ الكاش ده استُخدم في حلقة قبل كده — "
                  "بجيب لقطة جديدة", flush=True)
            cached = workdir / f"clip_{key}.mp4"
    except Exception:
        pass

    if not cached.exists():
        cands: list = []
        if source in ("auto", "pixabay"):
            cands += _pixabay_candidates(query)
        if source in ("auto", "pexels"):
            cands += _pexels_candidates(query)
        if source in ("auto", "commons"):
            cands += _commons_candidates(query)
        if source in ("auto", "ia"):
            cands += _ia_candidates(query)
        if source in ("auto", "nasa"):
            cands += _nasa_candidates(query)
        raw = workdir / f"raw_{key}.bin"
        bad = _badlist()
        # ذاكرة الوسائط: اللقطة اللي ظهرت في حلقة قبل كده مش بتتكرر
        try:
            from . import state as _state
            _seen_media = _state.media_used()
        except Exception:
            _seen_media = {}
        accepted = None
        for c in cands:
            url = c.get("url", "")
            if url in _seen_media:
                print(f"[footage] ↺ استبعدت لقطة مستخدمة قبل كده "
                      f"({c.get('_source', 'web')}) — بدور على غيرها", flush=True)
                continue
            if url in bad or not _dl(url, raw):
                continue
            dur = _probe_dur(raw)
            if dur < max(3.0, seconds):
                raw.unlink(missing_ok=True)
                continue
            ok = _prep(str(raw), min(seconds + 1, 12), cached,
                       offset=dur * 0.25)
            if ok and not _has_captions(cached):
                accepted = c  # قبلناها
                break
            if ok:
                _mark_bad(url)  # لقطة عليها نص محروق — لن تعود أبدًا
            cached.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)
        _trim_cache()
        if accepted is not None:
            # سجل الترخيص إلزامي قبل ما اللقطة تتاح لأي رندر (بند 0/4)
            from . import vault
            lic = accepted.get("_license") or ""
            # لا نساوي «مجاني للاستخدام» بـ CC: Pixabay/Pexels/NASA وCC-SA
            # تُرفض هنا ما لم تُرجع الواجهة CC0 أو CC-BY صريحة.
            if lic not in vault.ALLOWED_NETWORK_LICENSES:
                cached.unlink(missing_ok=True)
            else:
                attribution = lic.startswith("CC-BY")
                credit = ""
                if attribution:
                    who = (accepted.get("_title") or accepted.get("url", ""))
                    credit = f"Footage: {who} via {accepted.get('_source', 'web')}, {lic}"
                vault.register(cached, source=accepted.get("_source", "web"),
                               license=lic, attribution_required=attribution,
                               credit_line=credit, url=accepted.get("url", ""))
                print(f"[footage] 🎞 مصدر شبكي: {accepted.get('_source', 'web')} "
                      f"· رخصة {lic} · {str(accepted.get('_title', ''))[:70]}",
                      flush=True)
                try:
                    from . import state as _state
                    _state.mark_media_used(
                        accepted.get("url", ""),
                        f"video:{accepted.get('_source', 'web')}",
                        str(seed).split(":")[0])
                    _state.mark_media_used(f"clipcache:{key}",
                                           f"video:{accepted.get('_source', 'web')}",
                                           str(seed).split(":")[0])
                except Exception:
                    pass

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
