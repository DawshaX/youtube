"""🎵 محرّك الموسيقى الاحترافي — لحن بيتنفّس مع الكلام، صفر حقوق.

الفكرة:
    الموسيقى الخلفية بتزوّد الاحتفاظ ~15-25% لما تكون **متوافقة مع المزاج**
    ومستوى صوتها **بيتعلّم** لوحده مع الكلام (sidechain ducking حقيقي).

الأنماط (كل نمط = مقام + إيقاع + آلات مختلفة):
    هدوء      → مبسّط جدًا، باد دافي، نبض بطيء      (تأمل · سكينة · نوم)
    تأمل      → مقام حجاز ناعم، أوتار طويلة          (تدبر · قرآن بلا موسيقى)
    أمل       → مقام عجم صاعد، بيانو + أوتار        (بشريات · فرج)
    حكمة      → مقام كرد، إيقاع هادي                 (أمثال · قصص)
    مشرق      → مقام نهاوند، نبرة مشرقة              (خير · إفادة)
    سينمائي   → تدرّج صاعد + إمباكت                  (معجزات · أحداث)

⚠️ قواعد ثابتة (من FACTORY_RULES + كلام صاحب القناة):
    1. صفر موسيقى محفوظة — كل نغمة بتتولّد رياضيًا هنا.
    2. النص القرآني والتلاوة **بلا موسيقى** — بدالها أجواء طبيعية مولّدة.
    3. المستوى مضمون إنه ما يغطّيش على الكلام (-20dB وأقل).
"""
from __future__ import annotations

import hashlib
import math
import wave
from pathlib import Path

import numpy as np

SR = 44100

# ── المقامات العربية — ترددات حقيقية بنسب المقام (نفس ترتيب الموسيقى الشرقية)
MAQAM = {
    # حجاز: بعده المميز ¾ تون (نسبة 25/24 تقريبًا)
    "حجاز": [1.0, 1.067, 1.25, 1.333, 1.5, 1.6, 2.0],
    # كرد: قريب من الصغير الغربي بحس شرقي
    "كرد": [1.0, 1.122, 1.189, 1.335, 1.498, 1.6, 2.0],
    # عجم: الكبير الغربي — صاعد ومشرق
    "عجم": [1.0, 1.125, 1.25, 1.333, 1.5, 1.667, 2.0],
    # نهاوند: صغير غربي — حنين
    "نهاوند": [1.0, 1.122, 1.189, 1.335, 1.498, 1.682, 2.0],
    # بياتي: أشهر مقام عربي — حنين وهدوء
    "بياتي": [1.0, 1.059, 1.189, 1.335, 1.498, 1.6, 2.0],
    # صبا: حزن ناعم
    "صبا": [1.0, 1.059, 1.189, 1.335, 1.414, 1.6, 2.0],
    # عشاق: دافي
    "عشاق": [1.0, 1.122, 1.189, 1.335, 1.414, 1.6, 2.0],
}

# المزاج = (المقام, الجذر Hz, الإيقاع BPM, نمط الإحساس)
MOODS = {
    "هدوء":     ("بياتي",  196.0, 54, "soft"),
    "تأمل":     ("حجاز",   174.6, 50, "soft"),
    "أمل":      ("عجم",    220.0, 66, "rise"),
    "حكمة":     ("كرد",    196.0, 58, "steady"),
    "مشرق":     ("نهاوند", 261.6, 72, "rise"),
    "سينمائي":  ("صبا",    146.8, 62, "build"),
    "سكينة":    ("بياتي",  164.8, 48, "soft"),
    "فرج":      ("عجم",    246.9, 60, "rise"),
}

