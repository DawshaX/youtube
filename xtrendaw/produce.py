"""إنتاج حلقة كاملة: موضوع → سيناريو → صوت → مشاهد → كابتشنز → MP4.

دي الوحدة اللي بتتكرر كل دورة. النشر والحالة layers منفصلة فوقها.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import captions, content, scenes, settings, tts, video

CHIPS_AR = ["الحقيقة الأولى", "الحقيقة الثانية", "والحقيقة الثالثة"]

# الإيقاع البصري: قطعة مشهد جديدة كل ~2 ثانية (كانت قطعة واحدة لكل مقطع
# سردي ≈ 12 ثانية → شاشة ثابتة تقتل الاحتفاظ). يُضبط بـ XT_SCENE_CUT.
SCENE_CUT = max(0.8, float(os.environ.get("XT_SCENE_CUT", "2.0")))


def _cut_ranges(start: float, end: float, cut: float) -> list[tuple[float, float]]:
    """يقسّم مدى زمني لقطع ~2 ثانية، والذيل القصير يندمج في القطعة الأخيرة."""
    spans: list[tuple[float, float]] = []
    t = start
    min_tail = max(0.9, cut * 0.45)
    while t < end - 1e-3:
        nxt = min(t + cut, end)
        if end - nxt < min_tail:
            nxt = end
        spans.append((round(t, 3), round(nxt, 3)))
        t = nxt
    return spans


def _mix_sfx_events(music: Path, events: list[tuple[float, Path]],
                    duration: float, out: Path) -> Path | None:
    """يخلط المؤثرات على الموسيقى في توقيتاتها — من غير ما يرفع صوتها عليه."""
    from .tts import ffmpeg
    import subprocess
    if not events or not music.exists():
        return None
    cmd = [ffmpeg(), "-y", "-i", str(music)]
    for _, sfx_path in events:
        cmd += ["-i", str(sfx_path)]
    parts = []
    for k, (start, _) in enumerate(events, start=1):
        ms = max(0, int(start * 1000))
        parts.append(f"[{k}:a]adelay={ms}|{ms},volume=0.5[s{k}]")
    mix_inputs = "".join(f"[s{k}]" for k in range(1, len(events) + 1))
    filt = ";".join(parts) + f";[0:a]{mix_inputs}amix=inputs={len(events)+1}:duration=first:normalize=0[m]"
    cmd += ["-filter_complex", filt, "-map", "[m]", "-t", f"{duration:.2f}",
            "-c:a", "pcm_s16le", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and out.exists() and out.stat().st_size > 30_000:
        return out
    return None


def produce_episode(topic: dict, workdir: Path, narration_lang: str = "ar",
                    narration_voice: str | None = None) -> dict:
    """ينتج MP4 واحد ويعيد {video, plan, ass, captions, report}."""
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    # 1) السيناريو (لغة التعليق + الإنجليزي للقراءة/الـAI)
    segs = content.compose_script(topic, narration_lang)
    en_lines = content.english_lines(topic)

    # 2) الصوت + التوقيتات
    # صوت الحلقة: دبلجة لغة مطلوبة ← صوتها الرسمي، وإلا مكتبة الأصوات العربية
    # (حسب مزاج الموضوع + دوران بلا تكرار — حتمي حسب معرّف الموضوع)
    from . import voice as _voice
    if narration_voice is None and narration_lang != "ar":
        from . import dub as _dub
        narration_voice = _dub.voice_for(narration_lang)
    if narration_voice is None:
        narration_voice = topic.get("voice") or _voice.pick_voice(
            topic.get("mood"), seed=topic.get("id"))
    plan = tts.synthesize_segments(segs, narration_lang, workdir / "tts",
                                   voice=narration_voice)
    total = plan["total_duration"]
    if total <= 0:
        raise RuntimeError("مدة الصوت صفر")

    # 3) المشاهد — لقطة حيّة متحركة (خزنة assets/footage المولّدة محليًا)
    #    + طبقات نص، مقطوعة كل ~2 ثانية للحفاظ على الإيقاع الفيروسي
    from . import footage as _footage
    from . import music as _music
    from . import vault as _vault
    scene_list: list[dict] = []
    clip_usage: dict[str, int] = {}   # سقف استخدامين لكل لقطة في الحلقة
    used_assets: list = []              # لسجل الاعتمادات في التقرير
    for i, item in enumerate(plan["items"]):
        kind = item["seg"] if item["seg"] in ("hook", "outro") else f"fact{(i % 3) + 1}"
        text = item["text"]
        if ":" in text:
            text = text.split(":", 1)[1].strip()
        chip = ""
        if kind.startswith("fact") and 1 <= i <= 3:
            chip = CHIPS_AR[i - 1]
        elif item["seg"] == "takeaway":
            chip = "سر التحدي الكوني"
        elif item["seg"] == "cta":
            chip = "تحدي مستر بيست"
        subject = ""
        if i < len(en_lines):
            subject = en_lines[i]
            if ":" in subject:
                subject = subject.split(":", 1)[1].strip()
        queries = topic.get("_visual_queries") or []
        real_q = queries[i % len(queries)] if queries else ""
        fresh_pool = topic.get("_fresh_pool") or []
        sc = scenes.build_scene(kind, text, seed=f"{topic['id']}:{i}",
                                workdir=workdir / f"sc{i:02d}", subject=subject,
                                chip=chip, real_query=real_q)
        # كل مقطع سردي يتقطع لقطع ~2 ثانية — وكل قطعة تاخد لقطة متحركة
        # مختلفة (اللقطة السابقة مستبعدة + سقف استخدامين لكل لقطة في الحلقة).
        prev_clip: tuple[str, ...] = ()
        cuts = _cut_ranges(item["start"], item["end"], SCENE_CUT)
        for j, (s0, s1) in enumerate(cuts):
            entry = dict(sc)
            entry["start"] = s0
            entry["end"] = s1
            # 1) لقطة حية من النت (بيكساباي ← بكسلز ← كومنز ← الأرشيف ← ناسا)
            #    — دي الأساس الافتراضي؛ الخزنة المحلية احتياط أوفلاين فقط.
            clip = _footage.fetch_clip(real_q, s1 - s0,
                                       workdir / f"sc{i:02d}" / f"cut{j:02d}",
                                       seed=f"{topic['id']}:{i}:{j}")
            if clip is None:
                clip = _footage.vault_clip(kind, item["text"], s1 - s0,
                                           workdir / f"sc{i:02d}" / f"cut{j:02d}",
                                           seed=f"{topic['id']}:{i}:{j}",
                                           exclude=prev_clip, used=clip_usage)
            # لو الفيديو الشبكي ما جاش: صورة مرخصة تتحول حركة (مش إطار ثابت)
            if clip is None:
                from . import imagery
                clip = imagery.fetch_image_clip(real_q or text, s1 - s0,
                                                workdir / f"sc{i:02d}" / f"cut{j:02d}",
                                                seed=f"{topic['id']}:{i}:{j}")
            if clip is not None:
                entry["video"] = clip
                prev_clip = (clip.name,)
                origin = _footage.clip_origin(clip)
                if origin is not None:
                    clip_usage[origin.name] = clip_usage.get(origin.name, 0) + 1
                    used_assets.append(origin)
            scene_list.append(entry)

    # 3.5) موسيقى خلفية مولّدة (بلا حقوق) + مؤثرات مرخّصة على اللحظات المفصلية
    music_path = _music.make_music(plan["total_duration"], workdir / "music.wav")
    sfx_credits: list = []
    try:
        from . import sfx as _sfx
        events = []
        if plan["items"]:
            w = _sfx.pick("whoosh", workdir / "sfx")
            if w:
                events.append((plan["items"][0]["start"], w))
        take = next((it for it in plan["items"] if it.get("seg") == "takeaway"),
                    None)
        if take:
            im = _sfx.pick("impact", workdir / "sfx")
            if im:
                events.append((take["start"], im))
        sfx_credits = _sfx.session_credits()
        if events:
            mixed = _mix_sfx_events(music_path, events,
                                    plan["total_duration"],
                                    workdir / "music_sfx.wav")
            if mixed is not None:
                music_path = mixed
    except Exception:
        pass  # المؤثرات تجميل — المصنع ما يقفش عليها

    # 4) الكابتشنز المتزامنة (ASS — libass بيتكفل بالتشكيل العربي)
    #    + سطر إنجليزي موازٍ لكل مقطع عشان القراءة العالمية
    en_lines = content.english_lines(topic)
    ass_path, chunks = captions.build_ass(plan, workdir / "caps.ass", en_lines=en_lines)

    # 5) التجميع
    out = settings.OUT / f"{topic['id']}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    video.assemble(plan, scene_list, ass_path, out, workdir / "build", music=music_path)

    # 5.5) الغلاف — فريم حقيقي من الفيديو (لحظة الخطاف) + ≤3 كلمات
    from . import brand
    cover = settings.OUT / f"{topic['id']}-cover.png"
    hook_start = plan["items"][0]["start"] if plan["items"] else 0.0
    brand.compose_cover(topic, cover, seed=str(topic.get("id", "")),
                        video=out, frame_at=hook_start + 0.4)

    # 6) التحقق من المواصفات
    report = video.validate(out)

    # مصادر الصوت الفعلية (من خطة الـTTS نفسها — بلا ادعاء)
    ts_used = sorted({str(it.get("timing_source") or "estimate")
                      for it in plan["items"]})
    audio_sources = [f"edge-tts:{t}" for t in ts_used]

    (workdir / "report.json").write_text(
        json.dumps(
            {
                "episode": topic["id"],
                "title": topic["title_ar"],
                "total_duration": round(total, 3),
                "scenes": len(scene_list),
                "captions": len(chunks),
                "cover": str(cover),
                "audio_sources": audio_sources,
                "voice": narration_voice,
                "credits": _vault.credits_for(used_assets) + sfx_credits,
                "media_sources": _vault.sources_for(used_assets),
                "footage_usage": clip_usage,
                "validate": {
                    "info": report["info"],
                    "checks": report["checks"],
                    "ok": report["ok"],
                },
            },
            ensure_ascii=False, indent=1,
        ),
        encoding="utf-8",
    )

    return {
        "video": out,
        "cover": cover,
        "plan": plan,
        "ass": ass_path,
        "captions": chunks,
        "scenes": scene_list,
        "report": report,
    }
