#!/usr/bin/env python3
"""ينشر الحلقة الجاية من المكتبة الواحدة. القديم والجديد في نفس الطابور."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SHORT_CAP_BASE = int(os.environ.get("NOOR_SHORTS_PER_DAY", "8"))
LONG_CAP_BASE = int(os.environ.get("NOOR_LONGS_PER_DAY", "4"))


def _today_seed() -> int:
    """بذرة ثابتة من التاريخ — نفس اليوم = نفس النتيجة دايمًا."""
    import zlib
    return zlib.crc32(_day().encode())


def _caps() -> tuple[int, int]:
    """🎛️ سقف اليوم — **مش رقم ثابت**.

    ليه؟ القياس كان صريح: ١١ فيديو في ٢٤ ساعة = **١٠ مشاهدات**، والبحث في
    يوتيوب بعنوان الفيديو بالحرف مش بيرجّعه. يعني يوتيوب **موقّف التوزيع**،
    والأسباب المرجّحة: ١٢ فيديو كل يوم بنفس العدد ونفس الشكل — ده «مصنع»
    مش «قناة» في نظر سياسة المحتوى غير الأصيل.

    فالحل: عدد أقل + **متغيّر كل يوم** (مش عشوائي — محسوب من التاريخ، فمفيش
    احتمال نشر مكرّر أو مواعيد سايبة). النتيجة: القناة تبان بشرية ومتنفّسة،
    وكل فيديو ياخد نصيب أكبر من وقت الرندر والمونتاج.

    ترجع للعدد القديم فورًا: NOOR_SHORTS_PER_DAY=8 · NOOR_LONGS_PER_DAY=4
    و NOOR_DAILY_VARIATION=0.
    """
    if os.environ.get("NOOR_DAILY_VARIATION") != "1":
        return SHORT_CAP_BASE, LONG_CAP_BASE
    seed = _today_seed()
    s_delta = (seed % 4) - 1          # −١ · ٠ · ٠ · +١
    l_delta = ((seed // 4) % 3) - 1   # −١ · ٠ · +١ (حمولة رندر معقولة)
    return (max(1, SHORT_CAP_BASE + s_delta),
            max(1, LONG_CAP_BASE + l_delta))
LIB = ROOT / "data" / "noor_next" / "one_library.jsonl"
LEDGER = ROOT / "state" / "noor_library.json"


def _load() -> dict:
    """يقرأ سجل المكتبة. لو الملف مكسور (تعارض/JSON تالف) بيصلّحه أو يسترجع
    آخر نسخة سليمة — ومش بيرمي استثناء يوقف المصنع كله.
    (بق حقيقي 2026-10-12: علامات تعارض جيت خرّبت الملف والمصنع وقف 10 ساعات.)"""
    if not LEDGER.exists():
        return {"served": []}
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"[one] ⚠️ ذاكرة المكتبة مكسورة ({type(exc).__name__}) — بصلّح…", flush=True)
        fixed = None
        try:
            sys.path.insert(0, str(ROOT / "scripts"))
            import state_guard  # noqa: PLC0415

            text = LEDGER.read_text(encoding="utf-8", errors="replace")
            fixed, how = state_guard.repair_text(text)
            if fixed is None:
                git_text = state_guard._from_git(str(LEDGER.relative_to(ROOT)))
                if git_text:
                    try:
                        json.loads(git_text)
                        fixed, how = git_text, "اتسترجع من git"
                    except Exception:
                        fixed = None
            if fixed:
                LEDGER.write_text(fixed, encoding="utf-8")
                print(f"[one] 🔧 الذاكرة اتصلّحت: {how}", flush=True)
                return json.loads(fixed)
        except Exception as exc2:  # noqa: BLE001
            print(f"[one] ⚠️ الإصلاح مشي ({type(exc2).__name__})", flush=True)
        # آخر حل: نحفظ المكسور جانب ونبدأ نضيف — الدورة تكمل بدل ما تفشل
        try:
            LEDGER.with_suffix(".json.corrupt").write_text(
                LEDGER.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
            )
        except Exception:  # noqa: BLE001
            pass
        print("[one] ⚠️ بدأنا ذاكرة مكتبة جديدة (المكسورة محفوظة جانب)", flush=True)
        return {"served": []}


def _save(data: dict) -> None:
    """كتابة ذرّية: ملف مؤقت ثم نقل — عشان مفيش كتابة نص-نص لو الاتصال اتقطع."""
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(LEDGER)


def _rows() -> list[dict]:
    if not LIB.exists():
        return []
    return [json.loads(l) for l in LIB.read_text(encoding="utf-8").splitlines() if l.strip()]


def _day() -> str:
    """يوم النشر بتوقيت **القاهرة** — مش لوس أنجلوس.

    ليه؟ الجمهور عربي، وجدول المواعيد (noor_grid) بتوقيت القاهرة، وسقف
    اليوم لازم يقيس نفس اليوم اللي الجمهور عايشه. كان بيقيس بتوقيت
    كاليفورنيا ⇒ اليوم بيتقفل ٩–١٠ ساعات قبل ما يوم القاهرة يخلص،
    والمواعيد اللي بعده بتتحسب على يوم تاني.
    """
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Africa/Cairo")
    except Exception:
        tz = dt.timezone(dt.timedelta(hours=2))
    return dt.datetime.now(tz).date().isoformat()


def _counts() -> tuple[int, int]:
    bag = _load().get("day") or {}
    if bag.get("date") != _day():
        return 0, 0
    return int(bag.get("short") or 0), int(bag.get("long") or 0)


def _bump(kind: str) -> None:
    st = _load()
    day = _day()
    bag = st.get("day") or {}
    if bag.get("date") != day:
        bag = {"date": day, "short": 0, "long": 0}
    key = "long" if kind == "long" else "short"
    bag[key] = int(bag.get(key) or 0) + 1
    st["day"] = bag
    _save(st)


def wanted_kind(shorts: int | None = None, longs: int | None = None) -> str | None:
    if shorts is None or longs is None:
        shorts, longs = _counts()
    s_cap, l_cap = _caps()
    # 🎯 طلب صريح من الوركفلو (mode=long / mode=short).
    #    كان الوركفلو بيعمل FLAG وبيمرّره لـnoor_runner — وnoor_one ما كانش
    #    بيقراه أصلًا ⇒ الوضع اليدوي «طويل» كان بيتجاهله ويطلع شورت. الفجوة
    #    دي اتقفلت: الطلب الصريح بيتنفّذ، ولو السقف خلص بنرجع للمنطق العادي.
    forced = (os.environ.get("NOOR_FORCE_FORM") or "").strip()
    if forced == "long" and longs < l_cap:
        return "long"
    if forced == "short" and shorts < s_cap:
        return "short"
    if shorts >= s_cap and longs >= l_cap:
        return None
    if longs >= l_cap:
        return "short"
    if shorts >= s_cap:
        return "long"
    return "long" if (shorts + longs) % 3 == 2 else "short"


def next_item(kind: str | None = None) -> dict | None:
    st = _load()
    done = set(st.get("served") or [])
    last = str(st.get("last_series") or "")
    def ok(row: dict) -> bool:
        if row.get("id") in done or row.get("engine") == "source":
            return False
        is_long = row.get("kind") == "long"
        if kind == "long":
            return is_long
        if kind == "short":
            return not is_long
        return True
    fresh = [r for r in _rows() if ok(r) and r.get("series_id") != last]
    pool = fresh or [r for r in _rows() if ok(r)]
    if not pool:
        return None
    # لفّ بين العائلات عشان القديم والجديد يطلعوا، ومش نوع واحد ياكل الطابور.
    families: dict[str, list[dict]] = {}
    for row in pool:
        families.setdefault(str(row.get("series_id") or row.get("engine") or "عام"), []).append(row)
    turn = int(st.get("turn") or 0) % max(1, len(families))
    key = list(families)[turn]
    st["turn"] = turn + 1
    _save(st)
    return families[key][0]


def _mark(row: dict, url: str = "", err: str = "") -> None:
    st = _load()
    st["served"] = list(dict.fromkeys([*(st.get("served") or []), row["id"]]))
    st["last_series"] = row.get("series_id") or ""
    st.setdefault("done", []).append({"id": row["id"], "url": url, "err": err, "kind": row.get("kind")})
    _save(st)
    if url:
        _bump(str(row.get("kind") or "short"))


def _runner():
    import importlib.util
    name = "noor_runner_live"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "noor_runner.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _publish_life(row: dict) -> int:
    from xtrendaw.noor_next.produce import render
    runner = _runner()
    work = runner.WORK / f"one_{row['id']}"
    made = render(row, work)
    if not made:
        # متتحرقش الحلقة. اللوحة الفاضية مش فيديو، والمحاولة الجاية ممكن تلاقي لقطة.
        print(f"[one] {row.get('id')} اتأجل: مفيش مشاهد مرخّصة كفاية", flush=True)
        return 1
    title = f"{made['lines'][0][:70]} | {row.get('series_title') or 'نور'}"
    src = row.get("source") or ""
    credits = "\n".join(made["credits"]) or "لقطات مرخّصة."
    # ⚠️ درس حقيقي (2026-10-14): الوصف العام كان بيبدأ بـ
    #   «الشخصية: ليل، أصلية للمصنع. أسلوب اللقطات: … — صناعة المصنع»
    #   يعني **ملاحظات إنتاج داخلية** في وش المشاهد. ده (١) بيقول للمشاهد
    #   إن ده محتوى آلي فيقلّ ثقته، (٢) بيحرق أول ١٥٠ حرف — وهي الجزء اللي
    #   يوتيوب بياخده للبحث والاقتراح.
    #   الحل: الوصف يبدأ **بالمحتوى نفسه**، وبعدين الفايدة، وبعدين الإسناد.
    body = (row.get("spoken") or "").strip()
    benefit = str(row.get("benefit") or row.get("source") or "").strip()
    fair = "🤍 محتوى مصنوع بعناية. بلا وجوه حقيقية، وبلا وسائط محفوظة الحقوق."
    desc = "\n\n".join(x for x in (body, benefit, src, credits, fair) if x)
    url, err = runner._publish(made["video"], None, title[:95], desc, ["نور", row.get("series_title") or "خير"], synthetic=True)
    if err in ("quota_guard", "too_soon"):
        return 2
    _mark(row, url or "", err or "")
    print(f"[one] life {row['id']} {url or err}", flush=True)
    return 0 if url or runner.DRY else 1


def _publish_source(row: dict) -> int:
    os.environ["NOOR_ITEM_JSON"] = json.dumps(row, ensure_ascii=False)
    os.environ["NOOR_PLAN"] = "0"
    runner = _runner()
    rc = runner.short_once()
    _mark(row, err="" if rc == 0 else "source_failed")
    print(f"[one] source {row['id']} rc={rc}", flush=True)
    return 0 if rc == 0 else 1


def _unserved(kind: str, engine: str = "life") -> list[dict]:
    done = set(_load().get("served") or [])
    rows = []
    for row in _rows():
        if row.get("id") in done or row.get("engine") != engine or row.get("kind") != kind:
            continue
        rows.append(row)
    return rows


def _diverse(rows: list[dict], count: int) -> list[dict]:
    out = []
    seen = set()
    for row in rows:
        series = row.get("series_id") or row.get("id")
        if series in seen:
            continue
        seen.add(series)
        out.append(row)
        if len(out) == count:
            break
    return out


def opening() -> int:
    """شورتان وفيديو طويل من المكتبة، وبعدها الساعة ترجع عادي."""
    batch = _diverse(_unserved("short"), 2) + _diverse(_unserved("long"), 1)
    if len(batch) < 3:
        print("[one] الافتتاح ناقص شورت أو طويل", flush=True)
        return 1
    published = 0
    for row in batch:
        rc = _publish_life(row)
        if rc == 2:
            print(f"[one] الافتتاح وقف بعد {published} — الحصة أو الوقت", flush=True)
            return 0 if published else 0
        if rc == 0:
            published += 1
            print(f"[one] افتتاح {row.get('kind')} {row.get('id')}", flush=True)
    print(f"[one] الافتتاح نشر {published}", flush=True)
    return 0 if published else 1


def _one_live(kind: str, tries: int = 4) -> int:
    for _ in range(tries):
        row = next_item(kind)
        if not row:
            print(f"[one] مفيش {kind} جديد", flush=True)
            return 1
        try:
            rc = _publish_life(row)
        except Exception as exc:
            print(f"[one] الرندر وقع على {row.get('id')}: {type(exc).__name__}: {exc}", flush=True)
            _mark(row, err=type(exc).__name__)
            continue
        if rc == 0:
            print(f"[one] نزل {kind} {row.get('id')}", flush=True)
            return 0
        if rc == 2:
            return 2
        print(f"[one] {row.get('id')} ما نزلش، هنجرب غيره", flush=True)
    return 1


def first() -> int:
    """أول ريل وأول طويل من المصنع الجديد، وبعدها الساعة تكمل بنفس الشكل."""
    published = 0
    for kind in ("short", "long"):
        rc = _one_live(kind)
        if rc == 0:
            published += 1
        elif rc == 2:
            print(f"[one] وقفنا بعد {published}. الحصة أو الوقت.", flush=True)
            return 0 if published else 2
    print(f"[one] أول دفعة نشرت {published} من 2", flush=True)
    return 0 if published == 2 else 1


def main() -> int:
    if os.environ.get("NOOR_FIRST") == "1":
        return first()
    if not LIB.exists():
        print("[one] المكتبة الواحدة مش موجودة", flush=True)
        return 1
    kind = wanted_kind()
    shorts, longs = _counts()
    if kind is None:
        print(f"[one] سقف اليوم خلص: {shorts} شورت و{longs} طويل", flush=True)
        return 0
    s_cap, l_cap = _caps()
    print(f"[one] اليوم {shorts}/{s_cap} شورت و{longs}/{l_cap} طويل — الجاية {kind}", flush=True)
    for _ in range(3):
        row = next_item(kind)
        if not row:
            print("[one] الطابور خلص", flush=True)
            return 1
        engine = row.get("engine")
        try:
            rc = _publish_source(row) if engine == "source" else _publish_life(row)
        except Exception as exc:
            print(f"[one] الرندر وقع على {row.get('id')}: {type(exc).__name__}: {exc}", flush=True)
            _mark(row, err=type(exc).__name__)
            continue
        if rc == 2:
            return 0
        if rc == 0:
            return 0
    print("[one] ثلاث محاولات وقعت — الساعة دي من غير نشر قديم", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
