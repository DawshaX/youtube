"""🗓️ جدول ١٢ شورت + ٣ طويل كل يوم — توقيت القاهرة.

كل نوع من الـ١٢ ياخد شورت في اليوم، والطويل يتبدّل على الأنواع كلها
(سورة، قصص، معجزات، حمد، نصر، حديث، روح…).
المصنع بينشر موعدًا واحدًا في الدورة، ولو فات موعد يلحقه في الدورة الجاية
من غير ما يكدّس اليوم كله في دقيقة.
"""
from __future__ import annotations

import datetime as dt
import os as _os
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


# ─────────────────────────────────────────────────────────────────────────
# 🎛️ منظم الإيقاع (Cadence Governor) + إزاحة التوقيت — **إضافة، مش حذف**
#
# ليه؟ القياس قال: ١١ فيديو في ٢٤ ساعة = **١٠ مشاهدات**، والبحث في يوتيوب
# بعنوان الفيديو بالحرف **مش بيرجّعه**. ده مش ضعف جودة — ده نمط آلي:
# ١٥ فيديو كل يوم على **ساعات ثابتة بالدقيقة**، ٣٦٥ يوم في السنة، من غير
# فاصل واحد. ده بالظبط الوصف اللي سياسة «المحتوى غير الأصيل» بتحارب.
#
# الحل **مش إيقاف المصنع** (ممنوع) — الحل **اختيار أنسب المواعيد**:
#   NOOR_GRID_MAX_PER_DAY = 0 (افتراضي) → زي ما هو، ١٥/يوم بالظبط.
#   NOOR_GRID_MAX_PER_DAY = N (مثلاً ٦) → أنسب N مواعيد في اليوم بس.
#   NOOR_GRID_JITTER = 1 → إزاحة ±٢٢ دقيقة لكل موعد، محسوبة من التاريخ
#                          نفسه (نفس النتيجة لو رجعت تشغّلها تاني).
#
# ملحوظة مهمة: **كل الخانات ١٥ لسه موجودة**، والـvalidate لسه بيتأكد منها.
# اللي بيتغيّر بس: عددها اللي بيوصل للنشر. رجّع الرقم لـ0 وأرجع لـ١٥ فورًا.
_SLOT_INDEX = {id(s): i for i, s in enumerate(SLOTS)}


def _hour_value(h: int) -> float:
    """قيمة الساعة لنمو القناة (توقيت القاهرة، من عادات الجمهور العربي).

    الذروة: ٧–١١ مساءً (٩) · ثانوي: ١٢–٤ عصرًا (٧) · فجر/صبح: ٥–٧ (٨) —
    جمهور الورد والذكر بيصحى بدري، وده جمهور قنوات القرآن بالظبط.
    الليل المتأخر أخف (٤) لأن المنافسة فيه على نطاق واسع.
    """
    if 19 <= h <= 23:
        return 9.0
    if 5 <= h <= 7:
        return 8.0
    if 12 <= h <= 16:
        return 7.0
    if 8 <= h <= 11:
        return 6.0
    return 4.0


def _slot_score(i: int, form: str) -> float:
    """الطويل = ٣× الشورت (مصدر وقت المشاهدة والمشتركين) + قيمة الساعة."""
    return (3.0 if form == "long" else 1.0) * 10.0 + _hour_value(SLOTS[i]["h"])


def _cap_per_day() -> int:
    """سقف الفيديوهات في اليوم. 0 = بلا سقف (السلوك الأصلي بالحرف)."""
    try:
        return max(0, int(_os.environ.get("NOOR_GRID_MAX_PER_DAY") or "0"))
    except ValueError:
        return 0


def _band(h: int) -> int:
    """نطاق اليوم: فجر · ضحى · ظهر · مساء · ليل."""
    if h < 8:
        return 0
    if h < 12:
        return 1
    if h < 17:
        return 2
    if h < 21:
        return 3
    return 4


def _keep_indexes() -> set[int] | None:
    """أنسب N خانة — **بتغطية اليوم كله** مش أعلى درجات بس.

    ليه التنويع؟ قناة قرآن جمهورها بيسمع الفجر والصبح (ورد يومي)، وجمهور
    تاني بالليل. لو اخترنا «أعلى درجة» بس، الطويلات الليلية هتاكل اليوم
    كله والفجر يضيع — والمصنع بيتحول من «قناة» لـ«مصنع طويلات».
    الجزاء ٦ نقاط على كل نقطة إضافية في نفس النطاق ⇒ اليوم بيتوزّع طبيعي.
    """
    cap = _cap_per_day()
    if cap <= 0 or cap >= len(SLOTS):
        return None
    chosen: list[int] = []
    band_count: dict[int, int] = {}
    pool = sorted(range(len(SLOTS)),
                  key=lambda i: -_slot_score(i, SLOTS[i]["form"]))
    while len(chosen) < cap and pool:
        best_i, best_v = None, -1e9
        for i in pool:
            v = _slot_score(i, SLOTS[i]["form"]) - 6.0 * band_count.get(
                _band(SLOTS[i]["h"]), 0)
            if v > best_v:
                best_i, best_v = i, v
        chosen.append(best_i)
        b = _band(SLOTS[best_i]["h"])
        band_count[b] = band_count.get(b, 0) + 1
        pool.remove(best_i)
    return set(chosen)


def _jitter(day: dt.date, i: int) -> int:
    """إزاحة دقايق ثابتة لنفس اليوم — عشان الجدول ما يبقاش بصمة آلية.

    المحسوبة من التاريخ + رقم الخانة ⇒ نفس القيمة كل مرة (مفيش عشوائية
    حقيقية = مفيش مواعيد بتفوت)، بس **مختلفة كل يوم**.
    """
    if _os.environ.get("NOOR_GRID_JITTER") != "1":
        return 0
    import zlib
    h = zlib.crc32(f"{day.isoformat()}#{i}".encode()) % 45  # 0..44
    return h - 22  # −٢٢ .. +٢٢ دقيقة


def cairo_now(now: dt.datetime | None = None) -> dt.datetime:
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    return now.astimezone(CAIRO)


def day_slots(weekday: int, day: dt.date | None = None) -> list[dict]:
    kinds = WEEK[weekday]
    keep = _keep_indexes()          # 🎛️ منظم الإيقاع (None = كل الخانات)
    jday = day or cairo_now().date()
    out = []
    for i, (slot, kind) in enumerate(zip(SLOTS, kinds)):
        if keep is not None and i not in keep:
            continue
        # 🕰️ إزاحة التوقيت: h/m الفعليين، والمفتاح يفضل على الاسمي
        eff = (dt.datetime(2000, 1, 1, slot["h"], slot["m"])
               + dt.timedelta(minutes=_jitter(jday, i)))
        item = {
            "h": eff.hour, "m": eff.minute,
            "h0": slot["h"], "m0": slot["m"],
            "form": slot["form"],
            "slot_name": slot["name"], "kind": kind,
            "kind_ar": TYPE_AR.get(kind, kind),
            "theme": DAY_THEME[weekday],
            "day_ar": WEEKDAY_AR[weekday],
        }
        if day is not None:
            # المفتاح على الوقت **الاسمي** — عشان كل الأرشيف والدولة القديمة
            # تفضل مربوطة بصحيح (مفيش نشر مكرّر بعد التحديث).
            item["key"] = (f"{day.isoformat()}T{slot['h']:02d}:{slot['m']:02d}"
                           f"|{kind}|{slot['form']}")
            item["label"] = (f"{WEEKDAY_AR[weekday]} {item['h']:02d}:{item['m']:02d} "
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
