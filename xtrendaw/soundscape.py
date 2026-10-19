"""🌧️ نظام الساوندسكيب الاحترافي — أجواء طبيعية مولّدة 100% (صفر حقوق).

ليه الوحدة دي؟ (قرار صاحب القناة 2026-10-19: «ضيف كل حاجة وكل الأصوات…
كل فيديو غير التاني والأصوات كمان كده»):
    الفيديو الاحترافي على يوتيوب/تيكتوك مش بس صورة + صوت — فيه **طبقة أجواء**
    بتحس بيها (مطر تحت التلاوة، ليل وصَرَّة تحت القصة، عصافير فجر تحت الأذكار).
    دي مش موسيقى — أصوات طبيعة، وقاعدة «صفر موسيقى» للقرآن والأذكار سارية.

الذكاء:
    ١) الأجواء بتتختار **من كلمات المحتوى نفسه** (نار → طرقعة حطب، مطر →
       رذاذ، جنة → عصافير فجر، بحر → أمواج، ليل → صرصرة ونسيم).
    ٢) البذرة بتنوّع التفاصيل (شدة، توزيع، ترددات) ⇒ كل فيديو له بصمة صوتية
       مختلفة حتى لو نفس الجو.
    ٣) كل حاجة بتتولّد رياضيًا هنا (numpy) — مفيش ملف خارجي، مفيش API،
       مفيش حقوق، والرندر ما يقفش أبدًا (أي فشل = بلا أجواء بهدوء).

الأنظمة:
    rain · night · birds · fire · ocean · wind — وSFX تحولات: whoosh وchime.
"""
from __future__ import annotations

import hashlib
import wave
from pathlib import Path

import numpy as np

SR = 22050          # أجواء خلفية — مونو 22k خفيف وسريع حتى للحلقات الطويلة
TAU = 2 * np.pi


def _rng(seed: str) -> np.random.Generator:
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:12], 16)
    return np.random.default_rng(h)


def _norm(x: np.ndarray, peak: float = 0.7) -> np.ndarray:
    m = float(np.max(np.abs(x))) or 1.0
    return (x / m * peak).astype(np.float32)


