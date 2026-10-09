"""🃏 رندر كروت نور (2026-10-06) — القالب العام للتصنيفات الجديدة.

نفس الهوية البصرية والصوتية لمصنع نور (خلفية سينمائية متدرّجة + كروت نص +
تعليق edge-tts + أجواء طبيعية بلا موسيقى)، لكن المحتوى هنا **كارت/أسطر**
(اسم من أسماء الله · ذكر من حصن المسلم · سؤال كويز) بدل آية بتلاوة.

الوظايف:
  • build_card_short(item)  — هوك + أسطر منطوقة + سطر مصدر + خاتمة.
  • build_quiz_short(item)  — كويز «من أي سورة هذه الآية؟» بصوت **تلاوة بشرية**
                              للآية (ممنوع TTS على كلام الله) + أسئلة وخيارات.

الملفات الناتجة: workdir/noor.mp4 + workdir/cover.png
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import settings
from .noor_build import _narration
from .tts import ffmpeg

FPS = 30
_size_hook, _size_body, _size_src = 84, 74, 62


def _assemble(seq: list[tuple[Path, float, str]], scenes: list[str], workdir: Path,
              *, lead: float = 0.45, seed: int = 0, y: float = 0.44) -> dict:
    """يبني الفيديو النهائي: خلفية متدرّجة + كروت لكل فصل بطول صوته + صوت مركّب."""
    from .noor_premium import (_ambience, _mix_track, dur_of, grade_and_concat,
                               overlay, scene_clip)

    workdir.mkdir(parents=True, exist_ok=True)
    total = lead + sum(d for _w, d, _t in seq) + 0.25

    per = total / max(1, len((scenes or [])[:4]))
    clips = []
    for i, q in enumerate((scenes or ["mosque interior arches"])[:4]):
        c, _src = scene_clip(q, per + 0.6, workdir, f"card{seed}:{i}", i)
        clips.append(c)
    bg = grade_and_concat(clips, workdir / "bg.mp4")

    segs: list[Path] = []
    t0 = lead
    for i, (w, d, t) in enumerate(seq):
        last = i == len(seq) - 1
        size = _size_hook if i == 0 else (_size_src if ("📖" in t or "🧿" in t or
                                                        "🎙" in t) else _size_body)
        png = overlay([str(t).replace("🤍", "").replace("✨", "").replace("👀", "")
                       .replace("💛", "").replace("🕊️", "").replace("🤲", "").strip()],
                      workdir / f"c{i}.png", size=size, y=y, max_lines=5,
                      color=(255, 252, 240, 255), halo=24, spacing=1.55)
        seg = workdir / f"s{i:02d}.mp4"
        fades = "fade=t=in:st=0:d=0.4:alpha=1"
        if last:
            fades += f",fade=t=out:st={max(0.1, d - 0.5):.2f}:d=0.5:alpha=1"
        from .noor_look import compose_seg
        compose_seg(ffmpeg(), bg, png, seg, ss=t0, dur=d, fades=fades, fps=FPS)
        segs.append(seg)
        t0 += d

    lst = workdir / "segs.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs), encoding="utf-8")
    silent = workdir / "silent.mp4"
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(silent)], capture_output=True, check=True)

    pieces, cur = [], lead
    for w in [x[0] for x in seq]:
        pieces.append((cur, w, 1.0))
        cur += dur_of(w)
    amb = _ambience(total, workdir / "amb.wav", seed=seed)
    track = _mix_track(pieces, total, workdir / "track.m4a", ambience=amb)
    out = workdir / "noor.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-i", str(silent), "-i", str(track),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                        str(out)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("دمج صوت الكارت فشل: " + (r.stderr or "")[-300:])
    cover = workdir / "cover.png"
    subprocess.run([ffmpeg(), "-y", "-ss", f"{lead + 1.0:.2f}", "-i", str(out),
                    "-frames:v", "1", str(cover)], capture_output=True)
    return {"video": out, "cover": cover, "duration": total}


def build_card_short(item: dict, workdir: Path) -> dict:
    """كارت منطوق: هوك → الأسطر (اسم/ذكر) → سطر المصدر → خاتمة."""
    import os as _os
    if _os.environ.get("NOOR_LOOK") == "1":
        try:
            from .noor_look import bind
            bind(item, workdir)
        except Exception:
            pass
    voice = settings.VOICE_AR
    hook = str(item.get("hook") or "من نور الله 🤍")
    lines = [str(x) for x in (item.get("lines") or []) if str(x).strip()]
    src = str(item.get("source") or "")
    outro = str(item.get("outro") or
                "لو الكلام أفادك، اكتب آمين في التعليق وشاركه مع حد بتحبه، "
                "وتابعنا… نور جديد كل يوم.")

    seq: list[tuple[Path, float, str]] = []
    w, d = _narration(hook + ".", workdir, "hook", voice, rate=settings.VOICE_RATE)
    seq.append((w, d, hook))
    for i, ln in enumerate(lines):
        w, d = _narration(ln, workdir, f"l{i}", voice,
                          rate=settings.VOICE_RATE_TAFSIR)
        seq.append((w, d, ln))
    if src:
        w, d = _narration(src.replace("🧿", "").replace("🧩", "").strip(), workdir,
                          "src", voice, rate=settings.VOICE_RATE_TAFSIR)
        seq.append((w, d, src))
    w, d = _narration(outro, workdir, "outro", voice, rate=settings.VOICE_RATE)
    seq.append((w, d, outro))

    res = _assemble(seq, item.get("scenes") or ["mosque interior arches",
                                                "prayer beads on wood"],
                    workdir, seed=len(str(item.get("id") or "")))
    res.update({"text": lines[0] if lines else "", "sources": [src] if src else []})
    return res


def build_quiz_short(item: dict, workdir: Path) -> dict:
    """كويز تفاعلي: تلاوة الآية (بشر) → «من أي سورة؟» → اختيارات → الإجابة."""
    from .noor_premium import _trim_silence, ayah_text, dur_of, recitation

    import os as _os
    if _os.environ.get("NOOR_LOOK") == "1":
        try:
            from .noor_look import bind
            bind(item, workdir)
        except Exception:
            pass
    voice = settings.VOICE_AR
    s, a = int(item["surah"]), int(item["ayah"])
    reciter = item.get("reciter") or "husary"
    ay = ayah_text(s, a, a)
    rec = _trim_silence(recitation(s, a, reciter, workdir, globals_=ay["globals"]),
                        workdir, f"q_{s}_{a}")
    rec_d = max(1.2, dur_of(rec))

    seq: list[tuple[Path, float, str]] = []
    w, d = _narration(str(item.get("hook") or "امتحن معرفتك 👀"), workdir, "hook",
                      voice, rate=settings.VOICE_RATE)
    seq.append((w, d, item.get("hook") or "امتحن معرفتك 👀"))
    seq.append((rec, rec_d, str(item.get("question") or "من أي سورة هذه الآية؟")))
    opts = " · ".join(str(x) for x in (item.get("options") or []))
    w, d = _narration(opts, workdir, "opts", voice, rate=settings.VOICE_RATE_TAFSIR)
    seq.append((w, d, opts))
    ans = str(item.get("answer") or "")
    w, d = _narration(f"الإجابة: {ans}.", workdir, "ans", voice,
                      rate=settings.VOICE_RATE)
    seq.append((w, d, f"✅ الإجابة: {ans}"))
    src = str(item.get("source") or f"🎙️ سورة {item.get('surah_name', '')} — تلاوة {reciter}")
    w, d = _narration("اكتب إجابتك في التعليق، وشوف كام واحد عرفها. وتابعنا… "
                      "كويز جديد كل يوم.", workdir, "outro", voice,
                      rate=settings.VOICE_RATE)
    seq.append((w, d, src))

    res = _assemble(seq, item.get("scenes") or ["quran book open pages",
                                                "mosque interior arches"],
                    workdir, seed=s * 31 + a)
    res.update({"text": item.get("verse") or "", "surah_name": item.get("surah_name"),
                "sources": [src]})
    return res
