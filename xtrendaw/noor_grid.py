"""🗓️ جدول ١٢ شورت + ٣ طويل كل يوم — توقيت القاهرة.

كل نوع من الـ١٢ ياخد شورت في اليوم، والطويل يتبدّل على الأنواع كلها
(سورة، قصص، معجزات، حمد، نصر، حديث، روح…).
المصنع بينشر موعدًا واحدًا في الدورة، ولو فات موعد يلحقه في الدورة الجاية
من غير ما يكدّس اليوم كله في دقيقة.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

CAIRO = ZoneInfo("Africa/Cairo")
GRACE_MIN = 70

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
    "salah": "مواقيت الصلاة", "hijri": "تقويم هجري",
    "qfacts": "معلومة قرآنية", "proverb": "مثل عربي",
})

# الطويل ينفع من أي نوع. المحرّك يختار طريق التلاوة أو طريق الكروت.
LONG_KINDS = set(TYPE_IDS)
AYAH_LONG = {"quran", "tafsir", "qissa", "mujiza", "hamd", "nasr", "dua"}
CARD_LONG = {"hadith", "asma", "athkar", "spirit", "quiz", "salah", "hijri",
             "qfacts", "proverb"}

WEEKDAY_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
DAY_THEME = [
    "قرآن وقصص ومعجزة",
    "حمد ونصر وتدبر",
    "حديث وروح ودعاء",
    "أسماء وأذكار وكويز",
    "جمعة: قصص وحمد وقرآن",
    "معجزات ونصر وسكينة",
    "تدبر وقصص وحمد",
]

# ١٢ شورت + ٣ طويل. المسافة حوالي ٨٠ دقيقة عشان النبضة الساعية تلحق.
_TIMES = [
    (5, 0, "short", "فجر"),
    (6, 20, "short", "صباح ١"),
    (7, 40, "short", "صباح ٢"),
    (9, 0, "short", "ضحى"),
    (10, 20, "short", "قبل الطويل"),
    (11, 40, "long", "طويل الضحى"),
    (13, 0, "short", "ظهر"),
    (14, 20, "short", "بعد الظهر"),
    (15, 40, "short", "عصر"),
    (17, 0, "long", "طويل العصر"),
    (18, 20, "short", "مغرب"),
    (19, 40, "short", "مساء"),
    (21, 0, "long", "طويل الليل"),
    (22, 20, "short", "ليل"),
    (23, 40, "short", "هدوء"),
]
SLOTS = [{"h": h, "m": m, "form": form, "name": name} for h, m, form, name in _TIMES]

_SHORTS = list(TYPE_IDS)
_LONGS = [
    ["quran", "qissa", "mujiza"],
    ["hamd", "nasr", "tafsir"],
    ["hadith", "spirit", "dua"],
    ["asma", "athkar", "quiz"],
    ["qissa", "hamd", "quran"],
    ["mujiza", "nasr", "spirit"],
    ["tafsir", "qissa", "hamd"],
]


def _day_kinds(weekday: int) -> list[str]:
    shorts = _SHORTS[weekday:] + _SHORTS[:weekday]
    longs = list(_LONGS[weekday])
    out = []
    si = li = 0
    for slot in SLOTS:
        if slot["form"] == "long":
            out.append(longs[li])
            li += 1
        else:
            out.append(shorts[si])
            si += 1
    return out


WEEK = {wd: _day_kinds(wd) for wd in range(7)}


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


def _rows(done: set[str], now: dt.datetime | None, offsets: tuple[int, ...]) -> list[tuple[float, dict]]:
    local = cairo_now(now)
    found = []
    for offset in offsets:
        base = local.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=offset)
        day = base.date()
        for item in day_slots(base.weekday(), day):
            when = base.replace(hour=item["h"], minute=item["m"])
            delta = (local - when).total_seconds() / 60
            if item["key"] in done:
                continue
            row = dict(item)
            row["when"] = when.isoformat(timespec="minutes")
            found.append((delta, row))
    return found


def due(done: set[str], now: dt.datetime | None = None) -> list[dict]:
    """الموعد اللي جوه نافذة السماح. موعد واحد غالبًا."""
    hits = [row for delta, row in _rows(done, now, (0, -1)) if 0 <= delta <= GRACE_MIN]
    hits.sort(key=lambda r: r["when"])
    return hits


def backlog(done: set[str], now: dt.datetime | None = None) -> list[dict]:
    """مواعيد النهاردة اللي فاتت. الأقدم أولًا — الدورة تلحق واحدًا بس."""
    hits = [row for delta, row in _rows(done, now, (0,)) if delta > GRACE_MIN]
    hits.sort(key=lambda r: r["when"])
    return hits


def next_slot(done: set[str] | None = None, now: dt.datetime | None = None) -> str:
    local = cairo_now(now)
    done = done or set()
    for add in range(0, 3):
        base = local.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=add)
        day = base.date()
        for item in day_slots(base.weekday(), day):
            when = base.replace(hour=item["h"], minute=item["m"])
            if when >= local and item["key"] not in done:
                return item["label"]
    return "—"


def validate() -> list[str]:
    bad = []
    if len(TYPES) != 12:
        bad.append(f"الأنواع {len(TYPES)} مش ١٢")
    if len(SLOTS) != 15:
        bad.append(f"الخانات {len(SLOTS)} مش ١٥")
    if sum(1 for s in SLOTS if s["form"] == "short") != 12:
        bad.append("الشورتس مش ١٢")
    if sum(1 for s in SLOTS if s["form"] == "long") != 3:
        bad.append("الطويل مش ٣")
    for wd, kinds in WEEK.items():
        if len(kinds) != 15:
            bad.append(f"{WEEKDAY_AR[wd]} خاناته {len(kinds)}")
            continue
        shorts = [k for k, s in zip(kinds, SLOTS) if s["form"] == "short"]
        longs = [k for k, s in zip(kinds, SLOTS) if s["form"] == "long"]
        if len(shorts) != 12 or set(shorts) != set(TYPE_IDS):
            bad.append(f"{WEEKDAY_AR[wd]} الشورتس مش كل الـ١٢")
        if len(longs) != 3 or len(set(longs)) < 3:
            bad.append(f"{WEEKDAY_AR[wd]} الطويل مكرر أو ناقص")
        for k in longs:
            if k not in LONG_KINDS:
                bad.append(f"طويل مش مدعوم: {k}")
    return bad


def markdown() -> str:
    lines = ["# جدول نور — ١٢ شورت + ٣ طويل · توقيت القاهرة", ""]
    lines.append("كل نوع ياخد شورت في اليوم. الطويل يتبدّل على الأنواع. كل فيديو بنمط مختلف.")
    lines.append("")
    for wd in range(7):
        lines.append(f"## {WEEKDAY_AR[wd]} — {DAY_THEME[wd]}")
        for item in day_slots(wd, dt.date(2026, 1, 5 + wd)):
            mark = "🎥" if item["form"] == "long" else "📱"
            hh = f"{item['h']:02d}:{item['m']:02d}"
            lines.append(f"- {mark} {hh} {item['slot_name']}: **{item['kind_ar']}** (`{item['kind']}`)")
        lines.append("")
    return "\n".join(lines)