def _fade(x: np.ndarray, fin: float = 1.5, fout: float = 2.5) -> np.ndarray:
    n = len(x)
    ni = min(n // 2, int(fin * SR))
    no = min(n // 2, int(fout * SR))
    env = np.ones(n, dtype=np.float32)
    if ni:
        env[:ni] = np.linspace(0, 1, ni, dtype=np.float32)
    if no:
        env[-no:] = np.linspace(1, 0, no, dtype=np.float32)
    return x * env


def _write_wav(x: np.ndarray, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(x, -1, 1)
    pcm = (pcm * 32767).astype("<i2")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out


# ─────────────────────────────────────────────────────────────────────
# مولّدات الأجواء (كل واحدة بتاخد مدة + بذرة ⇒ نسخة بصمة مختلفة)
# ─────────────────────────────────────────────────────────────────────
def _rain(dur: float, rng: np.random.Generator) -> np.ndarray:
    """رذاذ: قطرات عشوائية (نبضات قصيرة مفلترة) + همهمة مدارية خفيفة."""
    n = int(dur * SR)
    base = rng.standard_normal(n).astype(np.float32) * 0.028
    # تنعيم بسيط كفلترة منخفضة (متوسط متحرك) ⇒ خشخشة مطر مش ضوضاء حادة
    k = 24
    base = np.convolve(base, np.ones(k, dtype=np.float32) / k, mode="same")
    # قطرات متفرقة أوضح (رعد بعيد ممنوع — إزعاج)
    ndrops = int(dur * 26)
    if ndrops:
        idx = rng.integers(0, max(1, n - 400), ndrops)
        for i in idx[: min(ndrops, 4000)]:
            L = int(rng.integers(60, 200))
            base[i:i + L] += (rng.standard_normal(L).astype(np.float32)
                              * np.exp(-np.linspace(0, 6, L)) * 0.10)
    # تموّج بطيء في الشدة ⇒ إحساس سحابة بتتحرك
    t = np.arange(n) / SR
    swell = 1.0 + 0.22 * np.sin(TAU * t / max(21.0, dur / 3.0)
                                + rng.uniform(0, TAU))
    return _norm(base * swell, 0.62)


def _night(dur: float, rng: np.random.Generator) -> np.ndarray:
    """ليل: صرصرة (قطارات نبضات عالية) + نسيم بني خفيف."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    f = float(rng.uniform(4200, 4800))          # تردد الصرصرة يتنوّع
    # قطارات بطول ~0.25 ثانية بفاصل عشوائي
    pos = 0.0
    while pos < dur - 0.4:
        L = int(0.22 * SR)
        s = int(pos * SR)
        chirp = np.sin(TAU * f * t[:L]).astype(np.float32)
        pulse = (np.sin(TAU * float(rng.uniform(28, 40)) * t[:L]) > 0).astype(np.float32)
        seg = chirp * pulse * np.exp(-np.linspace(0, 1.6, L)) * 0.05
        e = min(n, s + L)
        out[s:e] += seg[: e - s]
        pos += float(rng.uniform(0.55, 1.4))
    # نسيم (بني = تراكمي — أعمق من الأبيض)
    breeze = np.cumsum(rng.standard_normal(n)).astype(np.float32)
    breeze = np.convolve(breeze, np.ones(900, dtype=np.float32) / 900, mode="same")
    out += _norm(breeze, 0.035)
    return _norm(out, 0.5)


def _birds(dur: float, rng: np.random.Generator) -> np.ndarray:
    """فجر: تغريدات FM صاعدة/هابطة متفرقة — الصباح من غير موسيقى."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    nbird = int(dur * float(rng.uniform(0.5, 0.9)))
    for _ in range(min(nbird, 300)):
        s = int(float(rng.uniform(0.2, max(0.3, dur - 0.6))) * SR)
        L = int(float(rng.uniform(0.10, 0.28)) * SR)
        if s + L > n:
            continue
        f0 = float(rng.uniform(2100, 3400))
        f1 = f0 * float(rng.uniform(1.15, 1.6))
        seg_t = t[:L]
        freq = np.linspace(f0, f1, L)
        phase = np.cumsum(TAU * freq / SR)
        chirp = np.sin(phase).astype(np.float32)
        env = np.sin(np.linspace(0, np.pi, L))
        out[s:s + L] += chirp * env * 0.06
    # هواء صباحي خفيف
    air = np.cumsum(rng.standard_normal(n)).astype(np.float32)
    air = np.convolve(air, np.ones(700, dtype=np.float32) / 700, mode="same")
    out += _norm(air, 0.028)
    return _norm(out, 0.5)


def _fire(dur: float, rng: np.random.Generator) -> np.ndarray:
    """طرقعة حطب: فرقعة عشوائية (دلتا منحلة) فوق حرارة مدارية."""
    n = int(dur * SR)
    bed = rng.standard_normal(n).astype(np.float32) * 0.02
    bed = np.convolve(bed, np.ones(60, dtype=np.float32) / 60, mode="same")
    out = bed.copy()
    ncrack = int(dur * float(rng.uniform(6, 11)))
    if ncrack:
        idx = rng.integers(0, max(1, n - 900), min(n * 2, ncrack))
        for i in idx:
            L = int(rng.integers(80, 500))
            amp = float(rng.uniform(0.05, 0.22))
            out[i:i + L] += (rng.standard_normal(L).astype(np.float32)
                             * np.exp(-np.linspace(0, float(rng.uniform(4, 14)), L)) * amp)
    return _norm(out, 0.55)


def _ocean(dur: float, rng: np.random.Generator) -> np.ndarray:
    """أمواج: ضوضاء مفلترة شدة دورية طويلة (موجة تيجي وتمشي)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    raw = np.convolve(rng.standard_normal(n).astype(np.float32),
                      np.ones(500, dtype=np.float32) / 500, mode="same")
    period = float(rng.uniform(9.0, 14.0))
    waves = 0.5 + 0.5 * np.sin(TAU * t / period + rng.uniform(0, TAU))
    out = raw * (0.25 + 0.75 * waves)
    return _norm(out, 0.6)


def _wind(dur: float, rng: np.random.Generator) -> np.ndarray:
    """عاصفة هادئة: ضوضاء بنية + LFO عميق — جوّ جبال/صحراء."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    raw = np.cumsum(rng.standard_normal(n)).astype(np.float32)
    raw = np.convolve(raw, np.ones(1200, dtype=np.float32) / 1200, mode="same")
    gust = 1.0 + 0.5 * np.sin(TAU * t / float(rng.uniform(23, 37))
                              + rng.uniform(0, TAU))
    return _norm(raw * gust, 0.5)


# ─────────────────────────────────────────────────────────────────────
# المؤثرات (تحولات المشاهد)
# ─────────────────────────────────────────────────────────────────────
def _whoosh(rng: np.random.Generator) -> np.ndarray:
    """ووش انتقال: ضوضاء بسويب ترددي صاعد — حركة مونتاج المحترفين."""
    dur = float(rng.uniform(0.45, 0.7))
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0, f1 = 300.0, float(rng.uniform(2600, 4200))
    phase = np.cumsum(TAU * np.linspace(f0, f1, n) / SR)
    swp = np.sin(phase).astype(np.float32)
    noise = rng.standard_normal(n).astype(np.float32)
    k = 40
    noise = np.convolve(noise, np.ones(k, dtype=np.float32) / k, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return _norm((noise * 0.8 + swp * 0.2) * env, 0.65)


def _chime(rng: np.random.Generator) -> np.ndarray:
    """رنة لطيفة للخلاصة/الدعاء الختامي: جيبي + توافقيات متلاشية."""
    dur = 1.8
    n = int(dur * SR)
    t = np.arange(n) / SR
    base = float(rng.uniform(620, 780))
    out = np.zeros(n, dtype=np.float32)
    for h, a in ((1, 1.0), (2, 0.42), (3, 0.18), (5, 0.07)):
        out += np.sin(TAU * base * h * t).astype(np.float32) * a
    out *= np.exp(-t * 2.2)
    attack = int(0.02 * SR)
    out[:attack] *= np.linspace(0, 1, attack)
    return _norm(out, 0.5)


GENERATORS = {
    "rain": _rain, "night": _night, "birds": _birds,
    "fire": _fire, "ocean": _ocean, "wind": _wind,
}

# كلمات المحتوى ← الجو (الذكاء: الجو من معنى النص مش عشوائي)
KEYWORD_MAP: list[tuple[str, tuple[str, ...]]] = [
    ("fire", ("نار", "جهنم", "حريق", "لهب", "جحيم", "يحترق", "حمم")),
    ("birds", ("جنة", "فجر", "صباح", "أذكار الصباح", "أمل", "فرج", "ربيع",
               "طبيعة", "حديقة", "غابة")),
    ("ocean", ("بحر", "موج", "غرق", "سفينة", "يونس", "كوثر", "نهر", "ماء")),
    ("rain", ("مطر", "سحاب", "رحمة", "غيث", "سقيا", "دعاء", "سجود", "تلاوة",
              "قرآن", "رحمن")),
    ("night", ("ليل", "قمر", "نجوم", "ظر", "سحر", "تهجد", "قيام", "قصة",
               "قصص", "حكاية", "غار")),
    ("wind", ("صحراء", "جبل", "عاصفة", "ريح", "رمل", "هجرة", "سفر", "فضاء")),
]

# نوع المحتوى ← جو افتراضي لو مفيش كلمة مطابقة
KIND_MAP = {
    "quran": "rain", "ayat": "rain", "tafsir": "rain", "tilawa": "rain",
    "dua": "rain", "athkar": "birds", "adhkar": "birds", "sbh": "birds",
    "qissa": "night", "story": "night", "seerah": "night",
    "asma": "birds", "asmaa": "birds",
    "facts": "wind", "mujiza": "wind", "miracle": "wind",
    "hadith": "night",
}

# مستوى الأجواء تحت الصوت (رقم صغير جدًا — إحساس مش طبقة تغطي)
LEVEL_DEFAULT = 0.045
LEVEL_QURAN = 0.030        # التلاوة والدعاء: أخف درجة (وقار)
_QURAN_KINDS = {"quran", "ayat", "tafsir", "tilawa", "dua", "athkar", "adhkar"}


def pick_ambience(episode: dict) -> str:
    """الجو المناسب للحلقة: كلمات النص أولًا، ثم نوعه، وأخيرًا بذرة متنوعة."""
    text = " ".join(str(episode.get(f, "")) for f in
                    ("title", "hook", "body", "text", "desc", "description"))
    tid = str(episode.get("id") or episode.get("title") or "")
    for amb, keys in KEYWORD_MAP:
        if any(k in text for k in keys):
            return amb
    kind = str(episode.get("kind") or episode.get("plan_kind") or "").lower()
    if kind in KIND_MAP:
        return KIND_MAP[kind]
    keys = sorted(GENERATORS)
    return keys[int(hashlib.sha256((tid + "amb").encode()).hexdigest()[:6], 16)
                % len(keys)]


def ambience_wav(kind: str, dur: float, seed: str, out_dir: Path) -> Path | None:
    """جو كامل بمدة الحلقة → wav مونو خفيف، أو None بأمان."""
    gen = GENERATORS.get(kind)
    if gen is None or dur < 3:
        return None
    try:
        rng = _rng(f"{kind}:{seed}")
        audio = _fade(gen(dur + 0.5, rng), fin=1.2, fout=min(3.0, dur / 4))
        return _write_wav(audio, out_dir / f"amb_{kind}.wav")
    except Exception as exc:  # noqa: BLE001 — تجميل، المصنع ما يقفش عليه
        print(f"[soundscape] ⚠ الجو «{kind}» اتخطى: {type(exc).__name__}",
              flush=True)
        return None


def sfx_wav(name: str, seed: str, out_dir: Path) -> Path | None:
    """مؤثر تحول (whoosh/chime) → wav، أو None بأمان."""
    try:
        rng = _rng(f"sfx:{name}:{seed}")
        audio = _whoosh(rng) if name == "whoosh" else _chime(rng)
        return _write_wav(audio, out_dir / f"sfx_{name}.wav")
    except Exception:  # noqa: BLE001
        return None


def level_for(episode: dict) -> float:
    kind = str(episode.get("kind") or episode.get("plan_kind") or "").lower()
    return LEVEL_QURAN if kind in _QURAN_KINDS else LEVEL_DEFAULT


def describe(episode: dict) -> str:
    """سطر اعتماد للوصف تحت Credits: — شفافية الاستوديو الحقيقي."""
    amb = pick_ambience(episode)
    ar = {"rain": "مطر", "night": "ليل وصرصرة", "birds": "عصافير فجر",
          "fire": "طرقعة حطب", "ocean": "أمواج بحر", "wind": "نسيم"}.get(amb, amb)
    return f"أجواء طبيعية مولّدة داخليًا: {ar} (بلا حقوق)"
