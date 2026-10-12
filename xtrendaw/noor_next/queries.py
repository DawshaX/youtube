"""كل جملة تاخد استعلام لقطة يوصفها — بكلمات قابلة للبحث فعلًا.

القاعدة اللي اتعلمناها بالقياس (2026-10-12):
  الاستعلام اللي فيه تعليمات جودة زي «no people» أو «no text» **مش بيتلاقى**،
  لأن مصادر اللقطات المجانية بتدوّر على الكلمات نفسها مش على النية.
  قياس حقيقي: «rain window» → 2 مرشحين · «mosque dome» → 3 ·
  أما «sunlit floor empty no faces no people» → **صفر**.
  فالتعليمات دي بقت **فلاتر** في كود الجلب، مش جزء من نص البحث.
"""
from __future__ import annotations

# كلمات بتتحول لاستعلام إنجليزي قصير وقابل للبحث (من غير تعليمات جودة)
HINTS = (
    ("لوح", "wooden cutting board close up"),
    ("بصل", "onion wooden board"),
    ("ميه", "water pouring slowly"),
    ("حوض", "kitchen sink water"),
    ("نار", "kitchen flame stove"),
    ("ملح", "salt crystals close up"),
    ("فرن", "oven warm light"),
    ("كتاب", "open book pages sunlight"),
    ("مذاكرة", "desk lamp notebook"),
    ("طريق", "empty road morning"),
    ("سيارة", "car dashboard road"),
    ("سماء", "slow clouds blue sky"),
    ("نجم", "night sky stars"),
    ("مطر", "rain on leaves"),
    ("موبايل", "smartphone on table"),
    ("زرع", "houseplant leaves sunlight"),
    ("نبات", "green leaves close up"),
    ("قط", "cat from behind"),
    ("أهل", "family table warm light"),
    ("قهوة", "coffee cup window light"),
    ("غضب", "still water glass"),
    ("صبر", "slow river stones"),
    ("مال", "coins notebook"),
    ("طفل", "soft morning garden"),
    ("نيل", "nile river aerial"),
    ("إسكندرية", "alexandria sea corniche"),
    ("بحر", "calm sea horizon"),
    ("جبل", "mountain mist aerial"),
    ("ليل", "quiet night window light"),
    ("فجر", "sunrise above clouds"),
    ("مغرب", "sunset sky calm"),
    ("دور", "empty queue floor marks"),
    ("طابور", "empty queue floor marks"),
    ("ضوء", "sunrise through window"),
    ("صبح", "sunrise through window"),
    ("شباك", "curtain window morning light"),
    ("باب", "wooden door morning light"),
    ("بيت", "quiet room window light"),
    ("نوم", "empty bed morning light"),
    ("شارع", "empty street morning"),
    ("مطبخ", "kitchen morning light"),
    ("نضافة", "clean kitchen counter"),
    ("تراب", "dust sunlight window"),
    ("زجاج", "glass window cleaning"),
    ("هدوء", "calm water reflection"),
    ("كلمة", "open book warm light"),
    ("حديث", "old manuscript pages"),
    ("مسجد", "mosque dome architecture"),
    ("قرآن", "open quran book"),
    ("دعاء", "praying hands silhouette"),
    ("صلاة", "prayer mat mosque"),
    ("نور", "light through window"),
    ("سكينة", "calm lake reflection"),
    ("قلب", "hands holding heart shape"),
    ("خير", "helping hands community"),
    ("أمل", "sunrise horizon hope"),
    ("صبر", "slow river stones"),
    ("شكر", "warm tea hands"),
    ("أم", "warm home interior"),
    ("أب", "old workshop tools"),
    ("صح", "fresh vegetables market"),
    ("أكل", "cooking steam pot"),
    ("شاي", "tea pouring glass"),
)

ANGLES = (
    "close up",
    "wide shot",
    "morning light",
    "slow detail",
)

# شبكة أمان: استعلامات قصيرة **قيست فعلًا** وبتلاقي لقطات على المصادر المجانية
# بلا مفاتيح. بتتنوّع بالدوران حسب رقم الجملة عشان ما تتكررش في نفس الحلقة.
FALLBACK = (
    "rain on window",
    "mosque dome",
    "desert dunes",
    "night sky stars",
    "ocean waves",
    "mountain mist",
    "sunrise clouds",
    "green leaves sunlight",
    "river stream rocks",
    "quiet street morning",
    "blue sky clouds",
    "snow forest",
    "old book pages",
    "tea pouring",
    "candle flame",
    "water surface ripples",
    "fields harvest",
    "palm trees sky",
    "stone wall texture",
    "lantern light night",
    "birds flying sky",
    "rocky beach waves",
    "city lights night",
    "garden flowers",
)

# التعليمات دي **مش** بتتبعت للبحث — دي فلاتر جودة في كود الجلب.
QUALITY_FILTERS = ("no people", "no faces", "no face", "no text", "no driver face", "no subtitles")


def _strip_filters(text: str) -> str:
    """يشيل تعليمات الجودة من نص الاستعلام — عشان البحث يلاقي فعلًا."""
    s = f" {str(text or '').lower().strip()} "
    for bad in QUALITY_FILTERS:
        s = s.replace(bad, " ")
    s = s.replace("empty ", " ")          # «empty road» ← «road» (البحث ما بيفهمش «فاضي»)
    return " ".join(s.split())


def queries_for(sentence: str, scene: str, salt: int = 0) -> list[str]:
    """يرجّع لحد 4 استعلامات بالترتيب من الأدق للأعم — كلها قابلة للبحث."""
    found = [_strip_filters(q) for word, q in HINTS if word in sentence]
    base = _strip_filters(scene) or "calm nature landscape"
    angle = ANGLES[int(salt) % len(ANGLES)]
    fallback = FALLBACK[int(salt) % len(FALLBACK)]
    second = FALLBACK[(int(salt) * 3 + 7) % len(FALLBACK)]

    out: list[str] = []
    for q in [*found, f"{base} {angle}", base, fallback, second, "calm nature landscape"]:
        q = _strip_filters(q)
        if q and q not in out:
            out.append(q)
    return out[:5]
