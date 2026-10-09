"""🧠 المخطّط الأبدي — نور يعرف هو بيعمل إيه لسنين.

المخزون (كله من مصادر موثّقة، وصفر تكرار بفضل المسجّل):
  quran  : كل السور مقسّمة نوافذ ~٤ آيات      (~١٥٠٠ حلقة)
  tafsir : نفس النوافذ بتدبّر الميسّر          (~١٥٠٠ حلقة)
  hadith : أحاديث صحيحة قصيرة (بخاري/مسلم)    (مئات — تتفلتر تلقائيًا)
  qissa  : قصص الأنبياء من القرآن              (١٨ مقطع)
  asma   : أسماء الله الحسنى بالدليل القرآني   (٩٩)
  athkar : أذكار حصن المسلم                     (بالأبواب)
  dua    : أدعية قرآنية «ربنا…»                (مئات)
  quiz   : كويز «من أي سورة هذه الآية؟»        (٢٨+)
  spirit : روحانيات عامة (سكينة/امتنان/أمل)    (٣٦)
  mujiza : معجزات الأنبياء من نص القرآن        (٢٢ نافذة)
  hamd   : ولله الحمد وخير الله الدائم         (٢٠ نافذة)
  nasr   : الله غالب — فرج ونصر من غير عنف     (٢١ نافذة)

الجدول (NOOR_GRID=1): ١٢ نوع على أيام الأسبوع وساعات القاهرة،
٨ نشرات/يوم منهم ٣ طويلة. التفاصيل في noor_grid.py.

الدوران: كل نوع بياخد دوره — والمسجّل (ledger) على git يعني كل دورة تكمل
من مكان اللي قبلها، مش تعيد. ده اللي يخلي الشغل «أبدي».
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from . import settings

LEDGER = settings.STATE / "noor_ledger.json"
STOCK = settings.STATE / "noor_cache" / "stock"
UA = {"User-Agent": "NoorFactory/1.0 (free Islamic dawah content)"}

# توزيع الأنواع: قرآن أكتر (هو القلب) + حديث + تنويع
# 🆕 2026-10-07: ٢٨ خطوة — كل الأنواع بتنوّع على مدار اليوم
ROTATION = ["quran", "hadith", "asma", "quran", "dua", "qissa", "athkar",
            "quran", "quiz", "spirit", "quran", "salah", "tafsir", "hadith",
            "spirit", "quran", "asma", "hijri", "quran", "proverb", "dua",
            "quran", "qfacts", "qissa", "quran", "hadith", "spirit", "quran",
            "mujiza", "hamd", "nasr", "qissa", "mujiza", "hamd"]

COLLECTIONS = ("bukhari", "muslim", "abudawud", "nasai", "ibnmajah",
               "malik", "nawawi", "dehlawi")

QURAN_HOOKS = ["آية تُريح القلب 🤍", "تلاوة تُسكِن الروح 🕊️", "كلام الله… اسمعها بقلبك",
               "آية لكل قلب تعبان 💛", "دقيقة مع القرآن ✨", "لو قلبك مشغول… اسمع دي",
               "آية افتح بيها يومك 🌅", "تلاوة هادية لقلبك 🌿"]
TAFSIR_HOOKS = ["افهم الآية دي صح 🧩", "تدبّر آية… تغيّر نظرتك", "معنى آية كنت بتقراها ومش فاهمها"]
QISSA_HOOKS = ["قصة من القرآن 🤍", "حكاية فيها عبرة 📖", "قصة من غير ما تتقطع 📚"]


def _number_windows(flat: list[dict]) -> list[dict]:
    """ترقيم النوافذ جوه كل سورة: الجزء ٣ من ٧٢ (بيخلّي المشاهد يكمّل)."""
    from collections import defaultdict
    groups = defaultdict(list)
    for w in flat:
        groups[int(w.get("surah") or 0)].append(w)
    out = []
    for _s, ws in groups.items():
        ws.sort(key=lambda x: int(x.get("frm") or 1))
        for i, w in enumerate(ws, 1):
            w["idx"], w["total"] = i, len(ws)
            out.append(w)
    return out


def _surah_ar(name: str | None) -> str:
    try:
        from .noor_cats import strip_marks
        return strip_marks(name or "").replace("سورة", "").strip() or str(name or "")
    except Exception:
        return str(name or "")


def _ledger() -> dict:
    try:
        d = json.loads(LEDGER.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def done_keys() -> set[str]:
    return set((_ledger().get("done") or {}).keys())


def mark(key: str) -> None:
    d = _ledger()
    d.setdefault("done", {})[str(key)] = time.strftime("%Y-%m-%d %H:%M",
                                                       time.gmtime())
    d["n"] = len(d["done"])
    _save(d)


# ─────────────────────────── المخزون — نوافذ القرآن ───────────────────────────

def windows() -> list[dict]:
    """كل القرآن مقسّم نوافذ ~٤ آيات (بلا تكرار لسنين) — مصدر: alquran.cloud."""
    p = STOCK / "windows.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d:
                if "idx" not in d[0]:
                    d = _number_windows(d)
                    try:
                        p.write_text(json.dumps(d, ensure_ascii=False),
                                     encoding="utf-8")
                    except Exception:
                        pass
                return d
        except Exception:
            pass
    url = "https://api.alquran.cloud/v1/surah"
    data = json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=60).read())["data"]
    wins = []
    for s in data:
        n, num = int(s["numberOfAyahs"]), int(s["number"])
        step = n if n <= 4 else 4
        parts = []
        for frm in range(1, n + 1, step):
            to = min(n, frm + step - 1)
            parts.append({"surah": num, "frm": frm, "to": to,
                          "name": s.get("name", "")})
        # 🎬 ترقيم السلسلة (سورة البقرة ٣ / ٧٢) — بيخلّي المشاهد يكمّل ويشترك
        for i, w in enumerate(parts, 1):
            w["idx"], w["total"] = i, len(parts)
            wins.append(w)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(wins, ensure_ascii=False), encoding="utf-8")
    return wins


# ─────────────────────────── المخزون — أحاديث صحيحة قصيرة ─────────────────────

def hadith_stock(collection: str = "bukhari", limit: int = 600) -> list[dict]:
    """أحاديث صحيحة **قصيرة** (٨–٦٥ كلمة متن) من نفس مصدر المصنع المعتمد.

    الفلترة أمانة: المتن الطويل يُقصّ في الرندر ⇒ بنختار القصير فقط،
    والنص والعنوان من المصدر نفسه (صفر كتابة من الذاكرة).
    """
    p = STOCK / f"hadith_{collection}_short.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d:
                return d[:limit]
        except Exception:
            pass
    from . import noor_build
    try:
        src = noor_build.hadith_text(collection, 1)      # يضمن تحميل الكاش
        _ = src
    except Exception:
        return []
    cache = Path(getattr(noor_build, "CACHE", STOCK))
    big = cache / f"hadith-{collection}.json"
    if not big.exists():
        return []
    data = json.loads(big.read_text(encoding="utf-8"))
    out = []
    for h in data.get("hadiths", []):
        try:
            txt = noor_build._matn(h.get("text") or "")
        except Exception:
            txt = (h.get("text") or "").strip()
        w = len(txt.split())
        if 8 <= w <= 65:
            out.append({"n": int(h.get("hadithnumber") or 0), "words": w})
        if len(out) >= limit:
            break
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


# ─────────────────────────────── بناء السلاسل ────────────────────────────────

def series(kind: str) -> list[tuple[str, dict]]:
    """[(مفتاح, spec)] — بترتيب ثابت لكل نوع."""
    if kind in ("quran", "tafsir"):
        out = []
        for w in windows():
            key = f"{'q' if kind == 'quran' else 't'}-{w['surah']:03d}-{w['frm']:03d}"
            hook = (QURAN_HOOKS if kind == "quran" else TAFSIR_HOOKS)[
                (w["surah"] + w["frm"]) % len(QURAN_HOOKS if kind == "quran"
                                              else TAFSIR_HOOKS)]
            out.append((key, {"kind": "ayah", "surah": w["surah"],
                              "ayah": w["frm"], "ayah_to": w["to"],
                              "theme": "قرآن" if kind == "quran" else "تدبر",
                              "hook": hook, "plan": kind,
                              "series": (f"سلسلة {_surah_ar(w.get('name'))} "
                                         f"({w.get('idx', 1)}/{w.get('total', 1)})")
                              if w.get("total") else ""}))
        return out
    if kind == "hadith":
        out = []
        for col in COLLECTIONS:      # 🆕 ٨ مجموعات (~٣٢ ألف حديث)
            for h in hadith_stock(col):
                out.append((f"h-{col}-{h['n']}",
                            {"kind": "hadith", "collection": col,
                             "index": h["n"], "theme": "حديث",
                             "hook": f"من {col}"}))
        return out
    if kind == "qissa":
        from . import noor_cats
        out = []
        for it in noor_cats.STORIES:
            key = f"s-{it['surah']}-{it['ayah']}"
            hook = it.get("hook") or QISSA_HOOKS[(it["surah"] + it["ayah"]) % len(QISSA_HOOKS)]
            out.append((key, {"kind": "story", "them": "قرآن", "theme": "قرآن",
                              "hook": hook, "who": it["who"],
                              "surah": it["surah"], "ayah": it["ayah"],
                              "ayah_to": it.get("ayah_to")}))
        return out
    if kind == "spirit":
        from . import noor_spirit
        return [(it["id"], it) for it in noor_spirit.series()]
    if kind in ("salah", "hijri", "qfacts", "proverb"):
        from . import noor_more
        if kind == "salah":
            out = []
            for i in range(len(noor_more.CITIES)):
                it = noor_more.make_salah(i)
                if it:
                    out.append((it["id"], it))
            return out
        if kind == "hijri":
            it = noor_more.make_hijri()
            return [(it["id"], it)] if it else []
        wk = time.strftime("%Y-W%W", time.gmtime())
        n_items = (len(noor_more._qfacts_list()) if kind == "qfacts"
                   else len(noor_more.PROVERBS))
        out = []
        for i in range(n_items):
            it = (noor_more.make_qfacts(i) if kind == "qfacts"
                  else noor_more.make_proverb(i))
            if it:
                it = dict(it)
                it["id"] = f"{kind}-{i}-{wk}"
                out.append((it["id"], it))
        return out
    if kind == "athkar":
        from . import noor_cats
        return [(it["id"], it) for it in noor_cats.athkar_pool(200)]
    if kind == "asma":
        from . import noor_cats
        return [(it["id"], it) for it in noor_cats.asma_pool(99, per_run=14)]
    if kind == "dua":
        from . import noor_cats
        return [(it["id"], it) for it in noor_cats.dua_pool(120, per_run=18)]
    if kind == "quiz":
        from . import noor_cats
        return [(it["id"], it) for it in noor_cats.quiz_pool()]
    if kind in ("mujiza", "hamd", "nasr"):
        from . import noor_signs
        return noor_signs.series(kind)
    # أي نوع تاني (ديناميكي) — عنصر واحد من مصدره
    from . import noor_cats
    it = noor_cats.make(kind)
    if not it:
        return []
    return [(str(it.get("id")), it)]


def next_item() -> dict | None:
    """الحلقة الجاية: النوع اللي عليه الدور → أول مفتاح لسه ما اتعملش.

    لو NOOR_FORCE_KIND موجود (جدول اليوم) النوع ده بيتقدّم. في وضع الجدول
    الصارم ما بنسقطش على نوع تاني لو النوع المطلوب فاضي.
    """
    led = _ledger()
    turn = int(led.get("turn") or 0)
    done = done_keys()
    forced = os.environ.get("NOOR_FORCE_KIND", "").strip()
    strict = os.environ.get("NOOR_GRID_STRICT") == "1" and bool(forced)
    order = []
    if forced:
        order.append(forced)
    if not strict:
        for step in range(len(ROTATION) * 2):
            order.append(ROTATION[(turn + step) % len(ROTATION)])
    seen: set[str] = set()
    for kind in order:
        if kind in seen:
            continue
        seen.add(kind)
        try:
            s = series(kind)
        except Exception:
            continue
        for key, spec in s:
            if key in done:
                continue
            spec = dict(spec)
            spec.setdefault("theme", "قرآن")
            spec["id"] = key
            spec["plan_kind"] = kind
            if not forced:
                led["turn"] = (turn + 1) % len(ROTATION)
                _save(led)
            else:
                _save(led)
            return spec
    return None


def stats() -> dict:
    """جردة المخزون — كام حلقة متاحة وكام اتعمل (للتقرير)."""
    out = {"done": len(done_keys()), "kinds": {}}
    for kind in ("quran", "tafsir", "qissa", "spirit"):
        try:
            n = len(series(kind))
        except Exception:
            n = 0
        out["kinds"][kind] = n
    return out
