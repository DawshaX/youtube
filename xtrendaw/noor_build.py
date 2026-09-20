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
from .noor_premium import (CACHE, FONT_Q, FONT_UI, FONT_UI_B, FPS, H, UA, W,
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
    return r["wav"], r["duration"]


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

    lead = 0.7
    seq: list[tuple[Path, float, str]] = []       # (صوت، مدة، نص مصاحب)
    wav_hook, d_hook = _narration(item["hook"] + ".", workdir, "hook", voice,
                                  rate="+8%")
    seq.append((wav_hook, d_hook, item["hook"]))
    for gi, g in enumerate(groups):
        w, d = _narration(" ".join(g), workdir, f"h{gi}", voice, rate="-4%")
        seq.append((w, d, " ".join(g)))
    wav_src, d_src = _narration(f"رواه {h['book']}، رقم {h['number']}.",
                                workdir, "src", voice, rate="+2%")
    seq.append((wav_src, d_src, f"📖 {h['book']} — {h['number']}"))
    total = lead + sum(d for _w, d, _t in seq) + 0.6 + 2.4

    # خلفية: مشاهد الثيم
    scenes = item.get("scenes") or ["mosque interior arches"]
    per = (total - 2.4) / max(1, len(scenes[:4]))
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
                      font_path=FONT_Q if ("📖" not in t and i > 0) else FONT_UI_B,
                      color=(255, 252, 240, 255), halo=24, spacing=1.55)
        seg = workdir / f"s{i:02d}.mp4"
        fades = "fade=t=in:st=0:d=0.4:alpha=1"
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
    # خاتمة ثابتة
    op = overlay(["تابعنا للمزيد", "﴿ نور — قرآن وتدبر ﴾"], workdir / "out.png",
                 size=78, y=0.46, font_path=FONT_UI_B, halo=26, max_lines=3,
                 scrim_alpha=150)
    seg = workdir / "sout.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-ss", f"{t0:.3f}", "-i", str(bg),
                        "-loop", "1", "-t", "2.4", "-i", str(op),
                        "-filter_complex",
                        "[0:v]setsar=1[v0];[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[ov];"
                        "[v0][ov]overlay=0:0:format=auto,fade=t=out:st=1.6:d=0.8,"
                        "format=yuv420p[v]", "-map", "[v]", "-t", "2.4",
                        "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-pix_fmt", "yuv420p", str(seg)],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("خاتمة حديث فشلت: " + (r.stderr or "")[-300:])
    segs.append(seg)

    lst = workdir / "segs.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs),
                   encoding="utf-8")
    silent = workdir / "silent.mp4"
    subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-c", "copy", str(silent)],
                   capture_output=True, check=True)
    # الصوت: كل مقطع بوقته (مع هدوء البداية)
    ins, fc = [], []
    for i, w in enumerate(plan_audio, start=1):
        ins += ["-i", str(w)]
    cur = lead
    for i in range(1, len(plan_audio) + 1):
        fc.append(f"[{i}:a]adelay={int(cur*1000)}|{int(cur*1000)}[a{i}]")
        cur += dur_of(Path(plan_audio[i - 1]))
    fc.append("".join(f"[a{i}]" for i in range(1, len(plan_audio) + 1)) +
              f"amix=inputs={len(plan_audio)}:normalize=0,apad,"
              f"atrim=0:{total:.2f},loudnorm=I=-15:TP=-1.5:LRA=9[a]")
    out = workdir / "noor.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-i", str(silent)] + ins +
                       ["-filter_complex", ";".join(fc), "-map", "0:v",
                        "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-movflags",
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

    الطريقة: كل آية = مقطع (خلفية من شريحتها + نصها + تلاوتها) — فتوقيت النص
    مضبوط 100% لأن الصوت لكل آية لوحده، وبعدين بنلزق المقاطع كلها.

    extra: [(سورة، حد آيات)] تُضاف بعد السورة الأولى — بنى بيها فيديو
    ≥4 دقايق (أقل من كده يوتيوب يعتبره شورت ومش بيدخل في ساعات المشاهدة).
    """
    from . import noor_premium as np
    workdir.mkdir(parents=True, exist_ok=True)
    parts = [(surah, max_ayahs)] + list(extra or [])
    scenes = LONG_SCENES.get(theme) or ["night sky stars cloudscape",
                                       "mountains clouds sunrise",
                                       "ocean waves aerial",
                                       "green fields rain"]
    segs: list[Path] = []
    total = 0.0
    srcs: list[str] = []
    names: list[str] = []
    n_all = 0
    for part_i, (snum, nmax) in enumerate(parts):
        info = np._cached_json(f"{np.APIQ}/surah/{snum}/quran-uthmani",
                               f"surah-{snum}")["data"]
        ayahs = info["ayahs"][:nmax]
        surah_name = info["name"]
        names.append(surah_name)
        # كارت اسم السورة
        hp = overlay([f"سورة {surah_name}"], workdir / f"h{part_i}.png", size=100,
                     y=0.46, max_lines=2, tag="﴿ تلاوة وتدبّر ﴾")
        hd = 2.6
        hclip, hsrc = scene_clip(scenes[part_i % len(scenes)], hd, workdir,
                                 f"hdr{part_i}", part_i)
        srcs.append(hsrc)
        hseg = workdir / f"hg{part_i}.mp4"
        r = subprocess.run([ffmpeg(), "-y", "-stream_loop", "-1", "-i", str(hclip),
                            "-loop", "1", "-t", f"{hd}", "-i", str(hp),
                            "-filter_complex",
                            "[0:v]setsar=1[v0];[1:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1[ov];"
                            "[v0][ov]overlay=0:0:format=auto,fade=t=out:st=1.9:d=0.7,"
                            "format=yuv420p[v]", "-map", "[v]", "-t", f"{hd}",
                            "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(hseg)],
                           capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("كارت السورة فشل")
        wav_h = workdir / f"hw{part_i}.wav"
        subprocess.run([ffmpeg(), "-y", "-f", "lavfi", "-i",
                        f"anullsrc=r=44100:cl=stereo", "-t", f"{hd}", "-c:a",
                        "aac", "-b:a", "160k", str(wav_h)], capture_output=True)
        segs.append(hseg)          # بدون صوت (مقطع صامت)
        total += hd
        for i, a in enumerate(ayahs):
            num = int(a["number"])                      # الرقم العالمي
            try:
                rec = recitation(int(a["surah"]["number"]),
                                 int(a["numberInSurah"]), reciter,
                                 workdir / f"a{part_i}_{i:03d}", globals_=[num])
            except Exception as exc:                    # noqa: BLE001
                print(f"[noor] ⚠ آية {num} مش متاحة ({type(exc).__name__}) — تخطي",
                      flush=True)
                continue
            d = dur_of(rec)
            if d <= 0.3:
                continue
            hold = 0.5
            clip, src = scene_clip(scenes[n_all % len(scenes)], d + hold + 0.4,
                                   workdir / f"sc{n_all:03d}", f"long{surah}:{n_all}",
                                   n_all)
            srcs.append(src)
            png = overlay([a["text"].strip()], workdir / f"t{part_i}_{i:03d}.png",
                          size=92, y=0.47, halo=28, spacing=1.5, max_lines=4,
                          tag=f"﴿ {surah_name} — {a['numberInSurah']} ﴾")
            seg = workdir / f"g{part_i}_{i:03d}.mp4"
            dur = d + hold
            vf = ("[0:v]setsar=1[v0];[1:v]format=rgba,fade=t=in:st=0:d=0.32:alpha=1[ov];"
                  "[v0][ov]overlay=0:0:format=auto,format=yuv420p[v]")
            r = subprocess.run([ffmpeg(), "-y", "-stream_loop", "-1", "-i",
                                str(clip), "-loop", "1", "-t", f"{dur:.3f}",
                                "-i", str(png), "-filter_complex", vf, "-map",
                                "[v]", "-t", f"{dur:.3f}", "-r", str(FPS),
                                "-c:v", "libx264", "-preset", "veryfast", "-crf",
                                "20", "-pix_fmt", "yuv420p", "-an", str(seg)],
                               capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(f"آية {num} فشلت: " + (r.stderr or "")[-300:])
            withaudio = workdir / f"wa{part_i}_{i:03d}.mp4"
            subprocess.run([ffmpeg(), "-y", "-i", str(seg), "-i", str(rec),
                            "-filter_complex",
                            f"[1:a]adelay=0|0,apad,atrim=0:{dur:.2f},"
                            "loudnorm=I=-16:TP=-1.5:LRA=9[a]", "-map", "0:v",
                            "-map", "[a]", "-t", f"{dur:.2f}", "-c:v", "copy",
                            "-c:a", "aac", "-b:a", "160k", "-movflags",
                            "+faststart", str(withaudio)], capture_output=True)
            if not withaudio.exists():
                raise RuntimeError("دمج صوت آية فشل")
            segs.append(withaudio)
            total += dur
            n_all += 1
    # نلزق كل حاجة (المقاطع الصامتة صامتة فعلًا: بنولّد صوت فاضي ليها)
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
    if not fixed:
        raise RuntimeError("مفيش آيات اترندرت")
    lst = workdir / "all.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in fixed),
                   encoding="utf-8")
    out = workdir / "noor_long.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                        str(lst), "-c", "copy", str(out)],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("دمج السورة فشل: " + (r.stderr or "")[-300:])
    cover = workdir / "cover.png"
    subprocess.run([ffmpeg(), "-y", "-ss", "3", "-i", str(out), "-frames:v", "1",
                    str(cover)], capture_output=True)
    return {"video": out, "cover": cover, "duration": total,
            "surah": " و ".join(names), "ayahs": n_all, "sources": srcs}
