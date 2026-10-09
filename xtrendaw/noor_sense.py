"""يفهم الحلقة قبل ما تتقال.

مش بيؤلّف آية ولا حكم. بياخد الاسم والمكان والكلمات الموجودة فعلًا،
ويطلع هوك وعنوان ومشاهد من الكلام ده. الشعار العام («آية تريح القلب»،
«تلاوة خاشعة») ما يتقالش إلا لو الفيديو تلاوة سورة. الشورت يخلّص
بين 8 و 175 ثانية عشان يفضل شورت على يوتيوب (الحد 3 دقايق).
"""
from __future__ import annotations

import re
import unicodedata

SHORT_MIN = 8
SHORT_MAX = 175

GENERIC = {
    "آية تُريح القلب 🤍", "تلاوة تُسكِن الروح 🕊️", "كلام الله… اسمعها بقلبك",
    "آية لكل قلب تعبان 💛", "دقيقة مع القرآن ✨", "لو قلبك مشغول… اسمع دي",
    "آية افتح بيها يومك 🌅", "تلاوة هادية لقلبك 🌿",
    "افهم الآية دي صح 🧩", "تدبّر آية… تغيّر نظرتك",
    "معنى آية كنت بتقراها ومش فاهمها",
    "قصة من القرآن 🤍", "حكاية فيها عبرة 📖", "قصة من غير ما تتقطع 📚",
    "حديث صحيح ✅", "حديث صحيح", "امتحن معرفتك 👀", "من نور الله 🤍",
    "اسمع الآية دي للآخر… هتغيّر يومك",
}

# كلمة موجودة في النص → مشهد حر بلا وجوه. الجملة ما تتقالش إلا لو الكلمة موجودة.
ANCHORS = [
    ("نار", "fire embers cooling to mist no people", "النار"),
    ("بحر", "ocean aerial light no people", "البحر"),
    ("جبل", "mountain stone dawn mist", "الجبل"),
    ("حوت", "deep blue water light rays", "الحوت"),
    ("فلك", "wooden boat calm sea dawn", "الفلك"),
    ("ريح", "wind over desert dunes aerial", "الريح"),
    ("قمر", "moon over still water night", "القمر"),
    ("كهف", "cave mouth soft light mist", "الكهف"),
    ("نجم", "night sky stars no people", "النجوم"),
    ("مطر", "rain on leaves close", "المطر"),
    ("جنة", "green garden light rays", "الجنة"),
    ("صبر", "desert path dawn calm", "الصبر"),
    ("رحمة", "soft dawn clouds gold", "الرحمة"),
    ("شكر", "wheat field sunlight", "الشكر"),
    ("نور", "light through window dust", "النور"),
    ("ماء", "clear water stream stones", "الماء"),
    ("ليل", "night desert stars calm", "الليل"),
    ("صبح", "sunrise clouds gold aerial", "الصبح"),
]

KIND_SCENES = {
    "hadith": ["olive tree wind", "old manuscript light", "courtyard fountain calm"],
    "salah": ["minaret silhouette dawn", "empty mosque interior light", "city sunrise aerial"],
    "spirit": ["forest light rays", "rain on window glass", "ocean waves slow"],
    "quiz": ["open book aerial", "geometric pattern gold", "night sky question"],
    "proverb": ["old market empty morning", "olive grove path", "coffee cup window light"],
    "hijri": ["crescent moon night", "lanterns warm bokeh", "desert night stars"],
    "qfacts": ["open quran pages", "arabic geometric art", "gold light marble"],
    "asma": ["stars milky way", "light through geometric window", "calm lake reflection"],
    "athkar": ["morning mist meadow", "prayer beads wood table", "sunrise clouds gold"],
    "dua": ["rain on leaves", "candle light dark wood", "hands light silhouette no face"],
    "qissa": ["desert caravan distant", "sea horizon dawn", "mountain path mist"],
    "story": ["desert caravan distant", "sea horizon dawn", "mountain path mist"],
    "mujiza": ["ocean split light abstract", "moon over still water", "stone desert dawn"],
    "hamd": ["wheat field sunlight", "sunrise above clouds", "fruit and water still life"],
    "nasr": ["dawn after storm", "birds over calm sea", "green valley after rain"],
}

