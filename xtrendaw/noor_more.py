"""✨ تصنيفات المخزون الإضافية (2026-10-07) — تنويع حقيقي بمصادر موثّقة.

٤ أنواع جديدة كلها من APIs مجانية بلا مفاتيح:
  🕌 **salah**   : مواقيت الصلاة اليومية لعواصم ومدن العالم (api.aladhan)
                  — أعلى محتوى تفاعلًا محليًا: كل بلد يشوف مدينته وتوقيته.
  🌙 **hijri**   : التاريخ الهجري + عدّاد المناسبات (رمضان · العيدين · عرفة)
                  — تواريخ محسوبة من الـAPI نفسه (صفر تخمين).
  📖 **qfacts**  : معلومات محسوبة من بيانات القرآن (عدد السور/الآيات/المكي
                  والمدني/الأطول/الأقصر) — صفر معلومة من الذاكرة.
  🗣️ **proverb** : أمثال عربية مشهورة من التراث (ملك عام) + معناها بجملة.

القاعدة محفوظة: مفيش أي كتابة من الذاكرة في أمر ديني — دي معلومات
ومواقيت وتواريخ من مصادر بيانات معتمدة.
"""
from __future__ import annotations

import datetime as _dt
import json
import time
import urllib.request

from . import settings

UA = {"User-Agent": "NoorFactory/1.0 (islamic content auto)"}
CACHE = settings.STATE / "noor_cache" / "more"

# ─────────────── 🕌 مدن العالم (بالعربي + الاسم الإنجليزي للمصدر) ───────────────
CITIES: list[tuple[str, str, str]] = [
    ("مكة المكرمة", "Makkah", "Saudi Arabia"),
    ("المدينة المنورة", "Medina", "Saudi Arabia"),
    ("الرياض", "Riyadh", "Saudi Arabia"),
    ("القاهرة", "Cairo", "Egypt"),
    ("الإسكندرية", "Alexandria", "Egypt"),
    ("دبي", "Dubai", "UAE"),
    ("أبوظبي", "Abu Dhabi", "UAE"),
    ("الدوحة", "Doha", "Qatar"),
    ("الكويت", "Kuwait City", "Kuwait"),
    ("المنامة", "Manama", "Bahrain"),
    ("مسقط", "Muscat", "Oman"),
    ("عمّان", "Amman", "Jordan"),
    ("بيروت", "Beirut", "Lebanon"),
    ("دمشق", "Damascus", "Syria"),
    ("بغداد", "Baghdad", "Iraq"),
    ("صنعاء", "Sanaa", "Yemen"),
    ("الخرطوم", "Khartoum", "Sudan"),
    ("طرابلس", "Tripoli", "Libya"),
    ("تونس", "Tunis", "Tunisia"),
    ("الجزائر", "Algiers", "Algeria"),
    ("الرباط", "Rabat", "Morocco"),
    ("نواكشوط", "Nouakchott", "Mauritania"),
    ("إسطنبول", "Istanbul", "Turkey"),
    ("جاكرتا", "Jakarta", "Indonesia"),
    ("كوالالمبور", "Kuala Lumpur", "Malaysia"),
    ("كراتشي", "Karachi", "Pakistan"),
    ("لاهور", "Lahore", "Pakistan"),
    ("دكا", "Dhaka", "Bangladesh"),
    ("لاغوس", "Lagos", "Nigeria"),
    ("نيروبي", "Nairobi", "Kenya"),
    ("لندن", "London", "UK"),
    ("باريس", "Paris", "France"),
    ("برلين", "Berlin", "Germany"),
    ("نيويورك", "New York", "USA"),
    ("تورونتو", "Toronto", "Canada"),
]


def _get(url: str, timeout: int = 30):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=timeout)
        .read().decode("utf-8-sig", "replace"))


def _cache(name: str, fn, ttl_h: float = 6.0):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / name
    try:
        if p.exists() and (time.time() - p.stat().st_mtime) < ttl_h * 3600:
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    v = fn()
    if v:
        try:
            p.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return v


