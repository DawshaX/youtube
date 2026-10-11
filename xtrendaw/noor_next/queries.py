"""كل جملة تاخد استعلام لقطة يوصفها. من غير وجوه، ومن غير نص على الصورة."""
from __future__ import annotations

HINTS = (
    ("لوح", "wooden cutting board close up no people"),
    ("بصل", "onion on wooden board no people"),
    ("ميه", "clear water pouring slowly no people"),
    ("حوض", "kitchen sink water no people"),
    ("نار", "small kitchen flame no people"),
    ("ملح", "salt crystals close up no people"),
    ("فرن", "oven warm light no people"),
    ("كتاب", "open book pages sunlight no people"),
    ("مذاكرة", "desk lamp notebook no people"),
    ("طريق", "empty road morning aerial"),
    ("سيارة", "car dashboard road no driver face"),
    ("سماء", "slow clouds blue sky"),
    ("نجم", "night sky stars no people"),
    ("مطر", "rain on leaves close up"),
    ("موبايل", "smartphone on table screen off no people"),
    ("زرع", "houseplant leaves sunlight"),
    ("نبات", "green leaves close up"),
    ("قط", "cat from behind no face close"),
    ("أهل", "empty family table warm light"),
    ("قهوة", "coffee cup window light no people"),
    ("غضب", "still water in glass"),
    ("صبر", "slow river stones"),
    ("مال", "coins and paper notebook no people"),
    ("طفل", "soft morning garden no people"),
    ("نيل", "nile river aerial calm"),
    ("إسكندرية", "alexandria sea corniche empty"),
    ("بحر", "calm sea horizon"),
    ("جبل", "mountain mist aerial"),
    ("ليل", "quiet night window light"),
    ("فجر", "sunrise above clouds"),
    ("مغرب", "sunset sky calm"),
)


def queries_for(sentence: str, scene: str) -> list[str]:
    found = [q for word, q in HINTS if word in sentence]
    base = (scene or "calm nature empty no people").strip()
    if "no people" not in base:
        base += " no people"
    out = []
    for q in found + [base, "calm empty landscape no people no text"]:
        if q not in out:
            out.append(q)
    return out[:4]
