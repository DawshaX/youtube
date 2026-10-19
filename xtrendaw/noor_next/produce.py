"""رندر حلقة مكتملة: لقطة حية لكل جملة، شخصية أصلية، وأسلوب لقطات من المصنع."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from xtrendaw import footage, textrender, tts
from xtrendaw.noor_look import pick as pick_look

from .formats import motion_for, pick_format
from .montage import (FRAME, loudnorm, overlay_frame, pick_feeling,
                        pick_transition, write_timeline)
from .palettes import palette_for
from .queries import queries_for
from .souls import pick_soul, portrait
from .studio import (burn_words, circle, decorate, halo, layer,
                     licensed_whoosh, mark, mix_bed, say)
from .timeline import sentences, sacred_text

W, H, FPS = 1080, 1920, 30
# 🧱 سقف سلسلة الانتقالات في أمر ffmpeg واحد.
#    ليه؟ ffmpeg بيحجز كل مدخل في الذاكرة. سلسلة xfade بـ١٦ مدخل
#    = انفجار ذاكرة (متجرّب). ٨ آمنة ومجرّبة.
MAX_CHAIN = max(2, int(os.environ.get("NOOR_XFADE_CHAIN") or "8"))
# 🔍 حجم الكابشن في **مسار الإنتاج الحقيقي**. القياس: كان ٦٢–٧٦ بكسل —
#    صغير على موبايل، والمشاهد مش بيلحق يقرا الجملة قبل ما تتغير. (الإعداد
#    الكبير ١٠٠/٨٨/٧٠ كان في مسار تاني **مش مستخدم في النشر**!) فالحجم هنا
#    بقى مضروب في معامل واحد واضح. الرجوع للأصل: NOOR_CAPTION_SCALE=1
CAPTION_SCALE = max(0.5, float(os.environ.get("NOOR_CAPTION_SCALE") or "1.35"))


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "ffmpeg فشل")[-800:])


def _dur(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip() or 0)


def _line_audio(line: str, raw: Path, wav: Path, voice: str, rate: str, pitch: str):
    """جملة صوتها قصير أو وقع مش تلغي الحلقة. بنعيد مرة، وبعدين نتخطاها."""
    for attempt in (1, 2):
        try:
            spoken_words = say(line, raw, voice, rate, pitch)
            _run([
                "ffmpeg", "-y", "-i", str(raw),
                "-af", "apad=pad_dur=0.06",
                "-ar", "48000", "-ac", "2", str(wav),
            ])
            dur = _dur(wav)
        except Exception as exc:
            print(f"[studio] الصوت وقع ({attempt}): {type(exc).__name__}", flush=True)
            continue
        if dur >= 0.45:
            return spoken_words, dur
        print(f"[studio] الصوت قصير ({attempt}): {line[:40]}", flush=True)
    return None


def _voice(episode: dict, pal: dict, soul: dict | None) -> tuple[str, str, str]:
    if pal.get("sacred") or soul is None and pal.get("id") == "faith":
        return "ar-SA-HamedNeural", "-12%", "-4Hz"
    # الحياة عامية. صوت خليجي أو نبرة صفر بيطلّع النطق بايظ.
    voices = ("ar-EG-SalmaNeural", "ar-EG-ShakirNeural")
    seed = str(episode.get("id") or "")
    return voices[sum(ord(c) for c in seed) % 2], "-8%", "+0Hz"


def _crop(motion: str, seconds: float) -> tuple[str, str]:
    dur = max(seconds, 0.1)
    if motion == "left":
        return f"(in_w-out_w)*(1-t/{dur:.2f})", "(in_h-out_h)*0.35"
    if motion == "right":
        return f"(in_w-out_w)*t/{dur:.2f}", "(in_h-out_h)*0.35"
    if motion == "hold":
        return "(in_w-out_w)*0.5", "(in_h-out_h)*0.35"
    if motion == "rise":
        return "(in_w-out_w)*0.5", f"(in_h-out_h)*(0.55-0.18*t/{dur:.2f})"
    return f"(in_w-out_w)*t/{dur:.2f}", "(in_h-out_h)*0.35"


def _style_clip(src: Path, dst: Path, seconds: float, grade: str, motion: str,
                loop_edges: bool = False) -> None:
    """loop_edges=True ⇒ الشريحة دي **مفتوحة من الطرفين** (للريل اللي بيلفّ).

    ليه؟ يوتيوب بيلفّ الشورت تلقائيًا. لو آخر مشهد بيروح لأسود وأول مشهد
    جاي من أسود، المشاهد بيشوف «رمشة سودة» كل لفة. لما نطفّي التلاشي على
    أول شريحة وآخر شريحة، اللفة تبقى **متواصلة** — والمشاهد بيكمّل من غير
    ما يحس إنه رجع للأول. ده بيزوّد عدد اللفّات (إشارة قوية للشورتس).
    """
    fade = 0.27
    out_st = max(0.2, seconds - fade)
    x, y = _crop(motion, seconds)
    base = (
        f"scale={int(W * 1.08)}:{int(H * 1.08)}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:x='{x}':y='{y}'"
    )
    if loop_edges:
        tail = "fps=30,format=yuv420p"
    else:
        tail = (f"fade=t=in:st=0:d={fade},fade=t=out:st={out_st:.2f}:d={fade},"
                "fps=30,format=yuv420p")
    fancy = f"{base},{grade},{tail}" if grade else f"{base},{tail}"
    plain = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,format=yuv420p"

    def encode(vf: str) -> None:
        _run([
            "ffmpeg", "-y", "-i", str(src), "-t", f"{seconds:.2f}", "-vf", vf,
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", str(dst),
        ])

    try:
        encode(fancy)
    except RuntimeError as exc:
        print(f"[studio] التدريج اتخطى: {str(exc)[-180:]}", flush=True)
        encode(plain)


_XFADE = {
    "fade": "fade",
    "fadeblack": "fadeblack",
    "smoothleft": "smoothleft",
    "smoothright": "smoothright",
    "dissolve": "dissolve",
}



def _fewer_shots(lines: list[str], target: int = 22, cap: int = 3,
                 max_shots: int | None = None) -> list[str]:
    """يقلّل عدد اللقطات في الحلقة الطويلة بدمج الجمل القصيرة.

    ليه؟ الحلقة الطويلة (١١٠٠ كلمة) كانت بتطلع **٦٣ لقطة** ⇒ ٦٣ تحميل لقطة
    من النت + ٦٣ تمريرة تنسيق + مونتاج ⇒ الدورة الواحدة خدت **٤٠ دقيقة**
    (وقريبة من مهلة الـ٤٥). ومع الريمكس الهرمي الأمر بقى أهدى.
    والأهم: المونتاج الطويل بطبيعته **أهدى** — لقطة كل ٢٢ كلمة (≈ ١٢ ثانية)
    أنسب للمشاهد من قص كل ٥ ثواني.
    """
    words_all = sum(len(x.split()) for x in lines)
    if words_all < 260:
        return lines                       # الشورتس زي ما هي بالظبط
    # سقف صريح لعدد اللقطات: كل لقطة = تحميل من النت + تنسيق بمحرّك الفيديو
    # + كتابة كابشن. القياس الحقيقي: ٦٣ لقطة = دورة **٤٠ دقيقة** (قربت من
    # المهلة ٤٥)، و٣٧ لقطة لسه كانت تقيلة. الـ٢٦ لقطة بتخلّي المونتاج **أهدى
    # كمان** (لقطة كل ~٢٣ ثانية — ده الأسلوب الصح للمحتوى الطويل الهادي)
    limit = int(max_shots if max_shots is not None
                else os.environ.get("NOOR_LONG_MAX_SHOTS") or "26")
    target = max(target, -(-words_all // max(1, limit)))
    # لازم نسمح بجمل أكتر في المجموعة لو الهدف بيطلب كده (وإلا عدد اللقطات
    # يقف عند len(lines)/cap ويتخطّى السقف — ده حصل مع أطول حلقة: ٥٦ لقطة).
    cap = max(int(cap), -(-len(lines) // max(1, limit)))
    out: list[str] = []
    buf: list[str] = []
    words = 0
    for line in lines:
        buf.append(line)
        words += len(line.split())
        if words >= target or len(buf) >= cap:
            out.append(" ".join(buf))
            buf, words = [], 0
    if buf:
        out.append(" ".join(buf))
    return out


def _spans(lines: list[str], total: float) -> list[tuple[float, float]]:
    weights = [max(8, len(line)) for line in lines]
    whole = sum(weights) or 1
    cursor = 0.0
    out = []
    for weight in weights:
        dur = max(0.9, total * weight / whole)
        out.append((cursor, dur))
        cursor += dur
    if out and cursor > 0:
        scale = total / cursor
        cursor = 0.0
        scaled = []
        for _, dur in out:
            dur = max(0.8, dur * scale)
            scaled.append((cursor, dur))
            cursor += dur
        out = scaled
    return out


def _join(clips: list[Path], durs: list[float], transition: str, dst: Path) -> float:
    """مونتاج بانتقالات حقيقية — **بدون سقف على عدد اللقطات**.

    ليه هرمي (مستويات)؟ الحلقة الطويلة (١٠–٢٠ دقيقة) فيها ٥٠–٢٠٠ جملة،
    وقبل كده كان بيتولّد أمر ffmpeg واحد فيه ٢٠٠ مدخل و١٩٩ انتقال ⇒
    انفجار ذاكرة أكيد. دلوقتي: بنقسّم لمجموعات ٨، كل مجموعة تتعمل لوحدها،
    وبعدين نتائج المجموعات تتجمع بنفس الطريقة — لحد ما تفضل حاجة واحدة.
    النتيجة: انتقالات ناعمة على الطول كله، والذاكرة ثابتة مهما طالت الحلقة.
    """
    if len(clips) <= 1:
        return _join_chain(clips, durs, transition, dst)
    if len(clips) <= MAX_CHAIN:
        return _join_chain(clips, durs, transition, dst)
    chunks: list[Path] = []
    cdurs: list[float] = []
    for i in range(0, len(clips), MAX_CHAIN):
        part = clips[i:i + MAX_CHAIN]
        pdur = durs[i:i + MAX_CHAIN]
        if len(part) == 1:
            chunks.append(part[0])
            cdurs.append(pdur[0])
            continue
        out = dst.with_name(f"{dst.stem}.p{i // MAX_CHAIN}{dst.suffix}")
        cdurs.append(_join_chain(part, pdur, transition, out))
        chunks.append(out)
        print(f"[studio] 🧩 مجموعة مونتاج {i // MAX_CHAIN + 1}: "
              f"{len(part)} لقطة", flush=True)
    return _join(chunks, cdurs, transition, dst)


def _join_chain(clips: list[Path], durs: list[float], transition: str, dst: Path) -> float:
    """سلسلة انتقالات واحدة — للعدد الصغير بس (شوف MAX_CHAIN)."""
    if len(clips) == 1:
        dst.write_bytes(clips[0].read_bytes())
        return durs[0]
    name = _XFADE.get(transition, "fade")
    cmd = ["ffmpeg", "-y"]
    for clip in clips:
        cmd.extend(["-i", str(clip)])
    parts = []
    acc = durs[0]
    prev = "0:v"
    for i in range(1, len(clips)):
        fade = min(0.22, durs[i - 1] * 0.28, durs[i] * 0.28, 0.35)
        fade = max(0.08, fade)
        offset = max(0.04, acc - fade)
        label = f"x{i}"
        parts.append(
            f"[{prev}][{i}:v]xfade=transition={name}:duration={fade:.2f}:offset={offset:.2f}[{label}]"
        )
        prev = label
        acc += durs[i] - fade
    cmd.extend([
        "-filter_complex", ";".join(parts), "-map", f"[{prev}]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(dst),
    ])
    _run(cmd)
    return acc


def _plate(dst: Path, seconds: float, color: str) -> None:
    frames = max(12, int(seconds * FPS) + 2)
    paint = color if str(color).startswith("0x") else "0x1C2428"
    _run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={paint}:s=1240x2200:r={FPS}",
        "-frames:v", str(frames),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(dst),
    ])


def _caption(text: str, path: Path, y: float, fill: str, size: int) -> None:
    textrender.text_image(
        text, path, canvas=(W, H), font_size=size, fill=fill,
        stroke="#14110E", stroke_width=5, y_ratio=y, max_width_ratio=0.72,
    )


def _pro_studio(episode: dict) -> dict:
    """🆕 يرقّي الحلقة بمحرّكات الاستوديو الاحترافي (هوك + مزاج موسيقي).

    آمن تمامًا: لو المكتبة مش موجودة أو أي حاجة فشلت، الحلقة بترجع زي ما هي.
    الفشل مش بيوقف المصنع أبدًا.
    """
    try:
        from xtrendaw.pro import integrate

        return integrate.upgrade_item(dict(episode))
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] الترقية اتخطت: {type(exc).__name__}", flush=True)
        return episode


def _t0() -> float:
    import time as _t
    return _t.time()


def _lap(tag: str, start: float) -> float:
    """يطبع مدة المرحلة بالثواني ويرجّع الوقت الحالي (لسلسلة قياسات)."""
    import time as _t
    now = _t.time()
    print(f"[⏱️ مرحلة] {tag}: {now - start:.0f}ث", flush=True)
    return now


def _hook_into_spoken(episode: dict, spoken: str) -> str:
    """يحقن الهوك في **أول جملة منطوقة** عشان يتقال فعلًا، مش يبان بس.

    القاعدة المتفق عليها: أول ثانية هي اللي بتقرّر، والهوك لازم يكون مسموع
    ومكتوب في نفس الوقت. بتحقن بس لو الجملة الحالية ضعيفة — عشان ما نضيّعش
    نص أصلي قوي عند القناة.
    """
    hook = str(episode.get("hook") or "").strip()
    if not hook or sacred_text(spoken):
        return spoken
    try:
        from xtrendaw.pro import hooks

        lines = sentences(spoken)
        if not lines:
            return spoken
        first = lines[0].strip()
        if hook[:24] in spoken:          # الهوك موجود أصلًا
            return spoken
        if hooks.is_weak(first):          # جملة ضعيفة → نستبدلها بالهوك
            rest = " ".join(lines[1:]).strip()
            merged = f"{hook} {rest}".strip()
            print(f"[pro] هوك جديد مسموع: {hook[:48]}", flush=True)
            return merged
        # الجملة الأصلية قوية: نضيف سؤال الهوك قبلها (بيفتح الفضول)
        if hook.endswith(("؟", "?")):
            print(f"[pro] سؤال افتتاحي: {hook[:48]}", flush=True)
            return f"{hook} {spoken}".strip()
        return spoken
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] حقن الهوك اتخطى: {type(exc).__name__}", flush=True)
        return spoken


def render(episode: dict, work: Path) -> dict | None:
    # ⏱️ عدّاد المراحل: كل مرحلة بوقتها الحقيقي — عشان نعرف فين بيتحرق الوقت
    #    (الطويل لازم يخلص جوّه مهلة الدورة ٤٥ دقيقة، فالقياس مش رفاهية).
    _T = _t0()
    episode = _pro_studio(episode)
    spoken = (episode.get("spoken") or "").strip()
    if not spoken or sacred_text(spoken):
        return None
    spoken = _hook_into_spoken(episode, spoken)
    lines = sentences(spoken)
    if len(lines) < 2:
        return None
    lines = _fewer_shots(lines)     # الطويل: لقطة كل ~٢٢ كلمة بدل ٦٠+ لقطة
    pal = palette_for(episode)
    look = pick_look({"id": episode.get("id"), "hook": lines[0], "kind": pal["id"]})
    feeling, feel = pick_feeling(episode)
    soul = None if pal.get("sacred") else pick_soul(episode, feeling)
    fmt_name, fmt = pick_format(episode, feeling, neon=bool(soul and soul.get("neon")))
    transition = pick_transition(str(episode.get("id") or ""))
    voice, rate, pitch = _voice(episode, pal, soul)
    work.mkdir(parents=True, exist_ok=True)
    # الصوت مرة واحدة. التقطيع جملة-جملة كان بيطلّع النطق متقطع وبايظ.
    # ⚠️ باج حقيقي (2026-10-16): النص الطويل (١١٠٠ كلمة) رجع من خدمة الصوت
    #    **١٥ ثانية** بدل ٦٧٨ — واللوج قال «نجح»، والـ`-shortest` في الآخر
    #    قصّ الفيديو على الصوت، فنزلت حلقة ١٥ ثانية على القناة. عشان كده:
    #    النص الطويل بيتنطق **مُجزّأ** وبفحص مدة إجباري.
    say_text = tts.speakable(spoken)
    speech = tts.synthesize_long(
        say_text, "ar", work, "full", rate=rate, pitch=pitch, voice=voice,
    )
    audio = Path(speech["wav"])
    total = float(speech.get("duration") or 0)
    _T = _lap(f"النطق ({len(say_text.split())} كلمة)", _T)
    if total < 2 or not audio.exists():
        print("[studio] الصوت ما طلّعش", flush=True)
        return None
    # فحص أخير قبل ما نكمّل: الصوت لازم يقرب من المتوقّع من عدد الكلمات
    want = tts._expected_sec(say_text, rate)
    if want > 30 and total < want * 0.6:
        print(f"[studio] ✗ الصوت ناقص ({total:.0f}ث من ~{want:.0f}ث) — "
              "مش هننشر حلقة مقطوعة", flush=True)
        return None
    spans = _spans(lines, total)
    words = []
    for word in speech.get("words") or []:
        start = float(word.get("start") or 0)
        end = float(word.get("end") or start)
        words.append({"t": start, "d": max(0.12, end - start), "w": word.get("word") or ""})
    clips: list[Path] = []
    caps: list[Path] = []
    credits: list[str] = []
    durs: list[float] = []
    used: list[str] = []
    pool: list[Path] = []
    unique = 0
    scene = str(episode.get("scene") or "")
    for i, line in enumerate(lines):
        dur = spans[i][1]
        got = None
        fresh = False
        for q in queries_for(line, scene, salt=i):
            got = footage.fetch_clip(q, dur + 0.3, work, f"{episode.get('id')}:{i}:{q}")
            if got:
                fresh = True
                break
        if not got and pool:
            got = pool[i % len(pool)]
            print(f"[library] زاوية تانية من لقطة الحلقة: {line[:32]}", flush=True)
        if not got:
            print(f"[library] مفيش لقطة، ومفيش لوحة فاضية: {line[:40]}", flush=True)
            continue
        if fresh:
            unique += 1
            pool.append(got)
            from xtrendaw import vault
            rec = vault.record_for(got) or {}
            if rec.get("credit_line"):
                credits.append(rec["credit_line"])
            elif rec.get("source"):
                credits.append(f"{rec.get('source')} · {rec.get('license') or ''}")
        styled = work / f"shot-{i}.mp4"
        grades = [feel["grade"], look.get("grade") or "eq=saturation=1.02"]
        if fmt.get("neon"):
            grades.append("eq=saturation=1.12")
        grade = ",".join(part.strip(",") for part in grades if part)
        # 🎬 الكور: الشورتس بس — أول وآخر لقطة بلا تلاشي (لفة متواصلة).
        #    الحلقات الطويلة تفضل بتلاشيها الطبيعي (مش بتلفّ أصلًا).
        _loop = (len(lines) <= 12 and (i == 0 or i == len(lines) - 1)
                 and os.environ.get("NOOR_LOOP_SHORTS", "1") == "1")
        _style_clip(got, styled, dur, grade, motion_for(fmt, i),
                    loop_edges=_loop)
        png = work / f"cap-{i}.png"
        _caption(line, png, float(look.get("y") or 0.62),
                 pal.get("text") or "#F7F1E6",
                 max(58, int(round(int(feel["size"]) * CAPTION_SCALE))))
        clips.append(styled)
        caps.append(png)
        durs.append(dur)
        used.append(line)
    if unique < 2 or len(clips) < 2:
        print(f"[studio] المشاهد ناقصة ({unique} لقطة) — مش هننشر لوحة", flush=True)
        return None
    silent = work / "silent.mp4"
    visual_len = _join(clips, durs, transition, silent)
    _T = _lap(f"اللقطات والمونتاج ({len(clips)} لقطة)", _T)
    scale = visual_len / sum(durs) if sum(durs) else 1.0
    cmd = ["ffmpeg", "-y", "-i", str(silent)]
    for png in caps:
        cmd.extend(["-i", str(png)])
    chain = []
    prev = "0:v"
    t = 0.0
    for i, dur in enumerate(durs, 1):
        shown = max(0.4, dur * scale)
        chain.append(f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{t:.3f},{t + shown:.3f})'[v{i}]")
        prev = f"v{i}"
        t += shown
    over = work / "over.mp4"
    cmd.extend([
        "-filter_complex", ";".join(chain), "-map", f"[{prev}]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(over),
    ])
    _run(cmd)
    _T = _lap("طبقة الجمل", _T)
    if words and total > 0:
        fit = visual_len / total
        words = [{"t": w["t"] * fit, "d": w["d"] * fit, "w": w["w"]} for w in words]
    try:
        over = burn_words(over, words, work, pal.get("text") or "#F7F1E6", _run)
    except Exception as exc:
        print(f"[studio] تلوين الكلمة اتخطى: {type(exc).__name__}", flush=True)
    _T = _lap("تلوين الكلمة", _T)
    drawn = ("cartoon", "clay3d", "flat", "watercolor", "pastel", "lowpoly", "neon", "dusk", "sport")
    face = portrait(soul) if soul and soul.get("style") in drawn else None
    avatar_png = None
    if face:
        avatar_png = work / "avatar.png"
        if not circle(face, avatar_png):
            avatar_png = None
    badge = work / "mark.png"
    mark(badge, (soul or {}).get("mark") or "#E2B07A")
    framed = work / "framed.mp4"
    # 🧩 تمريرة واحدة للزينة كلها (أفاتار + علامة + إطار) بدل ٣ تمريرات
    #    كاملة على الفيديو — الفرق دقايق في الحلقة الطويلة بلا أي فرق في الشكل.
    #    لو وقعت لأي سبب: نرجع للطريقة القديمة بثلاث تمريرات (ما بتكسرش أبدًا).
    got = decorate(over, framed, avatar=avatar_png,
                   badge=badge if badge.exists() else None,
                   frame=FRAME if FRAME.exists() else None, run=_run)
    if got is not None:
        over = got
    else:
        if avatar_png:
            over = layer(over, work / "avatar.mp4", avatar_png, "46",
                         "'1510+5*sin(t)'", _run)
        over = layer(over, work / "marked.mp4", badge, "960", "72", _run)
        overlay_frame(over, framed, _run)
    _T = _lap("الطبقات والإطار", _T)
    music_credit = None
    voiced = audio
    ratio = (visual_len / total) if total else 1.0
    fitted = work / "fitted.wav"
    if 0.82 <= ratio <= 1.18:
        tempo = max(0.5, min(2.0, total / max(visual_len, 0.1)))
        _run(["ffmpeg", "-y", "-i", str(audio), "-af", f"atempo={tempo:.4f}", "-ar", "48000", "-ac", "2", str(fitted)])
        if fitted.exists():
            voiced = fitted
    else:
        _run(["ffmpeg", "-y", "-i", str(audio), "-af", "apad=pad_dur=3", "-t", f"{visual_len:.2f}", "-ar", "48000", "-ac", "2", str(fitted)])
        if fitted.exists():
            voiced = fitted
    normal = work / "normal.wav"
    loudnorm(voiced, normal, _run)

    # ── 🆕 موسيقى الاستوديو: مقام مخصّص للحلقة + خفض تلقائي وقت الكلام
    #    (القرآن والدعاء = بلا موسيقى خالص بقاعدة الموسيقى نفسها)
    audio_final = normal
    try:
        from xtrendaw.pro import integrate as _pro_int
        from xtrendaw.pro import music_pro as _pro_music

        mood = str(episode.get("_music_mood") or "")
        level = float(episode.get("_music_level") or 0.0)
        if mood and level > 0 and _pro_int.enabled().get("music") and normal.exists():
            mixed, music_credit = _pro_music.mix_with_voice(
                normal, work / "scored.wav", mood=mood, volume=level,
            )
            if mixed.exists() and mixed.stat().st_size > 2048:
                audio_final = mixed
                print(f"[pro] 🎵 مزيكا «{mood}» عند {level:.2f} — {music_credit[:60]}",
                      flush=True)
        elif mood:
            music_credit = f"بلا موسيقى ({mood}) — {episode.get('_music_why') or ''}".strip()
            print(f"[pro] 🕊️ {music_credit[:80]}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] المزيكا اتخطت: {type(exc).__name__}", flush=True)

    # ── 🌧️ الساوندسكيب: أجواء طبيعية مولّدة بذكاء من المحتوى نفسه
    #    (مطر/ليل/عصافير/نار/بحر/نسيم) — صفر موسيقى سارية، صفر حقوق،
    #    وكل فيديو ليه بصمة صوتية مختلفة بالبذرة. القرآن بأخف درجة وقار.
    try:
        from xtrendaw import soundscape as _scape
        _id = str(episode.get("id") or episode.get("title") or "")
        _amb = _scape.pick_ambience(episode)
        _amb_wav = _scape.ambience_wav(_amb, visual_len, _id, work)
        if _amb_wav is not None and audio_final.exists():
            _lvl = _scape.level_for(episode)
            _atmp = work / "scaped.wav"
            _run(["ffmpeg", "-y", "-i", str(audio_final), "-i", str(_amb_wav),
                  "-filter_complex",
                  f"[1:a]volume={_lvl:.3f}[amb];"
                  f"[amb][0:a]sidechaincompress=threshold=0.06:ratio=6:attack=20:release=400[duck];"
                  f"[0:a][duck]amix=inputs=2:duration=first:normalize=0[m]",
                  "-map", "[m]", "-ar", "48000", "-ac", "2", str(_atmp)])
            if _atmp.exists() and _atmp.stat().st_size > 2048:
                audio_final = _atmp
                music_credit = ((music_credit + " · ") if music_credit else "") \
                               + _scape.describe(episode)
                print(f"[soundscape] 🌧️ أجواء «{_amb}» بخفض تلقائي عند {_lvl:.3f}",
                      flush=True)
    except Exception as exc:  # noqa: BLE001 — تجميل، المصنع ما يقفش عليه
        print(f"[soundscape] اتخطى: {type(exc).__name__}", flush=True)

    lines = used
    out = work / "episode.mp4"
    # `-shortest` بيقصّ الفيديو على طول الصوت. ده كان بيحوّل حلقة ٦٠٠ ثانية
    # لحلقة ١٥ ثانية لو الصوت جه ناقص. دلوقتي: بناخد أقصرهم **بس لو الفرق
    # صغير**؛ ولو الصوت أقصر بكتير من الصورة، بنمدّه صمت ونكمّل (الفيديو
    # مش هيتشوّه، والحلقة ما تضيعش)، والفحص فوق أصلاً بيمنع الحالة دي.
    a_dur, v_dur = _dur(audio_final), _dur(framed)
    if v_dur and a_dur and a_dur < v_dur * 0.9:
        print(f"[studio] ⚠️ الصوت ({a_dur:.0f}ث) أقصر من الصورة ({v_dur:.0f}ث) — "
              "بنمدّ الصوت بدل قص الفيديو", flush=True)
        padded = work / "padded.wav"
        _run(["ffmpeg", "-y", "-i", str(audio_final),
              "-af", f"apad=whole_dur={v_dur:.2f}", "-t", f"{v_dur:.2f}",
              "-ar", "48000", "-ac", "2", str(padded)])
        if padded.exists() and padded.stat().st_size > 2048:
            audio_final = padded
    _run([
        "ffmpeg", "-y", "-i", str(framed), "-i", str(audio_final),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ])
    _T = _lap("الصوت والمزج والدمج", _T)

    # ── 🆕 التمريرة الختامية: تدريج سينمائي + حبيبات + شريط تقدّم + غلاف
    cover = None
    pro_report: dict = {}
    try:
        from xtrendaw.pro import integrate as _pro_int

        if out.exists():
            finished, pro_report = _pro_int.finish_video(
                out, work, episode, feeling=feeling,
            )
            if finished.exists() and finished.stat().st_size > 2048:
                out = finished
            cover = pro_report.get("cover")
            if pro_report.get("effects"):
                print(f"[pro] 🎬 {', '.join(pro_report['effects'])}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] التمريرة الختامية اتخطت: {type(exc).__name__}", flush=True)
    shots = [
        {"i": i, "say": line, "dur": durs[i], "visual": "footage", "motion": motion_for(fmt, i)}
        for i, line in enumerate(lines)
    ]
    write_timeline(work / "timeline.json", episode, shots, feeling, transition, {
        "format": fmt_name,
        "rights": fmt["rights"],
        "copied_video": False,
        "soul": None if not soul else soul["name"],
        "soul_style": None if not soul else soul["style"],
        "faces": bool(face),
        "face_kind": "شخصية أصلية" if face else "من غير وجه",
        "music": music_credit,
        "tools": [
            "خط زمني", "لقطة لكل جملة", "أسلوب لقطات أصلي", "كابشن عربي",
            "كلمة بتتلون", "انتقال بين اللقطات", "إطار", "صوت مصري متصل",
            "من غير لوحة فاضية", "ترخيص مع اللقطة",
        ],
    })
    return {
        "video": out,
        "duration": _dur(out),
        "look": look.get("name") or look.get("id"),
        "feeling": feeling,
        "transition": transition,
        "format": fmt_name,
        "soul": None if not soul else soul["name"],
        "voice": voice,
        "credits": list(dict.fromkeys(credits)),
        "lines": lines,
        "hook": episode.get("hook") or "",
        "hook_style": episode.get("hook_style") or "",
        "music_mood": episode.get("_music_mood") or "",
        "music_level": episode.get("_music_level") or 0.0,
        "cover": cover,
        "pro": pro_report,
    }
