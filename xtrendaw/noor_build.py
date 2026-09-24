"""بناء حلقات نور: شورت آية · شورت حديث · فيديو طويل (سورة كاملة).

كل حاجة من مصادر مسموحة:
- نص القرآن + التفسير: api.alquran.cloud (بيانات عامة).
- التلاوة: cdn.islamic.network — بننسب القارئ باسمه في الوصف (شرطهم).
- الحديث: فهرس صحيح البخاري/مسلم (fawazahmed0/hadith-api) — بالنص الأصلي.
- المشاهد: بيكسلز/بيكساباي/كومنز (رخص حرة) — أو AI بإفصاح إلزامي.
- أصوات التعليق: edge-tts (صوت ولّدناه — صفر حقوق للغير).
- بلا موسيقى خالص: خطر Content ID = صفر.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

from . import settings
from .noor_premium import (CACHE, FONT_DISPLAY, FONT_Q, FONT_UI, FONT_UI_B,
                           FPS, H, UA, W,
                           FPS_LONG, PRESET_LONG, _ambience, _mix_track,
                           _trim_silence,
                           ayah_tafsir, ayah_text, dur_of, grade_and_concat,
                           overlay, recitation, scene_clip)
from .tts import ffmpeg, synthesize_line, to_wav

HADITH_CDN = ("https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/"
              "ara-{col}.min.json")
COLLECTION_AR = {"bukhari": "صحيح البخاري", "muslim": "صحيح مسلم"}


# ─────────────────────────── نصوص ───────────────────────────

def hadith_text(collection: str, index: int) -> dict:
    """حديث بالنص الأصلي من مجموعة صحيحة + رقمه (بلا أي تعديل).

    الكاش: ملف صغير لكل حديث في state/noor_cache (المجموعة الكاملة 9.4MB —
    بنسيبها في الكاش العام بس، والسطر اللي اتنشر بيتحفظ لوحده على git).
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    small = CACHE / f"h-{collection}-{index}.json"
    if small.exists():
        d = json.loads(small.read_text(encoding="utf-8"))
        return {"text": d["text"], "number": int(index),
                "book": COLLECTION_AR.get(collection, collection)}
    p = CACHE / f"hadith-{collection}.json"
    if not p.exists():
        url = HADITH_CDN.format(col=collection)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=120) as r:
            p.write_bytes(r.read())
    data = json.loads(p.read_text(encoding="utf-8"))
    for h in data.get("hadiths", []):
        if int(h.get("hadithnumber") or -1) == int(index):
            txt = (h.get("text") or "").strip()
            try:
                small.write_text(json.dumps({"text": txt, "n": int(index)},
                                            ensure_ascii=False),
                                 encoding="utf-8")
            except Exception:
                pass
            return {"text": txt, "number": int(index),
                    "book": COLLECTION_AR.get(collection, collection)}
    raise RuntimeError(f"الحديث {collection}:{index} مش موجود")


def _narration(text: str, workdir: Path, name: str, voice: str,
               rate: str = "+0%") -> tuple[Path, float]:
    """تعليق بصوت edge-tts (صوت ولّدناه — بلا أي حقوق للغير)."""
    r = synthesize_line(text, "ar", workdir, name=name, rate=rate, voice=voice)
    w = _trim_silence(Path(r["wav"]), workdir, name)
    return w, dur_of(w)


def _strip(text: str) -> tuple[str, list[int]]:
    """يشيل التشكيل للمقارنة بس، ويرجّع خريطة (موقع في المنزوع → موقع أصلي)."""
    import unicodedata
    out, idx = [], []
    for i, ch in enumerate(text):
        if unicodedata.category(ch) == "Mn" or ch in "\u0670\u06d6\u06dc\u06df\u06e0\u06e2\u06e3\u06e5\u06e6\u06e7\u06e8\u06ea\u06eb\u06ec\u06ed":
            continue
        out.append(ch)
        idx.append(i)
    return "".join(out), idx


def _matn(text: str) -> str:
    """يستخرج **متن الحديث** من غير سلسلة الرواة (الإسناد).

    الإسناد («حدثنا مسدد… عن قتادة عن أنس») مش مقصود للمشاهد، والخبر في المتن.
    بنقصّ من **آخر** ذكر للنبي ﷺ (آخر ذكر = بداية المتن عادةً)، والنص بيفضل
    زي ما هو بلا أي تحويل في كلماته. لو مفيش علامة، بنرجع النص كامل.
    """
    t = re.sub(r"\s+", " ", (text or "").strip())
    bare, idx = _strip(t)
    best = -1
    for m in ["قال رسول الله", "قال النبي", "عن النبي", "عن رسول الله",
              "قال:", "يقول:"]:
        i = bare.rfind(m)
        if i > best:
            best = i
    if best <= 0:
        return t
    cut = t[idx[best]:]
    # نشيل «صلى الله عليه وسلم» الزيادة في الأول لصالح نطق أنظف؟ لا —
    # النص ما يتغيّرش. بس لو القصّ ساب أقل من 30 حرف، نرجع الأصلي.
    return cut if len(cut) > 30 else t


