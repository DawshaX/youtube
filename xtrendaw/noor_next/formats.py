"""أسلوب اللقطات. صناعة المصنع، مش نسخ فيديو مشهور.

التقليد هنا على الحرفة: افتتاح، قطع، قائمة، حكاية، قبل وبعد.
المحتوى واللقطات والصوت والشخصيات ملك المصنع أو مرخّصة له.
مفيش سحب لفيديو، ومفيش صوت ترند محفوظ، ومفيش لقطة من الفيديو الأصلي.
"""
from __future__ import annotations

RIGHTS = "أسلوب اللقطات من صناعة المصنع. مش نسخ فيديو، ومش صوت محفوظ، ومش وجه شخص حقيقي."

# كوفر واجهته المجانية بتمنع الاستخدام التجاري وبتطلب شعارهم. ما تدخلش النشر.
REFUSED = {
    "coverr_api": "الاستخدام التجاري ممنوع في شروط الواجهة، والنشر على القناة تجاري.",
    "famous_video_file": "نسخ لقطات فيديو مشهور تعدي على حق غيرنا.",
    "trend_audio": "صوت الترند المحفوظ بيقفل الشورت فوق ٦٠ ثانية.",
}

GRAMMARS = {
    "افتتاح وقطع": {"motions": ("push", "left", "right", "hold", "rise"), "neon": False},
    "قائمة": {"motions": ("hold", "push", "left", "hold", "right"), "neon": False},
    "حكاية": {"motions": ("rise", "hold", "push", "left", "hold"), "neon": False},
    "قبل وبعد": {"motions": ("left", "left", "hold", "right", "right"), "neon": False},
    "نيون هادي": {"motions": ("push", "hold", "right", "push"), "neon": True},
    "طين ثلاثي": {"motions": ("rise", "hold", "rise", "push"), "neon": False},
}


def pick_format(episode: dict, feeling: str = "", neon: bool = False) -> tuple[str, dict]:
    blob = " ".join(str(episode.get(k) or "") for k in ("series_title", "field", "emotion"))
    if "طفل" in blob or feeling == "طفل" or feeling == "حزن":
        name = "حكاية"
    elif neon and feeling in ("علم", "لحظة", "هزار"):
        name = "نيون هادي"
    elif feeling in ("علم", "جد"):
        name = "طين ثلاثي" if sum(ord(c) for c in str(episode.get("id") or "")) % 2 else "قائمة"
    else:
        names = ("افتتاح وقطع", "قائمة", "حكاية", "قبل وبعد")
        name = names[sum(ord(c) for c in str(episode.get("id") or "نور")) % len(names)]
    spec = dict(GRAMMARS[name])
    spec["rights"] = RIGHTS
    spec["copied_video"] = False
    return name, spec


def motion_for(spec: dict, index: int) -> str:
    motions = spec.get("motions") or ("push",)
    return motions[index % len(motions)]