# كل نوع له طريق رندر موجود. الاختبار يتأكد إن الخريطة دي كاملة.
ROUTES = {
    "quran": "premium", "tafsir": "premium", "ayah": "premium", "reel": "premium",
    "dua": "premium", "story": "premium", "qissa": "premium",
    "mujiza": "premium", "hamd": "premium", "nasr": "premium",
    "hadith": "hadith",
    "quiz": "quiz",
    "asma": "card", "athkar": "card", "spirit": "card",
    "salah": "card", "hijri": "card", "qfacts": "card", "proverb": "card",
}

RECITATION_KINDS = {"quran", "ayah", "reel"}


def bare(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.replace("ٱ", "ا").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ة", "ه").replace("ى", "ي")
    return t


def is_generic(hook: str | None) -> bool:
    h = (hook or "").strip()
    if not h or h in GENERIC:
        return True
    b = bare(h)
    slogans = ("تريح القلب", "تسكن الروح", "تهادي لقلبك", "حديث صحيح",
               "امتحن معرفتك", "قصه من القران", "حكايه فيها عبره")
    return any(bare(s) in b for s in slogans)


def anchors_in(text: str) -> list[tuple[str, str, str]]:
    b = bare(text)
    return [a for a in ANCHORS if bare(a[0]) in b]


def clip_spoken(text: str, max_words: int = 70) -> str:
    """يقص المتن على حد جملة، مش في نص الكلمة. النص الديني ما يتزادش عليه."""
    words = (text or "").split()
    if len(words) <= max_words:
        return (text or "").strip()
    cut = " ".join(words[:max_words])
    for sep in ("۔", ".", "،"):
        if sep in cut[12:]:
            return cut.rsplit(sep, 1)[0].strip() + sep
    return cut


def hook_from_text(text: str, *, surah: str = "", who: str = "",
                   kind: str = "") -> str:
    """هوك من الكلام نفسه. الكويز ما يكشفش اسم السورة."""
    text = re.sub(r"\s+", " ", text or "").strip()
    who = (who or "").strip()
    surah = (surah or "").strip()
    kind = kind or ""
    words = [w for w in text.replace("﴿", "").replace("﴾", "").split() if len(w) > 1]
    if kind == "quiz":
        lead = " ".join(words[:4])
        return f"{lead}… من أي سورة؟" if lead else "من أي سورة هذه الآية؟"
    found = anchors_in(text)
    if who and kind in ("story", "qissa", "mujiza"):
        if found:
            return f"{who}… و{found[0][2]}"
        return f"قصة {who}"
    if found and surah and kind != "quiz":
        return f"{found[0][2]}… من سورة {surah}"
    if found:
        return f"{found[0][2]} في الكلام ده"
    if words and surah and kind not in ("quiz",):
        return " ".join(words[:4]) + f" — سورة {surah}"
    if words:
        return " ".join(words[:6])
    if who:
        return f"قصة {who}"
    return ""


def scenes_from(text: str, kind: str = "") -> list[str]:
    qs = [a[1] for a in anchors_in(text)]
    for q in KIND_SCENES.get(kind, ["calm nature aerial no people",
                                    "soft light architecture empty",
                                    "dawn clouds aerial"]):
        if q not in qs:
            qs.append(q)
    return qs[:4]


def awaken(item: dict, *, short: bool = True) -> dict:
    """يعدّل الهوك والمشاهد لو لسه شعار عام. ما يمسحش هوك مكتوب عن القصة."""
    item = dict(item)
    kind = str(item.get("plan_kind") or item.get("kind") or "")
    blob = " ".join([
        str(item.get("who") or ""),
        str(item.get("verse") or ""),
        " ".join(str(x) for x in (item.get("lines") or [])),
        str(item.get("hook") or ""),
    ])
    if is_generic(item.get("hook")):
        built = hook_from_text(
            blob, surah=str(item.get("surah_name") or ""),
            who=str(item.get("who") or ""), kind=kind)
        if built:
            item["hook"] = built
    scenes = item.get("scenes") or []
    weak = (not scenes or scenes == ["mosque interior arches"]
            or (isinstance(scenes, list) and len(scenes) < 2))
    if weak or is_generic(str(item.get("hook") or "")):
        item["scenes"] = scenes_from(blob + " " + str(item.get("hook") or ""), kind)
    if short:
        item["max_sec"] = SHORT_MAX
    item["sense"] = True
    return item


def refine_hook(hook: str, text: str, *, surah: str = "", who: str = "",
                kind: str = "") -> str:
    """بعد ما النص ييجي من المصدر. هوك القصة المكتوب يفضل."""
    if hook and not is_generic(hook):
        return hook
    built = hook_from_text(text, surah=surah, who=who, kind=kind)
    return built or hook


def title_of(*, kind: str, hook: str, ref: str = "", reciter: str = "") -> str:
    kind = kind or ""
    hook = (hook or "").strip()
    label = {
        "qissa": "قصة", "story": "قصة", "mujiza": "معجزة", "hamd": "حمد",
        "nasr": "فرج", "hadith": "حديث", "quiz": "كويز",
        "asma": "اسم من أسماء الله", "athkar": "ذكر", "spirit": "كلمة",
        "salah": "مواقيت", "hijri": "هجري", "qfacts": "معلومة",
        "proverb": "مثل", "tafsir": "تدبر", "quran": "تلاوة",
        "ayah": "آية", "dua": "دعاء", "reel": "آيات",
    }.get(kind, "")
    parts = [hook]
    if label and label not in hook:
        parts.append(label)
    if kind != "quiz" and ref and ref not in hook:
        parts.append(ref)
    if reciter and kind in RECITATION_KINDS | {"dua", "mujiza", "story", "qissa",
                                               "hamd", "nasr", "tafsir"}:
        parts.append(reciter)
    title = " | ".join(p for p in parts if p)
    title = title.replace("تلاوة خاشعة من غير ما تتقطع", "")
    title = title.replace("تلاوة خاشعة", "").strip(" |")
    if kind in RECITATION_KINDS and "تلاوة" not in title and reciter:
        title = f"{title} | تلاوة {reciter}"
    return title[:95].strip(" |")


def long_title(kind: str, names: str) -> str:
    names = (names or "").strip()
    if kind == "quran":
        return f"سورة {names} كاملة | تلاوة هادئة"[:95]
    labels = {
        "qissa": "قصص من القرآن", "mujiza": "معجزات من القرآن",
        "hamd": "الحمد في القرآن", "nasr": "الفرج في القرآن",
        "tafsir": "تدبر", "dua": "أدعية من القرآن",
        "hadith": "أحاديث", "spirit": "كلمات تطمئن",
    }
    label = labels.get(kind, kind or "نور")
    title = f"{label}: {names}" if names else label
    if "تلاوة خاشعة" in title:
        title = title.replace("تلاوة خاشعة", "").strip()
    return title[:95]


def long_desc(kind: str, names: str) -> str:
    title = long_title(kind, names)
    return (
        f"{title}\n"
        f"كل مقطع مشهد مختلف، والكلام من مصدره بلا زيادة. {names}.\n"
        "🎙️ صوت بشري على كلام الله · 🧩 المعنى من التفسير الميسّر · 🚫 بلا موسيقى.\n"
        "لو أفادك، شارك الفيديو مع حد يهمه."
    )


def speech_room(rec_seconds: float, max_sec: float = SHORT_MAX) -> float:
    """ثواني الشرح المسموحة بعد التلاوة، من غير ما الشورت يعدّي ٣ دقايق."""
    return max(0.0, float(max_sec) - float(rec_seconds) - 6.0)
