"""🔌 طبقة الدمج — بتربط محرّكات الاستوديو الاحترافي بالمصنع الحي.

الفكرة: **إضافة فوق القايم، مش استبدال.** كل ترقية بتشتغل لوحدها، ولو أي
واحدة فشلت المصنع بيكمل بنفسه — مفيش حلقة تتوقف.

نقطة الاستخدام الوحيدة:
    from xtrendaw.pro import integrate
    integrate.activate()               # يفعّل كل الترقيات
    item  = integrate.upgrade_item(item)          # هوك + مزاج
    meta  = integrate.upgrade_metadata(...)        # عنوان/وصف/وسوم
    video = integrate.finish_video(video, work, item)   # مؤثرات + غلاف
    audio = integrate.finish_audio(audio, item, work)   # موسيقى + ducking
"""
from __future__ import annotations

import os
from pathlib import Path

from . import covers, effects, hooks, metadata, music_pro

__all__ = [
    "activate", "enabled", "upgrade_item", "upgrade_metadata",
    "finish_video", "finish_audio", "report",
]


def _on(name: str, default: str = "1") -> bool:
    """كل ترقية ليها مفتاح بيئي — تقدر تقفلها من غير أي تعديل كود."""
    return str(os.environ.get(name, default)).strip() not in ("0", "", "false", "False")


def enabled() -> dict:
    return {
        "hooks": _on("NOOR_PRO_HOOKS"),
        "music": _on("NOOR_PRO_MUSIC"),
        "effects": _on("NOOR_PRO_EFFECTS"),
        "covers": _on("NOOR_PRO_COVERS"),
        "metadata": _on("NOOR_PRO_METADATA"),
    }


def activate() -> dict:
    """يفعّل كل الطبقات ويرجّع حالة كل واحدة (للتسجيل في اللوج)."""
    state = enabled()
    print(
        "[pro] 🎬 الاستوديو الاحترافي: "
        + " · ".join(f"{k}={'✓' if v else '✗'}" for k, v in state.items()),
        flush=True,
    )
    return state


# ─────────────────────────────────────────────────────────────────────
# 1) العنصر (قبل الإنتاج)
# ─────────────────────────────────────────────────────────────────────
def upgrade_item(item: dict) -> dict:
    """هوك احترافي + مزاج موسيقي — بيتحسبوا قبل ما الرندر يبدأ."""
    out = dict(item or {})
    try:
        if enabled()["hooks"]:
            out = hooks.apply(out)
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] الهوك اتخطى: {type(exc).__name__}", flush=True)
    try:
        mood, level, why = music_pro.for_episode(out)
        out["_music_mood"] = mood
        out["_music_level"] = level
        out["_music_why"] = why
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] المزاج اتخطى: {type(exc).__name__}", flush=True)
    return out


# ─────────────────────────────────────────────────────────────────────
# 2) الميتاداتا (عنوان · وصف · وسوم · تعليق مثبّت)
# ─────────────────────────────────────────────────────────────────────
def upgrade_metadata(item: dict, *, hook: str = "", body: str = "", ref: str = "",
                     sources: list[str] | None = None, reciter: str = "",
                     kind: str = "", kw: str = "", effects_applied: list[str] | None = None,
                     mood_credit: str = "", legacy_title: str = "") -> dict:
    """يرجّع {"title", "description", "tags", "pinned", "short"}.

    آمن تمامًا: أي فشل = القيم الفاضية، والمصنع بيكمل بالميتاداتا القديمة.
    """
    res = {"title": "", "description": "", "tags": [], "pinned": "", "short": ""}
    if not enabled()["metadata"]:
        return res
    try:
        res["title"] = metadata.title_for(
            item, hook=hook, kind=kind or str(item.get("kind") or ""),
            kw=kw, reciter=reciter, ref=ref, long_title=legacy_title,
        )
        res["description"] = metadata.description_for(
            item, hook=hook, body=body, ref=ref, sources=sources or [],
            kind=kind or str(item.get("kind") or ""), reciter=reciter,
            mood_credit=mood_credit, effects=effects_applied or [],
        )
        res["tags"] = metadata.tags_for(
            item, kind=kind or str(item.get("kind") or ""), kw=kw, reciter=reciter,
        )
        res["pinned"] = metadata.pinned_comment(
            item, hook=hook, kind=kind or str(item.get("kind") or ""),
        )
        res["short"] = metadata.short_for(
            item, hook=hook, kind=kind or str(item.get("kind") or ""),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] الميتاداتا اتخطت: {type(exc).__name__}: {str(exc)[:80]}", flush=True)
    return res


# ─────────────────────────────────────────────────────────────────────
# 3) الفيديو (بعد الرندر)
# ─────────────────────────────────────────────────────────────────────
def finish_video(video: Path, work: Path, item: dict, *,
                 feeling: str = "") -> tuple[Path, dict]:
    """مؤثرات سينمائية + غلاف عالي النقر.

    يرجّع (الفيديو النهائي, {"cover": path|None, "effects": [...], ...})
    """
    out: dict = {"effects": [], "cover": None, "skipped": []}
    final = video
    try:
        if enabled()["effects"]:
            import time as _t
            _t0 = _t.time()
            final, rep = effects.apply_all(video, work, item, feeling=feeling)
            print(f"[⏱️ مرحلة] التمريرة الختامية (تدريج/حبيبات/شريط): "
                  f"{_t.time() - _t0:.0f}ث", flush=True)
            out["effects"] = rep.get("applied", [])
            out["skipped"] = rep.get("skipped", [])
    except Exception as exc:  # noqa: BLE001
        out["skipped"].append(type(exc).__name__)

    try:
        if enabled()["covers"]:
            cover = work / "cover_pro.png"
            hook = str(item.get("hook") or "")
            covers.build(
                final if final.exists() else video, cover,
                title_hook=covers.short_title(hook),
                episode_id=str(item.get("id") or ""),
                at=1.3,
            )
            if cover.exists():
                out["cover"] = cover
    except Exception as exc:  # noqa: BLE001
        out["skipped"].append(f"cover:{type(exc).__name__}")
    return final, out


# ─────────────────────────────────────────────────────────────────────
# 4) الصوت (موسيقى + ducking)
# ─────────────────────────────────────────────────────────────────────
def finish_audio(audio: Path, item: dict, *, mood: str = "",
                 level: float = -1.0) -> tuple[Path, str]:
    """يخلط الموسيقى المولّدة مع الصوت — إلا لو المحتوى قرآني.

    يرجّع (المسار، الإسناد).
    """
    if not enabled()["music"] or not audio.exists():
        return audio, ""
    try:
        mood = mood or str(item.get("_music_mood") or "هدوء")
        if mood in ("طبيعة", "none", ""):
            return audio, ""
        if level < 0:
            level = float(item.get("_music_level") or 0.15)
        if level <= 0:
            return audio, ""
        out = audio.with_name(audio.stem + "_bed.wav")
        got, credit = music_pro.mix_with_voice(audio, out, mood=mood, volume=level)
        if got.exists() and got.stat().st_size > 1000:
            return got, credit
    except Exception as exc:  # noqa: BLE001
        print(f"[pro] الموسيقى اتخطت: {type(exc).__name__}: {str(exc)[:90]}", flush=True)
    return audio, ""


def report() -> str:
    """سطر واحد للتسجيل في اللوج — بيلخص حالة الاستوديو."""
    s = enabled()
    on = [k for k, v in s.items() if v]
    return f"🎬 استوديو احترافي: {len(on)}/{len(s)} طبقة شغالة ({', '.join(on)})"
