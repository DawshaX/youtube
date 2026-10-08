"""🗓️ جدول الـ١٢ نوع — تقسيم اليوم والساعة بتوقيت القاهرة.

الـ٩ أنواع الأصلية في المخطّط بقت ١٢:
  قرآن · تدبر · حديث · قصص الأنبياء · أسماء الله · أذكار · أدعية · كويز · روح
  + معجزات · ولله الحمد · الله غالب (خير الله دائم)

كل يوم ٨ نشرات (القاعدة القديمة) **منهم ٣ فيديوهات طويلة**.
المسافة بين المواعيد ساعتان ونص، والنافذة ٧٠–١٠٠ دقيقة عشان تأخير
السيرفر ما يضيّعش الموعد، ومن غير ما يلحق موعدين في نفس الدورة.

النص الديني مش بيتكتب هنا. الجدول بيختار النوع، والمصدر (API) بيجيب النص.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

CAIRO = ZoneInfo("Africa/Cairo")
GRACE_MIN = 100

# ترتيب ثابت = ترتيب الخانات تحت
SLOTS = [
    {"h": 6, "m": 0, "form": "short", "name": "فجر"},
    {"h": 8, "m": 30, "form": "short", "name": "صباح"},
    {"h": 11, "m": 0, "form": "long", "name": "ضحى طويل"},
    {"h": 13, "m": 30, "form": "short", "name": "ظهر"},
    {"h": 16, "m": 0, "form": "long", "name": "عصر طويل"},
    {"h": 18, "m": 30, "form": "short", "name": "مغرب"},
    {"h": 21, "m": 0, "form": "long", "name": "ليل طويل"},
    {"h": 23, "m": 30, "form": "short", "name": "هدوء"},
]

TYPES = [
    {"id": "quran", "ar": "قرآن", "lane": "دين"},
    {"id": "tafsir", "ar": "تدبر", "lane": "دين"},
    {"id": "hadith", "ar": "حديث", "lane": "دين"},
    {"id": "qissa", "ar": "قصص الأنبياء", "lane": "قصص"},
    {"id": "asma", "ar": "أسماء الله", "lane": "دين"},
    {"id": "athkar", "ar": "أذكار", "lane": "روح"},
    {"id": "dua", "ar": "أدعية", "lane": "روح"},
    {"id": "quiz", "ar": "كويز", "lane": "دين"},
    {"id": "spirit", "ar": "روح وسكينة", "lane": "روح"},
    {"id": "mujiza", "ar": "معجزات", "lane": "معجزات"},
    {"id": "hamd", "ar": "ولله الحمد", "lane": "خير الله"},
    {"id": "nasr", "ar": "الله غالب", "lane": "خير الله"},
]
TYPE_IDS = tuple(t["id"] for t in TYPES)
TYPE_AR = {t["id"]: t["ar"] for t in TYPES}
TYPE_AR.update({
    "salah": "مواقيت الصلاة",
    "hijri": "تقويم هجري",
    "qfacts": "معلومة قرآنية",
    "proverb": "مثل عربي",
})

# الطويل لازم يكون نوع المحرّك يعرف يجمعه (تلاوة/سلسلة)، مش كارت معلومة
LONG_KINDS = {"quran", "qissa", "mujiza", "hamd", "nasr"}

# لمسات إضافية لسه في المصنع (مش من الـ١٢) — خانة في الأسبوع عشان متختفيش
BONUS = {"salah", "hijri", "qfacts", "proverb"}

WEEKDAY_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
DAY_THEME = [
    "مواقيت وقرآن وقصص",
    "حمد ونصر وخير الله",
    "قصص وسكينة",
    "حديث ومعجزة",
    "جمعة وحمد",
    "قصص الأنبياء ومعجزات",
    "روح وخير الله الدائم",
]

# ٨ خانات لكل يوم، بنفس ترتيب SLOTS. الخانات 2 و4 و6 طويلة.
WEEK: dict[int, list[str]] = {
    0: ["salah", "athkar", "quran", "tafsir", "qissa", "hadith", "mujiza", "dua"],
    1: ["asma", "hamd", "nasr", "spirit", "hamd", "quiz", "quran", "nasr"],
    2: ["qissa", "dua", "qissa", "athkar", "quran", "quran", "mujiza", "spirit"],
    3: ["hadith", "mujiza", "hamd", "hijri", "nasr", "quiz", "qissa", "tafsir"],
    4: ["quran", "hamd", "quran", "dua", "hamd", "spirit", "mujiza", "tafsir"],
    5: ["qissa", "mujiza", "qissa", "nasr", "mujiza", "qfacts", "quran", "asma"],
    6: ["spirit", "proverb", "hamd", "quran", "qissa", "hadith", "nasr", "dua"],
}

# مشاهد إنجليزي للمصادر الحرة — طبيعة وعمارة فاضية، بلا وجوه وبلا سلاح
SCENES = {
    "quran": ["mosque courtyard empty dawn", "quran book soft light", "desert sunrise aerial"],
    "tafsir": ["library sunlight dust", "arabic calligraphy closeup", "quiet study window light"],
    "hadith": ["olive tree wind", "old manuscript light", "courtyard fountain calm"],
    "qissa": ["desert caravan distant", "sea horizon dawn", "mountain path mist"],
    "asma": ["stars milky way", "light through geometric window", "calm lake reflection"],
    "athkar": ["morning mist meadow", "prayer beads wood table", "sunrise clouds gold"],
    "dua": ["hands light silhouette no face", "rain on leaves", "candle light dark wood"],
    "quiz": ["open book aerial", "night sky question", "geometric pattern gold"],
    "spirit": ["forest light rays", "ocean waves slow", "rain window glass"],
    "mujiza": ["ocean split light abstract", "fire embers to cool mist", "moon over still water"],
    "hamd": ["wheat field sunlight", "fruit and water still life", "sunrise above clouds"],
    "nasr": ["dawn after storm", "birds over calm sea", "green valley after rain"],
    "salah": ["minaret silhouette dawn", "empty mosque interior light", "city sunrise aerial"],
    "hijri": ["crescent moon night", "lanterns warm bokeh", "desert night stars"],
    "qfacts": ["open quran pages", "arabic geometric art", "gold light marble"],
    "proverb": ["old market empty morning", "coffee cup window light", "olive grove path"],
}


def cairo_now(now: dt.datetime | None = None) -> dt.datetime:
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    return now.astimezone(CAIRO)


def day_slots(weekday: int, day: dt.date | None = None) -> list[dict]:
    kinds = WEEK[weekday]
    out = []
    for slot, kind in zip(SLOTS, kinds):
        item = {
            "h": slot["h"], "m": slot["m"], "form": slot["form"],
            "slot_name": slot["name"], "kind": kind,
            "kind_ar": TYPE_AR.get(kind, kind),
            "theme": DAY_THEME[weekday],
            "day_ar": WEEKDAY_AR[weekday],
        }
        if day is not None:
            item["key"] = (f"{day.isoformat()}T{slot['h']:02d}:{slot['m']:02d}"
                           f"|{kind}|{slot['form']}")
            item["label"] = (f"{WEEKDAY_AR[weekday]} {slot['h']:02d}:{slot['m']:02d} "
                             f"{slot['name']} · {item['kind_ar']} · {slot['form']}")
        out.append(item)
    return out


def due(done: set[str], now: dt.datetime | None = None) -> list[dict]:
    """الموعد اللي وقته عدّى ولسه جوه نافذة السماح، والأقدم أولًا.

    نافذة واحدة بس بتيجي في الدورة — المواعيد متباعدة ساعتين ونص.
    """
    local = cairo_now(now)
    found = []
    for offset in (0, -1):
        day = (local + dt.timedelta(days=offset)).date()
        midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
        base = midnight + dt.timedelta(days=offset)
        for item in day_slots(base.weekday(), day):
            when = base.replace(hour=item["h"], minute=item["m"])
            delta = (local - when).total_seconds() / 60
            if 0 <= delta <= GRACE_MIN and item["key"] not in done:
                row = dict(item)
                row["when"] = when.isoformat(timespec="minutes")
                found.append(row)
    found.sort(key=lambda r: r["when"])
    return found


def next_slot(done: set[str] | None = None, now: dt.datetime | None = None) -> str:
    local = cairo_now(now)
    done = done or set()
    for add in range(0, 3):
        day = (local + dt.timedelta(days=add)).date()
        base = local.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=add)
        for item in day_slots(base.weekday(), day):
            when = base.replace(hour=item["h"], minute=item["m"])
            if when >= local and item["key"] not in done:
                return item["label"]
    return "—"


def validate() -> list[str]:
    """يرجّع قائمة أخطاء. فاضية = الجدول سليم."""
    bad = []
    if len(TYPES) != 12:
        bad.append(f"الأنواع {len(TYPES)} مش ١٢")
    if len(WEEK) != 7:
        bad.append("الأسبوع ناقص")
    seen = set()
    for wd, kinds in WEEK.items():
        if len(kinds) != 8:
            bad.append(f"{WEEKDAY_AR[wd]} خاناته {len(kinds)}")
            continue
        longs = [k for k, s in zip(kinds, SLOTS) if s["form"] == "long"]
        if len(longs) != 3:
            bad.append(f"{WEEKDAY_AR[wd]} الطويل {len(longs)}")
        for k in longs:
            if k not in LONG_KINDS:
                bad.append(f"طويل مش مدعوم: {k} يوم {WEEKDAY_AR[wd]}")
        seen.update(kinds)
    missing = [t for t in TYPE_IDS if t not in seen]
    if missing:
        bad.append("نوع من الـ١٢ مش في الأسبوع: " + "، ".join(missing))
    return bad


def markdown() -> str:
    lines = ["# جدول نور الأسبوعي — ١٢ نوع · توقيت القاهرة", ""]
    lines.append("كل يوم ٨ نشرات، منهم ٣ طويلة. المسافة ساعتان ونص.")
    lines.append("")
    for wd in range(7):
        lines.append(f"## {WEEKDAY_AR[wd]} — {DAY_THEME[wd]}")
        for item in day_slots(wd, dt.date(2026, 1, 5 + wd)):
            mark = "🎥" if item["form"] == "long" else "📱"
            # التاريخ فوق وهمي عشان المفتاح؛ العرض بالساعة بس
            hh = f"{item['h']:02d}:{item['m']:02d}"
            lines.append(f"- {mark} {hh} {item['slot_name']}: **{item['kind_ar']}** (`{item['kind']}`)")
        lines.append("")
    return "\n".join(lines)