# ─────────────────────────── شورت حديث ───────────────────────────

def build_hadith_short(item: dict, workdir: Path) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    h = hadith_text(item["collection"], int(item["index"]))
    txt = _matn(h["text"])
    words = txt.split()
    groups = [words[i:i + 6] for i in range(0, min(len(words), 72), 6)]
    voice = settings.VOICE_AR

    lead = 0.45
    seq: list[tuple[Path, float, str]] = []       # (صوت، مدة، نص مصاحب)
    # 🎙️ نبرة واحدة لكل الحلقة (تحديث 2026-09-25): قبل كده كان كل فصل بسرعة
    # مختلفة (+10 / -4 / +2 / +6) فالصوت كان بيتنطّط ويبان «مقطّع». دلوقتي
    # الهوك أسرع سنت بسيط، والمتن والحديث بسرعة تدبّر واحدة، والمصدر زي المتن.
    wav_hook, d_hook = _narration(item["hook"] + ".", workdir, "hook",
                                  voice, rate=settings.VOICE_RATE)
    for gi, g in enumerate(groups):
        w, d = _narration(" ".join(g), workdir, f"h{gi}", voice,
                          rate=settings.VOICE_RATE_TAFSIR)
        seq.append((w, d, " ".join(g)))
    wav_src, d_src = _narration(f"رواه {h['book']}، حديث رقم {h['number']}.",
                                workdir, "src", voice,
                                rate=settings.VOICE_RATE_TAFSIR)
    seq.append((wav_src, d_src, f"📖 {h['book']} — {h['number']}"))
    # 🎙️ خاتمة منطوقة — كان قبل كده 2.4 ثانية **صمت كامل** = موت الفيديو في آخره
    outro_line = item.get("outro") or (
        "لو الحديث أفادك، اكتب آمين في التعليق، وشاركه مع حد بتحبه. "
        "وتابعنا… حديث صحيح جديد كل ساعة.")
    wav_out, d_out = _narration(outro_line, workdir, "outro", voice,
                                rate=settings.VOICE_RATE)
    seq.append((wav_out, d_out, outro_line))
    total = lead + sum(d for _w, d, _t in seq) + 0.25

    # خلفية: مشاهد الثيم
    scenes = item.get("scenes") or ["mosque interior arches"]
    per = total / max(1, len(scenes[:4]))
    clips = []
    for i, q in enumerate(scenes[:4]):
        c, _src = scene_clip(q, per + 0.6, workdir, f"hd:{h['number']}:{i}", i)
        clips.append(c)
    bg = grade_and_concat(clips, workdir / "bg.mp4")

    # حلقات (فصول): كل فصل = نص + صوته
    segs: list[Path] = []
    t0 = lead
    plan_audio: list[Path] = []
    for i, (w, d, t) in enumerate(seq):
        png = overlay([t.replace("🤍","").replace("🕊️","").replace("✨","")
                       .replace("🌌","").replace("💛","").replace("🎙️","").strip()],
                      workdir / f"c{i}.png",
                      size=88 if i == 0 else (78 if "📖" not in t else 66),
                      y=0.44, max_lines=4,
                      font_path=FONT_UI_B if (i == 0 or "📖" in t or
                                              i == len(seq) - 1) else FONT_DISPLAY,
                      color=(255, 252, 240, 255), halo=24, spacing=1.55)
        seg = workdir / f"s{i:02d}.mp4"
        fades = "fade=t=in:st=0:d=0.4:alpha=1"
        if i == len(seq) - 1:            # آخر فصل: تلاشي للخارج زي باقي الفيديوهات
            fades += f",fade=t=out:st={max(0.1, d - 0.5):.2f}:d=0.5:alpha=1"
        vf = ("[0:v]setsar=1[v0];[1:v]format=rgba," + fades +
              "[ov];[v0][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        r = subprocess.run([ffmpeg(), "-y", "-ss", f"{t0:.3f}", "-i", str(bg),
                            "-loop", "1", "-t", f"{d:.3f}", "-i", str(png),
                            "-filter_complex", vf, "-map", "[v]", "-t",
                            f"{d:.3f}", "-r", str(FPS), "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "20",
                            "-pix_fmt", "yuv420p", str(seg)],
                           capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("فصل حديث فشل: " + (r.stderr or "")[-300:])
        segs.append(seg)
        plan_audio.append(w)
        t0 += d
    lst = workdir / "segs.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs),
                   encoding="utf-8")
    silent = workdir / "silent.mp4"
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-c", "copy", str(silent)],
                   capture_output=True, check=True)
    # الصوت: كل مقطع في وقته + أجواء طبيعية تحت الكل (بلا موسيقى)
    pieces = []
    cur = lead
    for w in plan_audio:
        pieces.append((cur, w, 1.0))
        cur += dur_of(w)
    amb = _ambience(total, workdir / "amb.wav", seed=len(txt))
    track = _mix_track(pieces, total, workdir / "track.m4a", ambience=amb)
    out = workdir / "noor.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-i", str(silent), "-i", str(track),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a",
                        "aac", "-b:a", "192k", "-shortest", "-movflags",
                        "+faststart", str(out)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("دمج صوت الحديث فشل: " + (r.stderr or "")[-300:])
    cover = workdir / "cover.png"
    subprocess.run([ffmpeg(), "-y", "-ss", f"{lead + 1.0:.2f}", "-i", str(out),
                    "-frames:v", "1", str(cover)], capture_output=True)
    return {"video": out, "cover": cover, "duration": total,
            "text": txt, "book": h["book"], "number": h["number"],
            "sources": ["حديث صحيح — " + h["book"]]}