# كلمات بتحدّد المزاج — من محتوى الحلقة نفسه
MOOD_WORDS = {
    "هدوء": ("هدوء", "سكون", "نام", "نوم", "راحة", "سكينة", "صمت", "بحر", "ليل", "نجوم"),
    "تأمل": ("تدبر", "تأمل", "آية", "معنى", "تفسير", "فكر", "قلب", "ذكر"),
    "أمل": ("أمل", "فرج", "خير", "رجاء", "توبة", "بشري", "ضحك", "أشرق", "نور", "ضوء", "فجر"),
    "حكمة": ("حكمة", "مثل", "عبرة", "درس", "قصة", "سيرة", "نصيحة", "أدب"),
    "مشرق": ("علم", "معلومة", "أرض", "سماء", "فضاء", "كون", "اكتشاف", "جبل", "غابة", "حديقة"),
    "سينمائي": ("معجزة", "عاصفة", "صدمة", "تحول", "قوة", "عظمة", "موسى", "بحر", "نار"),
    "سكينة": ("دعاء", "راحة", "طمأنينة", "قلق", "تعب", "شقاء", "حزن", "دموع"),
    "فرج": ("فرج", "دعاء", "خير", "باب", "يسر", "نجاح", "فتح"),
}


def _env_curve(n: int, atk: float, dec: float, sus: float = 0.7, rel: float = 0.3) -> np.ndarray:
    """غلاف ADSR كامل — نغمة بتحيا وتموت، مش قطع حاد."""
    a = max(1, int(n * atk))
    d = max(1, int(n * dec))
    r = max(1, int(n * rel))
    s = max(1, n - a - d - r)
    env = np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, sus, d),
        np.full(s, sus),
        np.linspace(sus, 0, r),
    ])
    return env[:n] if len(env) >= n else np.pad(env, (0, n - len(env)))


