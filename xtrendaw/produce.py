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


def produce_episode(topic: dict, workdir: Path) -> dict:
    """ينتج MP4 واحد ويعيد {video, plan, ass, captions, report}."""
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    # 1) السيناريو (عربي للصوت + إنجليزي للقراءة/الـAI)
    segs = content.compose_script(topic, "ar")
    en_lines = content.english_lines(topic)

    # 2) الصوت + التوقيتات
    plan = tts.synthesize_segments(segs, "ar", workdir / "tts")
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
            clip = _footage.vault_clip(kind, item["text"], s1 - s0,
                                       workdir / f"sc{i:02d}" / f"cut{j:02d}",
                                       seed=f"{topic['id']}:{i}:{j}",
                                       exclude=prev_clip, used=clip_usage)
            if clip is None:
                clip = _footage.fetch_clip(real_q, s1 - s0,
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

    # 3.5) موسيقى خلفية مولّدة (بلا حقوق)
    music_path = _music.make_music(plan["total_duration"], workdir / "music.wav")

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
                "credits": _vault.credits_for(used_assets),
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