def _turn() -> int:
    return int(time.time() // 1800)


# ─────────────────────────── 🕌 مواقيت الصلاة ───────────────────────────

def make_salah(city_index: int | None = None) -> dict | None:
    i = int(city_index if city_index is not None else _turn()) % len(CITIES)
    ar, en, country = CITIES[i]
    day = time.strftime("%Y-%m-%d", time.gmtime())
    def fetch():
        d = _get(f"https://api.aladhan.com/v1/timingsByCity?city={en}"
                 f"&country={country}&method=4")["data"]
        t = d["timings"]
        return {"fajr": t["Fajr"], "dhuhr": t["Dhuhr"], "asr": t["Asr"],
                "maghrib": t["Maghrib"], "isha": t["Isha"],
                "hijri": d["date"]["hijri"], "day": day}
    got = _cache(f"salah_{en.replace(' ', '')}_{day}.json", fetch)
    if not got:
        return None
    t = got
    lines = [f"الفجر {t['fajr']}", f"الظهر {t['dhuhr']}", f"العصر {t['asr']}",
             f"المغرب {t['maghrib']}", f"العشاء {t['isha']}"]
    return {
        "id": f"salah-{en.replace(' ', '')}-{day}",
        "kind": "salah", "theme": "ذكر",
        "hook": f"مواقيت الصلاة النهاردة في {ar} 🕌",
        "lines": lines,
        "title": f"مواقيت الصلاة في {ar} النهاردة 🕌 | {day}",
        "body": (f"مواقيت الصلاة اليوم في {ar} ({country}):\n"
                 + " · ".join(lines) +
                 f"\n\n🌙 التاريخ الهجري: {t['hijri']['day']} "
                 f"{t['hijri']['month']['ar']} {t['hijri']['year']}هـ\n"
                 f"📍 طريقة الحساب: رابطة العالم الإسلامي — api.aladhan.com"),
        "ref": f"🕌 {ar} — {day}",
        "src_lines": ["🕌 المواقيت من api.aladhan.com (طريقة رابطة العالم الإسلامي)",
                      "⏰ المواقيت بتتغير يوميًا — تابعنا لكل يوم جديد."],
        "tags_extra": "#مواقيت_الصلاة #الصلاة #أذان #prayer_times #islam",
        "scenes": ["mosque minaret sunset silhouette", "mosque architecture night",
                   "islamic city skyline minaret", "prayer beads quran table"],
        "source": "🕌 api.aladhan.com",
    }


# ──────────────────────── 🌙 التاريخ الهجري + العدّاد ────────────────────────

EVENTS = [("رمضان", 9, 1), ("عيد الفطر", 10, 1), ("يوم عرفة", 12, 9),
          ("عيد الأضحى", 12, 10), ("السنة الهجرية الجديدة", 1, 1)]


def make_hijri() -> dict | None:
    today = _dt.date.today().strftime("%d-%m-%Y")
    def fetch():
        d = _get(f"https://api.aladhan.com/v1/gToH?date={today}")["data"]["hijri"]
        return {"day": d["day"], "month": d["month"]["ar"],
                "mnum": d["month"]["number"], "year": int(d["year"])}
    cur = _cache(f"hijri_{today}.json", fetch, ttl_h=20)
    if not cur:
        return None
    # أقرب مناسبة جاية (التاريخ بيتحسب من الـAPI نفسه)
    best = None
    for label, m, dd in EVENTS:
        for yy in (cur["year"], cur["year"] + 1):
            try:
                g = _cache(f"h2g_{dd}_{m}_{yy}.json",
                           lambda dd=dd, m=m, yy=yy: _get(
                               f"https://api.aladhan.com/v1/hToG?date="
                               f"{dd:02d}-{m:02d}-{yy}")["data"]["gregorian"]["date"],
                           ttl_h=24 * 30)
                if not g:
                    continue
                dt = _dt.datetime.strptime(g, "%d-%m-%Y").date()
                n = (dt - _dt.date.today()).days
                if n >= 0 and (best is None or n < best[2]):
                    best = (label, dt.strftime("%Y-%m-%d"), n)
            except Exception:
                continue
    lines = [f"التاريخ الهجري النهاردة: {cur['day']} {cur['month']} {cur['year']}هـ"]
    if best:
        lines.append(f"باقي {best[2]} يوم على {best[0]} 📅")
    return {
        "id": f"hijri-{today}", "kind": "hijri", "theme": "وقت",
        "hook": f"التاريخ الهجري النهاردة 🌙 {cur['day']} {cur['month']}",
        "lines": lines,
        "title": (f"التاريخ الهجري النهاردة 🌙 {cur['day']} {cur['month']} "
                  f"{cur['year']}هـ" + (f" | باقي {best[2]} يوم على {best[0]}"
                                        if best else "")),
        "body": ("\n".join(lines) +
                 "\n\n📅 التواريخ محسوبة من التقويم الهجري (api.aladhan.com)."),
        "ref": f"🌙 {cur['day']} {cur['month']} {cur['year']}هـ",
        "src_lines": ["🌙 التاريخ والعدّاد من api.aladhan.com (بلا تخمين)",
                      "📌 تابعنا تعرف المناسبة قبل ميعادها."],
        "tags_extra": "#التقويم_الهجري #رمضان #عيد #hijri #islamic_calendar",
        "scenes": ["crescent moon night sky", "mosque silhouette dusk",
                   "stars long exposure sky", "old lantern warm light"],
        "source": "🌙 api.aladhan.com",
    }


# ─────────────────────── 📖 معلومات محسوبة من القرآن ───────────────────────

def _meta() -> dict:
    def fetch():
        d = _get("https://api.alquran.cloud/v1/meta")["data"]
        s = d["surahs"]["references"]
        return {"n": len(s), "ayahs": sum(int(x["numberOfAyahs"]) for x in s),
                "meccan": sum(1 for x in s if x["revelationType"] == "Meccan"),
                "medinan": sum(1 for x in s if x["revelationType"] == "Medinan"),
                "longest": max(s, key=lambda x: int(x["numberOfAyahs"])),
                "shortest": min(s, key=lambda x: int(x["numberOfAyahs"])),
                "juz": len((d.get("juzs") or {}).get("references") or []) or 30,
                "names": [x["name"] for x in s]}
    return _cache("quran_meta.json", fetch, ttl_h=24 * 30) or {}


def _clean(name: str) -> str:
    from .noor_cats import strip_marks
    return strip_marks(name).replace("سورة", "").strip()


def _qfacts_list() -> list[tuple[str, str]]:
    m = _meta()
    if not m:
        return []
    out = [
        ("عدد سور القرآن الكريم", f"{m['n']} سورة"),
        ("عدد آيات القرآن الكريم", f"{m['ayahs']} آية"),
        ("السور المكية", f"{m['meccan']} سورة"),
        ("السور المدنية", f"{m['medinan']} سورة"),
        ("عدد أجزاء القرآن", f"{m['juz']} جزءًا"),
        ("أطول سورة في القرآن",
         f"{_clean(m['longest']['name'])} — {m['longest']['numberOfAyahs']} آية"),
        ("أقصر سورة في القرآن",
         f"{_clean(m['shortest']['name'])} — {m['shortest']['numberOfAyahs']} آيات"),
    ]
    prophets = ["نوح", "هود", "يوسف", "يونس", "إبراهيم", "محمد", "مريم",
                "لقمان", "طه"]
    found = [p for p in prophets if any(_clean(nm) == p for nm in m["names"])]
    if found:
        out.append(("سور بأسماء أنبياء وأعلام في القرآن", " · ".join(found)))
    return out


def make_qfacts(index: int | None = None) -> dict | None:
    facts = _qfacts_list()
    if not facts:
        return None
    i = int(index if index is not None else (_turn() // 4)) % len(facts)
    key, val = facts[i]
    return {
        "id": f"qfacts-{i}", "kind": "qfacts", "theme": "قرآن",
        "hook": "هل تعلم؟ 📖",
        "lines": [f"{key}: {val}"],
        "title": f"هل تعلم؟ 📖 {key} — {val}",
        "body": (f"{key}: **{val}**\n\n🌍 معلومة محسوبة من بيانات القرآن "
                 "الكريم نفسها (alquran.cloud) — صفر كتابة من الذاكرة."),
        "ref": "📖 معلومات قرآنية",
        "src_lines": ["📖 بيانات: alquran.cloud (بيانات المصحف الرسمية)",
                      "🧩 معلومة واحدة في كل فيديو — تابعنا تعرف أكتر."],
        "tags_extra": "#معلومات_قرآنية #هل_تعلم #القرآن_الكريم #quran #islam",
        "scenes": ["quran book open pages closeup", "old holy quran pages",
                   "islamic calligraphy art", "mosque interior arches"],
        "source": "📖 alquran.cloud",
    }


# ─────────────────────────── 🗣️ أمثال عربية من التراث ───────────────────────────

PROVERBS: list[tuple[str, str]] = [
    ("الصبر مفتاح الفرج", "مهما طال الضيق، الفرج جاي لعند الصابرين."),
    ("من جدّ وجد، ومن زرع حصد", "التعب الحقيقي دايمًا بيتحوّل نتيجة."),
    ("خير الكلام ما قلّ ودلّ", "كلمة قصيرة معنى كبير أحسن من كلام كتير فاضي."),
    ("في التأني السلامة، وفي العجلة الندامة", "استنى شويّة… تصل أحسن من إنك تجري وتقع."),
    ("يد واحدة لا تصفّق", "أي نجاح كبير بيتعمل بأيدٍ كتير، مش بيد واحدة."),
    ("كل تأخيرة فيها خيرة", "اللي اتأخر عنك… ممكن يكون اتحمّاك من حاجة."),
    ("القرش الأبيض ينفع في اليوم الأسود", "الاحتياط للوقت الصعب حكمة مش بخل."),
    ("اطلبوا العلم من المهد إلى اللحد", "التعلّم مش له سن — بيبدأ من الصغر وبيوصل للآخر."),
    ("لا يلدغ المؤمن من جحر مرتين", "اللي اتعلم من غلطته مرة… ما يكرّرهاش."),
    ("من سار على الدرب وصل", "الخطوة البطيئة المستمرة توصل أكتر من الجرية المتقطّعة."),
    ("الباب اللي يجيلك منه الريح… سدّه واستريح", "ابعد عن أسباب التعب بدل ما تعالج النتيجة."),
    ("العين بصيرة والإيد قصيرة", "ساعات الواحد يشوف اللي عايزه ويقدر عليه."),
    ("بعد ما شاب… ودّوه الكتاب", "الفرصة اللي تفوت صعب ترجع زي ما كانت."),
    ("حبل الكذب قصير", "الصدق بيطول، والكذب دايمًا بينكشف."),
    ("مكره أخاك لا بطل", "أحيانًا بتعمل الحاجة مش لأنك عايز، لكن لأن مفيش غيرها."),
    ("إن كان الكلام من فضة… فالسكون من ذهب", "أحيانًا السكوت أرخص وأسلم من أي كلمة."),
    ("الجار قبل الدار", "اسأل عن الجيرة والناس قبل المكان."),
    ("رجع بخفي حنين", "سافر كتير وطلع بإيد فاضية — التعب من غير نتيجة."),
    ("الطيور على أشكالها تقع", "الصاحب بيشبه صاحبه — اختار صحبتك بعناية."),
    ("اللي على راسه بطحة… يحسّس عليها", "اللي بيبرّر كتير… غالبًا فيه حاجة مخبية."),
]


def make_proverb(index: int | None = None) -> dict | None:
    if not PROVERBS:
        return None
    i = int(index if index is not None else (_turn() // 3)) % len(PROVERBS)
    p, meaning = PROVERBS[i]
    return {
        "id": f"proverb-{i}", "kind": "proverb", "theme": "أخلاق",
        "hook": "مثل شعبي… ومعناه 🗣️",
        "lines": [p, meaning],
        "title": f"{p} 🗣️ | مثل عربي ومعناه في 15 ثانية",
        "body": (f"المثل: {p}\nالمعنى: {meaning}\n\n"
                 "🗣️ من التراث العربي (ملك عام) — حكمة بسيطة لكل يوم."),
        "ref": f"🗣️ مثل: {p}",
        "src_lines": ["🗣️ من التراث العربي الشعبي (ملك عام)",
                      "💡 مثل ومعناه كل فيديو — تابعنا."],
        "tags_extra": "#أمثال_عربية #حكمة #اقتباسات #تراث #wisdom #proverbs",
        "scenes": ["old arabic book pages", "arabian tea cups wooden table",
                   "desert palm shadow light", "traditional lantern market"],
        "source": "🗣️ التراث العربي",
    }


MAKERS = {"salah": make_salah, "hijri": make_hijri, "qfacts": make_qfacts,
          "proverb": make_proverb}


def make(kind: str) -> dict | None:
    fn = MAKERS.get(kind)
    if not fn:
        return None
    try:
        return fn()
    except Exception:
        return None