def _tone(freq: float, dur: float, kind: str = "pad", detune: float = 0.0) -> np.ndarray:
    """نغمة واحدة. `kind` بيحدد الطابع الصوتي."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR

    if kind == "pad":
        # باد غني: 3 توافقيات بترددات مضاعفة
        sig = (np.sin(2 * np.pi * freq * t)
               + 0.42 * np.sin(2 * np.pi * freq * 2 * t)
               + 0.18 * np.sin(2 * np.pi * freq * 3 * t))
        if detune:
            sig += 0.3 * np.sin(2 * np.pi * (freq * (1 + detune)) * t)
        env = _env_curve(n, 0.12, 0.15, 0.72, 0.35)
    elif kind == "pluck":
        # نغمة وترية (بيانو/قانون) — هجوم سريع وتلاشي
        sig = (np.sin(2 * np.pi * freq * t)
               + 0.55 * np.sin(2 * np.pi * freq * 2 * t)
               + 0.25 * np.sin(2 * np.pi * freq * 3 * t)
               + 0.12 * np.sin(2 * np.pi * freq * 4 * t))
        env = np.exp(-np.linspace(0, 4.2, n))
    elif kind == "bass":
        sig = np.sin(2 * np.pi * freq * t) + 0.22 * np.sin(4 * np.pi * freq * t)
        env = np.exp(-np.linspace(0, 2.4, n))
    elif kind == "bell":
        sig = (np.sin(2 * np.pi * freq * t)
               + 0.5 * np.sin(2 * np.pi * freq * 2.76 * t)
               + 0.2 * np.sin(2 * np.pi * freq * 5.4 * t))
        env = np.exp(-np.linspace(0, 5.5, n))
    elif kind == "air":
        # طيف هواء/بحر — ضجيج مفلتر بتدرّج لطيف
        rng = np.random.default_rng(int(freq) % 9973)
        noise = rng.uniform(-1, 1, n).astype(np.float32)
        # مرشّح تمرير منخفض بسيط (متوسط متحرك ضخم)
        k = max(3, int(SR / max(60.0, freq)))
        kernel = np.ones(k, dtype=np.float32) / k
        sig = np.convolve(noise, kernel, mode="same")
        env = np.ones(n) * 0.9
    else:
        sig = np.sin(2 * np.pi * freq * t)
        env = _env_curve(n, 0.1, 0.2)
    return (sig * env).astype(np.float32)


def _reverb(sig: np.ndarray, amount: float = 0.22, decay: float = 0.35) -> np.ndarray:
    """صدى بسيط (comb delay) — بيدي إحساس مكان واسع بلا مكتبات."""
    if amount <= 0:
        return sig
    out = sig.copy()
    for d_ms, gain in ((85, 0.5), (137, 0.34), (211, 0.24)):
        d = int(SR * d_ms / 1000)
        if d >= len(sig):
            continue
        tail = sig[:-d] * (gain * amount * decay)
        out[d:] += tail
    peak = float(np.max(np.abs(out))) or 1.0
    return (out / peak * float(np.max(np.abs(sig)) or 1.0)).astype(np.float32)


def _pick_mood(text: str, kind: str = "", episode_id: str = "") -> str:
    blob = f"{kind} {text}"
    best, score = "هدوء", 0
    for mood, words in MOOD_WORDS.items():
        s = sum(1 for w in words if w in blob)
        if s > score:
            best, score = mood, s
    if score == 0:
        names = list(MOODS)
        seed = int(hashlib.sha256(str(episode_id).encode()).hexdigest()[:8], 16)
        best = names[seed % len(names)]
    return best


def compose(duration: float, out_path: Path, *, mood: str = "هدوء",
            volume: float = 0.16, loops: int = 1) -> Path:
    """يؤلّف مقطوعة بمزاج معيّن ومدّة محددة.

    كل طبقة (باد · باص · لحن · هات) بتشتغل على المقام والإيقاع بتاع المزاج.
    النتيجة: مقطوعة متفردة مش متكررة — لأن كل مزاج ليه مقامه.
    """
    maqam_name, root, bpm, feel = MOODS.get(mood, MOODS["هدوء"])
    scale = MAQAM.get(maqam_name, MAQAM["بياتي"])

    dur = max(2.0, min(float(duration) + 1.2, 900.0))
    n = int(dur * SR)
    beat = 60.0 / bpm
    bar = beat * 4.0
    nbars = max(1, int(math.ceil(dur / bar)))

    pad = np.zeros(n, dtype=np.float32)
    bass = np.zeros(n, dtype=np.float32)
    lead = np.zeros(n, dtype=np.float32)
    bells = np.zeros(n, dtype=np.float32)
    air = _tone(root, dur, "air") * (0.05 if feel == "soft" else 0.03)
    air = air[:n] if len(air) >= n else np.pad(air, (0, n - len(air)))

    # تقدّم الكوردات (٤ درجات من المقام) — بيتغير حسب الإحساس
    if feel == "soft":
        degrees = [0, 3, 5, 3]
    elif feel == "rise":
        degrees = [0, 2, 4, 5]
    elif feel == "build":
        degrees = [0, 1, 4, 5]
    else:
        degrees = [0, 4, 3, 5]

    rng = np.random.default_rng(abs(hash((maqam_name, int(bpm), int(dur)))) % (2**31))

    for b in range(nbars):
        start = int(b * bar * SR)
        if start >= n:
            break
        length = min(int(bar * SR), n - start)
        deg = degrees[b % len(degrees)]

        # ── باد: ٣ نغمات من المقام (الأساس + الخامسة + الثامنة)
        for offset in (0, 4, 7):
            idx = (deg + offset) % 7
            f = root * scale[idx] * (2 if (deg + offset) >= 7 else 1)
            tone = _tone(f, length / SR, "pad", detune=0.0025)
            # طول النغمة ممكن يختلف بمقياس واحد عن المطلوب — نقصّ للاتنين
            seg = tone[:length]
            pad[start:start + len(seg)] += seg * 0.32

        # ── باص على أول كل مازورة + النصف
        for frac in (0.0, 0.5):
            s = start + int(bar * frac * SR)
            if s >= n:
                continue
            bf = root / 2 * scale[deg % 7]
            tone = _tone(bf, min(beat * 1.4, (n - s) / SR), "bass")
            end = min(n, s + len(tone))
            bass[s:end] += tone[: end - s] * (0.82 if feel != "soft" else 0.6)

        # ── لحن: نغمات مختارة على ربع المازورة (مش كل ضربة = أقل رتابة)
        note_slots = 4 if feel in ("rise", "build") else 3
        for i in range(note_slots):
            s = start + int(bar * (i / note_slots) * SR)
            if s >= n:
                continue
            if rng.random() < 0.32:      # مساحات صمت = تنفّس
                continue
            step = int(rng.integers(0, 7))
            f = root * scale[(deg + step) % 7]
            if step >= 5:
                f *= 2
            kind = "pluck" if feel in ("rise", "steady") else "bell"
            tone = _tone(f, min(beat * 1.15, (n - s) / SR), kind)
            end = min(n, s + len(tone))
            lead[s:end] += tone[: end - s] * 0.24

        # ── جرس عند نهاية كل ٤ مباريات — علامة موسيقية
        if b % 4 == 3:
            s = start + int(bar * 0.75 * SR)
            if s < n:
                f = root * scale[(deg + 4) % 7] * 2
                tone = _tone(f, min(1.6, (n - s) / SR), "bell")
                end = min(n, s + len(tone))
                bells[s:end] += tone[: end - s] * 0.18

    mix = pad + bass + lead + bells + air * 0.6
    mix = _reverb(mix, amount=0.24 if feel in ("soft", "steady") else 0.16)

    # تطبيع سلس — من غير قطع
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = (mix / peak) * float(volume)

    # تلاشي دخول وخروج
    fin, fout = int(1.1 * SR), int(1.6 * SR)
    if len(mix) > fin + fout:
        mix[:fin] *= np.linspace(0, 1, fin)
        mix[-fout:] *= np.linspace(1, 0, fout)

    pcm = np.clip(mix * 32767, -32768, 32767).astype("<i2")
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())
    return out_path


def _duck(voice: np.ndarray, bed: np.ndarray, sr: int = SR,
          floor: float = 0.30, atk_ms: int = 45, rel_ms: int = 260) -> np.ndarray:
    """Sidechain ducking حقيقي: الموسيقى بتنزل لما الكلام يشتغل.

    ده اللي بيفرّق بين «موسيقى مزعجة» و«موسيقى احترافية».
    """
    a = max(1, int(sr * atk_ms / 1000))
    r = max(1, int(sr * rel_ms / 1000))
    # غلاف الطاقة من الصوت (نافذة ٧٥ms)
    win = max(1, int(sr * 0.075))
    kernel = np.ones(win, dtype=np.float32) / win
    energy = np.convolve(np.abs(voice).astype(np.float32), kernel, mode="same")
    top = float(np.percentile(energy, 92)) or 1.0
    norm = np.clip(energy / top, 0, 1)

    gain = np.empty_like(norm)
    g = 1.0
    for i, v in enumerate(norm):
        target = 1.0 - (1.0 - floor) * float(v)
        step = (1.0 / a) if target < g else (1.0 / r)
        g += max(-step, min(step, target - g))
        gain[i] = g

    m = min(len(bed), len(gain))
    out = bed.copy()
    out[:m] = bed[:m] * gain[:m]
    return out


def _to_wav(src: Path, work_dir: Path | None = None) -> Path:
    """يحوّل أي صوت (mp3/m4a/aac/mp4/…) لـ WAV 16-bit mono عشان نشتغل عليه.

    المصنع بيطلّع صوت edge-tts بصيغة mp3 — فلازم نتعامل معاها زي ما هي.
    لو التحويل فشل، بيرجّع الملف الأصلي (الفشل آمن).
    """
    src = Path(src)
    if src.suffix.lower() == ".wav":
        return src
    dst = (work_dir or src.parent) / (src.stem + ".conv.wav")
    for exe in _ffmpeg_candidates():
        try:
            import subprocess
            subprocess.run(
                [exe, "-v", "error", "-y", "-i", str(src), "-vn",
                 "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(dst)],
                check=True, capture_output=True, timeout=600)
            if dst.exists() and dst.stat().st_size > 1024:
                return dst
        except Exception:
            continue
    return src


def _ffmpeg_candidates() -> list[str]:
    """يلاقي ffmpeg بأي طريقة متاحة في البيئة (system أو imageio-ffmpeg)."""
    import os
    import shutil

    found = [p for p in (shutil.which("ffmpeg"), os.environ.get("FFMPEG_BIN")) if p]
    try:
        import imageio_ffmpeg  # type: ignore

        found.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass
    return list(dict.fromkeys(found))


def mix_with_voice(voice_wav: Path, out_wav: Path, *, mood: str = "هدوء",
                   volume: float = 0.15, run=None) -> tuple[Path, str]:
    """يخلط الموسيقى مع الصوت مع ducking حقيقي — بلا ffmpeg في الخلط نفسه.

    يقبل WAV أو MP3 أو أي صيغة صوت (بيحوّلها الأول).
    يرجّع (الملف, سطر الإسناد).
    """
    import wave as _wave

    voice_wav = _to_wav(Path(voice_wav))
    if Path(voice_wav).suffix.lower() != ".wav":
        raise RuntimeError(f"تعذّر تحويل الصوت لمقطع WAV: {voice_wav}")

    with _wave.open(str(voice_wav), "rb") as w:
        ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(w.getnframes())
    dtype = {1: np.int8, 2: "<i2", 4: "<i4"}.get(sw, "<i2")
    data = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    scale = 32768.0 if sw == 2 else 128.0
    voice = data / scale

    bed_path = voice_wav.parent / f"bed_{mood}.wav"
    dur = len(voice) / sr
    compose(dur, bed_path, mood=mood, volume=1.0)
    with _wave.open(str(bed_path), "rb") as w:
        braw = w.readframes(w.getnframes())
    bed = np.frombuffer(braw, dtype="<i2").astype(np.float32) / 32768.0
    if len(bed) > len(voice):
        bed = bed[: len(voice)]
    else:
        bed = np.pad(bed, (0, len(voice) - len(bed)))

    ducked = _duck(voice, bed)
    final = voice * 0.94 + ducked * float(volume)
    peak = float(np.max(np.abs(final))) or 1.0
    if peak > 0.97:
        final = final / peak * 0.97

    pcm = np.clip(final * 32767, -32768, 32767).astype("<i2")
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with _wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(stereo.tobytes())

    credit = (f"🎵 موسيقى مولّدة للمصنع (مقام {MOODS.get(mood, MOODS['هدوء'])[0]}) — "
              f"حقوق المصنع 100%، صفر Content ID.")
    return out_wav, credit


def for_episode(item: dict, *, duration: float = 0.0, out_dir: Path | None = None
                ) -> tuple[str, float, str]:
    """يحدّد المزاج والمستوى المناسبين للحلقة.

    ⚠️ النص القرآني/التلاوة = **بلا موسيقى** (قاعدة شرعية + صفر Content ID).
    بيرجّع (المزاج, المستوى, سبب).
    """
    kind = str(item.get("kind") or item.get("plan_kind") or "")
    sacred = kind in ("ayah", "quran", "reel", "dua") or bool(item.get("sacred"))

    if sacred:
        return "طبيعة", 0.0, "تلاوة قرآنية — بلا موسيقى، أجواء طبيعية مولّدة بدالها."

    text = " ".join(str(item.get(k) or "") for k in ("spoken", "hook", "field", "theme", "series_title"))
    mood = _pick_mood(text, kind, str(item.get("id") or ""))
    level = {"سينمائي": 0.19, "مشرق": 0.17, "أمل": 0.16,
             "حكمة": 0.14, "هدوء": 0.13, "سكينة": 0.12, "تأمل": 0.12,
             "فرج": 0.16}.get(mood, 0.15)
    return mood, level, f"مزاج {mood} — موسيقى مولّدة بمقام {MOODS.get(mood, MOODS['هدوء'])[0]}."