# ─────────────────────────── فيديو طويل: سورة كاملة ───────────────────────────

LONG_SCENES = {
    "ملك": ["night sky stars cloudscape", "mountains clouds sunrise",
            "birds flying sunset", "night clouds moon"],
    "رحمن": ["ocean waves aerial", "garden flowers rain", "stars galaxy night",
             "pearls water closeup", "green trees sunlight", "sea sunset calm"],
    "واقعة": ["storm clouds dark sky", "lightning storm night", "desert sunrise",
              "field wind grass", "cosmos nebula stars"],
    "كهف": ["cave entrance light", "mountain valley mist", "ancient ruins stone",
            "night sky stars desert"],
    "يس": ["green fields rain", "night sky milky way", "city lights night aerial",
           "sunrise over mountains"],
    "رحمن_": [],
}


def build_long_surah(surah: int, workdir: Path, reciter: str = "husary",
                     theme: str = "رحمن", max_ayahs: int = 40,
                     extra: list[tuple[int, int]] | None = None) -> dict:
    """فيديو طويل لمحرّك ساعات المشاهدة: سورة كاملة (وأحيانًا أكتر من سورة).

    فكرة الأداء (بق حقيقي 2026-09-20): الطريقة القديمة كانت 40 ثانية لكل آية
    (تنزيل لقطة + رندر لوحده) → 50 دقيقة للسورة. دلوقتي:
      1) بنجيب التلاوة لكل آية الأول ونحسب الطول الكلي بالتوقيت الحقيقي.
      2) بنبني **مسار خلفية واحد** من 6 لقطات (مش لقطة لكل آية).
      3) كل آية = قصّة من المسار (seek سريع) + طبقة نص + صوتها.
    فالرندر بيبقى دقايق بدل عشرات الدقايق.
    """
    from . import noor_premium as np
    workdir.mkdir(parents=True, exist_ok=True)
    parts = [(surah, max_ayahs)] + list(extra or [])
    scenes = LONG_SCENES.get(theme) or ["night sky stars cloudscape",
                                       "mountains clouds sunrise",
                                       "ocean waves aerial",
                                       "green fields rain"]
    names: list[str] = []
    # ── 1) الميتاداتا + التلاوة (مع تخطي أي آية مش متاحة)
    plan: list[tuple[str, int, Path, float]] = []
    for part_i, (snum, nmax) in enumerate(parts):
        info = np._cached_json(f"{np.APIQ}/surah/{snum}/quran-uthmani",
                               f"surah-{snum}")["data"]
        ayahs = info["ayahs"][:nmax]
        names.append(info["name"])
        for i, a in enumerate(ayahs):
            num = int(a["number"])                       # الرقم العالمي
            try:
                rec = recitation(int(snum), int(a["numberInSurah"]), reciter,
                                 workdir / f"a{part_i}_{i:03d}", globals_=[num])
            except Exception as exc:                     # noqa: BLE001
                print(f"[noor] ⚠ آية {num} مش متاحة ({type(exc).__name__}) — تخطي",
                      flush=True)
                continue
            d = dur_of(rec)
            if d <= 0.3:
                continue
            plan.append((a["text"].strip(), int(a["numberInSurah"]), rec, d))
    if not plan:
        raise RuntimeError("مفيش آيات اترندرت")

    header = 2.6                                   # كارت اسم السورة
    hold = 0.5
    total = header + sum(d + hold for _t, _n, _r, d in plan)

    # ── 2) مسار الخلفية: 6 لقطات متساوية الطول (مش لقطة لكل آية)
    n_sc = 6
    per = total / n_sc + 1.2
    clips, srcs = [], []
    for i in range(n_sc):
        c, src = scene_clip(scenes[i % len(scenes)], per, workdir,
                            f"longbg{surah}:{i}", i)
        clips.append(c)
        srcs.append(src)
    bg = grade_and_concat(clips, workdir / "bg_long.mp4")
    print(f"[noor] 🎞 خلفية الطويل جاهزة ({total:.0f}ث · {len(clips)} لقطة)",
          flush=True)

    segs: list[Path] = []
    # كارت اسم السورة
    hp = overlay([f"سورة {' و '.join(names)}"], workdir / "hdr.png", size=100,
                 y=0.46, max_lines=2, tag="﴿ تلاوة وتدبّر ﴾")
    hseg = workdir / "hg.mp4"
    vf = ("[0:v]setsar=1[v0];[1:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1[ov];"
          "[v0][ov]overlay=0:0:format=auto,fade=t=out:st=1.8:d=0.7,"
          "format=yuv420p[v]")
    r = subprocess.run([ffmpeg(), "-y", "-ss", "0", "-i", str(bg), "-loop", "1",
                        "-t", f"{header}", "-i", str(hp), "-filter_complex", vf,
                        "-map", "[v]", "-t", f"{header}", "-r", str(FPS_LONG),
                        "-c:v", "libx264", "-preset", PRESET_LONG, "-crf", "21",
                        "-pix_fmt", "yuv420p", "-an", str(hseg)],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("كارت السورة فشل: " + (r.stderr or "")[-200:])
    segs.append(hseg)

    # ── 3) كل آية: قصّة من المسار + نص + صوتها
    t_off = header
    for k, (txt, num, rec, d) in enumerate(plan):
        dur = d + hold
        png = overlay([txt], workdir / f"t{k:03d}.png", size=92, y=0.47, halo=28,
                      spacing=1.5, max_lines=4, tag=f"﴿ {num} ﴾")
        seg = workdir / f"g{k:03d}.mp4"
        vf2 = ("[0:v]setsar=1[v0];[1:v]format=rgba,fade=t=in:st=0:d=0.32:alpha=1[ov];"
               "[v0][ov]overlay=0:0:format=auto,format=yuv420p[v]")
        r = subprocess.run([ffmpeg(), "-y", "-ss", f"{t_off:.3f}", "-i", str(bg),
                            "-loop", "1", "-t", f"{dur:.3f}", "-i", str(png),
                            "-filter_complex", vf2, "-map", "[v]", "-t",
                            f"{dur:.3f}", "-r", str(FPS), "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "20", "-pix_fmt",
                            "yuv420p", "-an", str(seg)], capture_output=True,
                           text=True)
        if r.returncode:
            raise RuntimeError(f"آية {num} فشلت: " + (r.stderr or "")[-200:])
        withaudio = workdir / f"wa{k:03d}.mp4"
        subprocess.run([ffmpeg(), "-y", "-i", str(seg), "-i", str(rec),
                        "-filter_complex",
                        f"[1:a]adelay=0|0,apad,atrim=0:{dur:.2f},"
                        "loudnorm=I=-16:TP=-1.5:LRA=9[a]", "-map", "0:v",
                        "-map", "[a]", "-t", f"{dur:.2f}", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                        str(withaudio)], capture_output=True)
        if not withaudio.exists():
            raise RuntimeError("دمج صوت آية فشل")
        segs.append(withaudio)
        t_off += dur
        if k % 10 == 9:
            print(f"[noor] … {k + 1}/{len(plan)} آية ({t_off / 60:.1f} دقيقة)",
                  flush=True)

    fixed: list[Path] = []
    for s in segs:
        probe = subprocess.run([ffmpeg(), "-i", str(s)], capture_output=True,
                               text=True).stderr
        if "Audio:" in probe:
            fixed.append(s)
            continue
        w = s.with_name("a_" + s.name)
        subprocess.run([ffmpeg(), "-y", "-i", str(s), "-f", "lavfi", "-i",
                        "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", str(w)],
                       capture_output=True)
        fixed.append(w if w.exists() else s)
    lst = workdir / "all.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in fixed),
                   encoding="utf-8")
    out = workdir / "noor_long.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                        str(lst), "-c", "copy", str(out)], capture_output=True,
                       text=True)
    if r.returncode:
        raise RuntimeError("دمج الفيديو الطويل فشل: " + (r.stderr or "")[-300:])
    cover = workdir / "cover.png"
    subprocess.run([ffmpeg(), "-y", "-ss", "3", "-i", str(out), "-frames:v", "1",
                    str(cover)], capture_output=True)
    return {"video": out, "cover": cover, "duration": total,
            "surah": " و ".join(names), "ayahs": len(plan), "sources": srcs}
