"""🆕 تصنيفات نور الجديدة (2026-10-06) — بعد بحث ساحة يوتيوب الإسلامي.

أعلى أنواع المحتوى الإسلامي تفاعلًا على الشورتس (نتيجة البحث):
  1) **أسماء الله الحسنى** (٩٩ اسم) — سلاسل + كويزات، بحث متكرر ضخم.
  2) **الأذكار اليومية** (صباح/مساء/نوم/بعد الصلاة/الهم) — أعلى نية بحث يومية.
  3) **الأدعية القرآنية** «ربنا…» — مؤثرة ومنتشرة عالميًا.
  4) **قصص الأنبياء من القرآن** — أقوى محتوى قصصي ديني.
  5) **الكويز: من أي سورة هذه الآية؟** — التفاعل (تعليقات) = وقود الخوارزمية.

قواعد السلامة (زي باقي المصنع — ممنوع كتابة من الذاكرة):
  • api.alquran.cloud — نص عثماني + تلاوة + تفسير ميسّر (مصدر معتمد)
  • api.aladhan.com — أسماء الله الحسنى الـ٩٩
  • hisnmuslim.com — الأذكار الثابتة (حصن المسلم)
  • التعليق الصوتي (edge-tts) للكلام العادي فقط — **ممنوع TTS على كلام الله**:
    أي ذكر فيه آية قرآنية بين ﴿ ﴾ بيتفلتر، والتلاوة دايمًا بصوت قارئ بشري.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request

from . import settings

ALQURAN = "https://api.alquran.cloud/v1"
ASMA_API = "https://api.aladhan.com/v1/asmaAlHusna"
HISN_INDEX = "https://www.hisnmuslim.com/api/ar/husn_ar.json"
UA = "Mozilla/5.0 (compatible; NoorFactory/1.0)"

CATS = ("asma", "athkar", "dua", "story", "quiz")

_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")


def strip_marks(t: str) -> str:
    """يشيل التشكيل للمقارنة (مش للعرض) — النص المعروض دايمًا بالنص العثماني."""
    return _MARKS.sub("", str(t or "")).strip()


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(urllib.parse.quote(url, safe=":/?&=%#"),
                                 headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def _json(url: str, timeout: int = 30):
    return json.loads(_get(url, timeout).decode("utf-8-sig", "replace"))


def _cache_dir():
    d = settings.STATE / "noor_cache" / "cats"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache(name: str, fn, ttl_hours: float = 24.0):
    """كاش طويل (المصادر دي ثابتة) — يخفّف الشبكة ويسرّع الدورة."""
    p = _cache_dir() / name
    try:
        if p.exists() and (time.time() - p.stat().st_mtime) < ttl_hours * 3600:
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    val = fn()
    try:
        p.write_text(json.dumps(val, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return val


def _rot() -> int:
    """مؤشر دوران زمني (نص ساعة) — تنويع مضمون بلا تكرار متقارب."""
    return int(time.time() // 1800)


# ─────────────────────────── الآية الكاملة (نص + تلاوة + تفسير) ───────────────

def ayah_full(s: int, a: int) -> dict:
    """نص عثماني + صوت تلاوة + تفسير ميسّر لآية واحدة (مصدران معتمدان)."""
    d = _json(f"{ALQURAN}/ayah/{int(s)}:{int(a)}/editions/"
              "quran-uthmani,ar.alafasy,ar.muyassar")
    out = {"surah": int(s), "ayah": int(a), "text": "", "tafsir": "",
           "surah_name": "", "audio_ref": ""}
    for e in (d.get("data") or []):
        ident = ((e.get("edition") or {}).get("identifier") or "")
        if ident == "quran-uthmani":
            out["text"] = e.get("text") or ""
            out["surah_name"] = ((e.get("surah") or {}).get("name") or "")
        elif ident == "ar.alafasy":
            out["audio_ref"] = e.get("audio") or ""
        elif ident == "ar.muyassar":
            out["tafsir"] = e.get("text") or ""
    return out


def search_refs(keyword: str, limit: int = 80) -> list[list[int]]:
    """مراجع الآيات اللي فيها الكلمة (نص الفهرس = تفسير؛ فبنتحقق بعدها من الآية نفسها)."""
    d = _json(f"{ALQURAN}/search/{urllib.parse.quote(keyword)}/all/ar")
    matches = ((d.get("data") or {}).get("matches") or [])
    out, seen = [], set()
    for m in matches[:limit * 3]:
        try:
            s = int((m.get("surah") or {}).get("number"))
            a = int(m.get("numberInSurah"))
        except Exception:
            continue
        if (s, a) in seen:
            continue
        seen.add((s, a))
        out.append([s, a])
        if len(out) >= limit:
            break
    return out


# ─────────────────────────────── ١) أسماء الله الحسنى ─────────────────────────

ASMA_HOOKS = ["اسم الله «{n}» ✨", "تعرف معنى «{n}»؟ ✨",
              "«{n}» — أجمل ما تنادي به 🤍", "من أسماء الله: «{n}» ✨"]


def make_asma() -> dict | None:
    try:
        names = _cache("asma99.json",
                       lambda: (_json(ASMA_API) or {}).get("data") or [], ttl_hours=24 * 60)
    except Exception:
        return None
    names = [n for n in names if isinstance(n, dict) and n.get("name")]
    if not names:
        return None
    start = _rot() % len(names)
    for k in range(10):
        n = names[(start + k) % len(names)]
        pure = strip_marks(n["name"]).replace("ال", "", 1) if len(strip_marks(n["name"])) > 4 \
            else strip_marks(n["name"])
        try:
            refs = _cache(f"asma_refs_{n.get('number')}.json",
                          lambda pure=pure: search_refs(pure, limit=10), ttl_hours=24 * 60)
        except Exception:
            refs = []
        for s, a in (refs or [])[:6]:
            try:
                v = ayah_full(s, a)
            except Exception:
                continue
            if pure and pure in strip_marks(v["text"]):
                hook = ASMA_HOOKS[(start + k) % len(ASMA_HOOKS)].format(n=n["name"])
                return {
                    "id": f"asma-{n.get('number')}",
                    "kind": "asma", "theme": "توحيد", "hook": hook,
                    "name": n["name"],
                    "meaning": ((n.get("en") or {}).get("meaning") or ""),
                    "surah": s, "ayah": a, "surah_name": v["surah_name"],
                    "verse": v["text"], "tafsir": v["tafsir"],
                }
    return None


# ─────────────────────────────── ٢) الأذكار (حصن المسلم) ───────────────────────

ATHKAR_WANTED = ["أذكار الصباح والمساء", "أذكار النوم", "أذكار الاستيقاظ من النوم",
                 "الأذكار بعد السلام من الصلاة", "دعاء الهم والحزن",
                 "دعاء الفزع في النوم و من بُلِيَ بالوحشة", "أذكار السفر",
                 "دعاء دخول المسجد", "دعاء الخروج من المسجد", "الذكر بعد الوضوء"]


def _hisn_categories() -> list[dict]:
    d = _json(HISN_INDEX)
    arr = d.get("العربية") if isinstance(d, dict) else None
    if not isinstance(arr, list):
        for v in (d.values() if isinstance(d, dict) else []):
            if isinstance(v, list) and v and isinstance(v[0], dict) and "TITLE" in v[0]:
                arr = v
                break
    return [c for c in (arr or []) if isinstance(c, dict) and c.get("TITLE")]


def make_athkar() -> dict | None:
    """ذكر ثابت من حصن المسلم — **بلا آيات قرآنية** (القرآن للتلاوة البشرية بس)."""
    try:
        cats = _cache("hisn_index.json", _hisn_categories, ttl_hours=24 * 30)
    except Exception:
        return None
    cats = [c for c in cats if str(c.get("TITLE")) in ATHKAR_WANTED]
    if not cats:
        return None
    idx = _rot() % len(cats)
    for k in range(len(cats)):
        c = cats[(idx + k) % len(cats)]
        title = str(c.get("TITLE"))
        url = str(c.get("TEXT") or "").replace("http://", "https://")
        if not url.endswith(".json"):
            continue
        try:
            items = _cache(f"hisn_{c.get('ID')}.json", lambda u=url: _json(u),
                           ttl_hours=24 * 30)
        except Exception:
            continue
        if isinstance(items, dict):
            items = next((v for v in items.values() if isinstance(v, list)), [])
        clean = []
        for it in (items or []):
            t = str((it or {}).get("ARABIC_TEXT") or "").strip()
            if not t or "﴿" in t or "ﷺ" in t:
                continue          # فيها آية أو صيغة صلاة على النبي → نخليها لحلقة تانية
            if len(t.split()) < 4 or len(t.split()) > 60:
                continue
            clean.append({"id": (it or {}).get("ID"), "text": t,
                          "repeat": (it or {}).get("REPEAT") or ""})
        if not clean:
            continue
        i = _rot() % len(clean)
        return {
            "id": f"athkar-{c.get('ID')}-{clean[i]['id']}",
            "kind": "athkar", "theme": "ذكر",
            "hook": f"ذكر يقوّي قلبك 🤍 | {title}",
            "lines": [clean[i]["text"]],
            "source": f"🧿 حصن المسلم — {title}",
            "repeat": clean[i]["repeat"],
        }
    return None


# ─────────────────────────── ٣) أدعية قرآنية («ربنا…») ────────────────────────

DUA_HOOKS = ["دعاء من القرآن لقلبك 🤲", "خد الدعاء ده معاك 🤲",
             "أجمل دعاء تقوله النهاردة 🤲", "دعاء مش هتنساه 🤲"]


def make_dua() -> dict | None:
    try:
        refs = _cache("dua_refs.json",
                      lambda: search_refs("ربنا", limit=120), ttl_hours=24 * 30)
    except Exception:
        return None
    n = len(refs or [])
    if not n:
        return None
    start = _rot() % n
    for k in range(14):
        s, a = refs[(start + k) % n]
        try:
            v = ayah_full(s, a)
        except Exception:
            continue
        if "ربنا" in strip_marks(v["text"]) or "ربى" in strip_marks(v["text"]):
            return {
                "id": f"dua-{s}-{a}", "kind": "dua", "theme": "ذكر",
                "hook": DUA_HOOKS[(start + k) % len(DUA_HOOKS)],
                "surah": s, "ayah": a, "surah_name": v["surah_name"],
                "verse": v["text"], "tafsir": v["tafsir"],
            }
    return None


# ─────────────────────────── ٤) قصص الأنبياء من القرآن ────────────────────────

STORIES = [
    {"who": "يوسف", "surah": 12, "ayah": 4, "hook": "رؤيا يوسف… بداية الحكاية 🌙"},
    {"who": "يوسف", "surah": 12, "ayah": 99, "ayah_to": 101,
     "hook": "آخر الحكاية… كيف انتهى يوسف؟ 👑"},
    {"who": "يعقوب", "surah": 12, "ayah": 86, "hook": "شكوى يعقوب… أجمل شكوى 💛"},
    {"who": "موسى", "surah": 28, "ayah": 7, "ayah_to": 9, "hook": "أم موسى… وأصعب قرار 💙"},
    {"who": "موسى", "surah": 20, "ayah": 39, "ayah_to": 40,
     "hook": "رعاية الله في أصعب لحظة 🕊️"},
    {"who": "موسى", "surah": 28, "ayah": 22, "ayah_to": 24,
     "hook": "موسى… والفرار والأمل 🌵"},
    {"who": "يونس", "surah": 21, "ayah": 87, "ayah_to": 88,
     "hook": "دعاء الخروج من الظلمة 🐋"},
    {"who": "نوح", "surah": 11, "ayah": 41, "ayah_to": 43, "hook": "السفينة… وبركة الله 🚢"},
    {"who": "إبراهيم", "surah": 21, "ayah": 51, "ayah_to": 54,
     "hook": "إبراهيم… سؤال لقومه 🙌"},
    {"who": "زكريا", "surah": 19, "ayah": 2, "ayah_to": 6,
     "hook": "دعاء زكريا… لما تعذّر كل شيء 🤲"},
    {"who": "مريم", "surah": 19, "ayah": 16, "ayah_to": 21, "hook": "مريم… وكرامة الله 🤍"},
    {"who": "عيسى", "surah": 19, "ayah": 29, "ayah_to": 33,
     "hook": "الكلام في المهد… آية الله ✨"},
    {"who": "أيوب", "surah": 21, "ayah": 83, "ayah_to": 84,
     "hook": "أيوب… صبر نال الفرج 🌾"},
    {"who": "آدم", "surah": 7, "ayah": 19, "ayah_to": 23, "hook": "آدم… وبداية التوبة 🌿"},
    {"who": "سليمان", "surah": 27, "ayah": 15, "ayah_to": 19, "hook": "سليمان… وعالم النمل 🐜"},
    {"who": "ذو القرنين", "surah": 18, "ayah": 83, "ayah_to": 88,
     "hook": "ذو القرنين… قوة برحمة 🏔️"},
    {"who": "أصحاب الكهف", "surah": 18, "ayah": 9, "ayah_to": 12,
     "hook": "أصحاب الكهف… المعجزة 🕯️"},
    {"who": "لقمان", "surah": 31, "ayah": 12, "ayah_to": 13,
     "hook": "وصية لقمان… لأولاده 🧡"},
]


def make_story() -> dict | None:
    if not STORIES:
        return None
    it = STORIES[_rot() % len(STORIES)]
    try:
        v = ayah_full(it["surah"], it.get("ayah_to") or it["ayah"])
    except Exception:
        v = {}
    return {
        "id": f"story-{it['surah']}-{it['ayah']}", "kind": "story", "theme": "قرآن",
        "hook": it["hook"], "who": it["who"],
        "surah": it["surah"], "ayah": it["ayah"], "ayah_to": it.get("ayah_to"),
        "surah_name": v.get("surah_name", ""), "verse": v.get("text", ""),
        "tafsir": v.get("tafsir", ""),
    }


# ───────────────────────── ٥) الكويز: من أي سورة هذه الآية؟ ───────────────────

QUIZ_REFS = [[18, 10], [12, 4], [2, 255], [55, 13], [19, 16], [20, 39], [21, 87],
             [28, 7], [36, 1], [67, 3], [94, 5], [103, 1], [49, 13], [31, 14],
             [17, 82], [39, 53], [13, 28], [3, 190], [24, 35], [35, 1], [53, 1],
             [87, 1], [91, 1], [93, 1], [108, 1], [112, 1], [70, 40], [75, 1]]

SURAH_NAMES = ["الكهف", "يوسف", "البقرة", "الرحمن", "مريم", "طه", "الأنبياء",
               "القصص", "يس", "الملك", "الشرح", "العصر", "الحجرات", "لقمان",
               "الإسراء", "الزمر", "الرعد", "آل عمران", "النور", "فاطر", "النجم",
               "الأعلى", "الشمس", "الضحى", "الكوثر", "الإخلاص", "المعارج", "القيامة"]


def make_quiz() -> dict | None:
    if not QUIZ_REFS:
        return None
    turn = _rot()
    s, a = QUIZ_REFS[turn % len(QUIZ_REFS)]
    try:
        v = ayah_full(s, a)
    except Exception:
        return None
    if not v.get("text"):
        return None
    right = v.get("surah_name") or f"سورة {s}"
    right_clean = strip_marks(right).replace("سُورَةُ", "").replace("سورة", "").strip()
    others = [x for x in SURAH_NAMES if strip_marks(x) not in strip_marks(right_clean)]
    picks = [others[(turn + 1) % len(others)], others[(turn + 7) % len(others)]]
    opts = [right_clean] + picks
    opts = [opts[i % 3] for i in (turn % 3, (turn + 1) % 3, (turn + 2) % 3)]
    return {
        "id": f"quiz-{s}-{a}", "kind": "quiz", "theme": "تدبر",
        "hook": "امتحن معرفتك 👀",
        "surah": s, "ayah": a, "surah_name": right,
        "question": "من أي سورة هذه الآية؟",
        "options": [f"سورة {o}" for o in opts],
        "answer": f"سورة {right_clean}",
        "verse": v["text"], "tafsir": v.get("tafsir", ""),
    }


MAKERS = {"asma": make_asma, "athkar": make_athkar, "dua": make_dua,
          "story": make_story, "quiz": make_quiz}


def make(kind: str) -> dict | None:
    fn = MAKERS.get(kind)
    if not fn:
        return None
    try:
        return fn()
    except Exception:
        return None
