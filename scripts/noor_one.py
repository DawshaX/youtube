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



# ── 🕰️ قائمة انتظار الطويل (الكيو) ──────────────────────────────────────
# طلب صاحب القناة (2026-10-14): الريلز ٦ بس في اليوم، والباقي **فيديوهات
# طويلة تنزل على الكيو**. يعني الطويل ما ينفعش ينزل مع الريلز في نفس اللحظة
# وبنفس الرشقة — ينزل **مجدول** في خانة من شبكة مواعيد الذروة، ويظهر عند
# المشاهد في وقته (وفوق كده الفيديو يفضل Private لحد الموعد = صفر رشق).
#
# المواعيد مختارة من عادات الجمهور العربي (توقيت القاهرة): بعد الظهر، قبل
# المغرب، بعد العشا، وآخر الليل. الأربعة مبعدين عن بعض مدة كافية.
QUEUE_HOURS = tuple(int(x) for x in (
    os.environ.get("NOOR_LONG_QUEUE_HOURS") or "13,17,21,23").split(","))
QUEUE_MIN_LEAD = int(os.environ.get("NOOR_LONG_QUEUE_LEAD_MIN", "25"))


def _queue_at(now=None) -> str | None:
    """أقرب خانة فاضية في كيو الطويل → UTC ISO (أو None لو الكيو مقفول).

    الخانات المحجوزة محفوظة في ذاكرة المكتبة (``long_queue``) ⇒ إعادة تشغيل
    الدورة ما بتحجزش نفس الخانة مرتين، ومفيش «فيديوين على نفس الساعة».
    """
    if (os.environ.get("NOOR_LONG_QUEUE") or "0") != "1":
        return None
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Africa/Cairo")
    except Exception:
        tz = dt.timezone(dt.timedelta(hours=2))
    local = (now or dt.datetime.now(dt.timezone.utc)).astimezone(tz)
    booked = set(_load().get("long_queue") or [])
    limit = local + dt.timedelta(minutes=QUEUE_MIN_LEAD)
    for add in range(0, 8):
        day = (local + dt.timedelta(days=add)).date()
        for hour in QUEUE_HOURS:
            slot = dt.datetime(day.year, day.month, day.day, hour, 0, tzinfo=tz)
            if slot <= limit:
                continue
            key = slot.strftime("%Y-%m-%dT%H:%M")
            if key in booked:
                continue
            print(f"[one] 🕰️ خانة الكيو: {key} (القاهرة)", flush=True)
            return slot.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def _queue_mark(at: str) -> None:
    """نحجز الخانة فورًا — عشان دورة تانية ما تاخدهاش."""
    st = _load()
    booked = list(st.get("long_queue") or [])
    try:
        import datetime as dt
        key = dt.datetime.strptime(at, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc).strftime("%Y-%m-%dT%H:00")
        from zoneinfo import ZoneInfo
        key = dt.datetime.strptime(at, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc).astimezone(
            ZoneInfo("Africa/Cairo")).strftime("%Y-%m-%dT%H:%M")
    except Exception:
        key = at[:16]
    booked.append(key)
    st["long_queue"] = booked[-60:]
    _save(st)


# ── ⭐ اختيار «الأفضل» مش «أي حاجة» ─────────────────────────────────────
# طلب صاحب القناة: «خليهم الأفضل». يعني النسخة اللي تنزل من الـ٦ دول لازم
# تكون أقوى نسخة متاحة في المكتبة **دلوقتي**، مش أول صف في الطابور.
def _score_item(row: dict, st: dict) -> float:
    """درجة قوة الحلقة من إشارات حقيقية في بياناتها.

    مش درجة ذوق شخصي: بنقيس حاجات بتفرق فعلًا في الاحتفاظ —
    هوك قوي (مش «اتكلم عن…») · طول كلام كافي · فايدة واضحة · مش سلسلة
    اتكررت قريب · مش نفس الإحساس اللي نزل امبارح.
    """
    score = 0.0
    hook = str(row.get("hook") or "").strip()
    spoken = str(row.get("spoken") or "").strip()
    words = len(spoken.split())
    score += min(words / 34.0, 1.6)                 # كلام كافي = وقت مشاهدة
    if 12 <= len(hook.split()) <= 14:
        score += 0.3                                # طول هوك مناسب
    if hook.endswith(("؟", "?")):
        score += 0.5                                # سؤال = فضول
    try:
        from xtrendaw.pro.hooks import is_weak
        if hook and is_weak(hook):
            score -= 1.2                            # «اتكلم عن» = ضعيف
    except Exception:
        pass
    if str(row.get("benefit") or "").strip():
        score += 0.45                               # فايدة واضحة للمشاهد
    if any(ch.isdigit() for ch in hook):
        score += 0.3                                # رقم في الهوك = توقّف
    last_series = str(st.get("last_series") or "")
    if str(row.get("series_id") or "") == last_series:
        score -= 2.0                                # نفس السلسلة = تكرار
    done = st.get("done") or []
    recent_series = [str(d.get("series_id") or "") for d in done[-9:]]
    sid = str(row.get("series_id") or "")
    score -= 1.5 * recent_series.count(sid)         # سلسلة قريبة جدًا
    recent_kinds = [str(d.get("emotion") or "") for d in done[-5:]]
    emo = str(row.get("emotion") or "")
    if emo:
        score -= 0.7 * recent_kinds.count(emo)      # نفس الإحساس مرتين
    return score


def _best_of(rows: list[dict], st: dict) -> dict | None:
    """أعلى درجة، ومع التساوي الأقدم أولًا (ترتيب ثابت = مفيش مفاجآت)."""
    if not rows:
        return None
    scored = []
    for i, row in enumerate(rows):
        try:
            sc = _score_item(row, st)
        except Exception:
            sc = 0.0
        scored.append((-sc, i, row))
    scored.sort(key=lambda x: (x[0], x[1]))
    return scored[0][2]


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
    # ⭐ «الأفضل» مش «أي حاجة»: بنرتّب المرشحين بدرجة قوة حقيقية (هوك ·
    #    طول كلام · فايدة · بُعد عن التكرار) وناخد أعلاها. الطابور الأول
    #    (لفّ العائلات) بقى **احتياطي** لو التسجيل وقع لأي سبب.
    best = _best_of(pool, st)
    if best is not None:
        st["turn"] = int(st.get("turn") or 0) + 1
        _save(st)
        print(f"[one] ⭐ اختيار الأفضل: {best.get('id')} — "
              f"{str(best.get('hook') or '')[:50]}", flush=True)
        return best
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
    # نسجّل الحقول اللي الإحصاء الدرجات بيحتاجها (سلسلة/إحساس) — من غيرها
    # «بُعد عن التكرار» ما كانش هيتحسب صح.
    st.setdefault("done", []).append({
        "id": row["id"], "url": url, "err": err, "kind": row.get("kind"),
        "series_id": row.get("series_id") or "",
        "emotion": row.get("emotion") or "",
        "at": __import__("time").strftime("%Y-%m-%d %H:%M",
                                          __import__("time").gmtime())})
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
    # 🛡️ بوابة أمان (درس 2026-10-16): حلقة «طويلة» نزلت ١٥ ثانية لأن الصوت
    #    رجع ناقص. مستحيل نسمح بده تاني: الطويل المفروض دقايق، ولو طلع أقل
    #    من نص المتوقّع **ما ينزلش** — يتحفظ ونجرّبه تاني بدل ما نحرق القناة.
    if str(row.get("kind")) == "long":
        from xtrendaw import tts as _tts
        want = _tts._expected_sec(str(row.get("spoken") or ""))
        got = float(made.get("duration") or 0)
        if want > 60 and got < want * 0.55:
            print(f"[one] 🛡️ حلقة طويلة قصيرة ({got:.0f}ث من ~{want:.0f}ث) — "
                  "مش هتنزل. اتأجلت.", flush=True)
            _mark(row, "", "short_render")
            return 1
    title = f"{made['lines'][0][:70]} | {row.get('series_title') or 'نور'}"
    tags = ["نور", row.get("series_title") or "خير"]
    pinned = ""
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

    # ── 🎥 المسار الاحترافي للفيديو الطويل ─────────────────────────────────
    # الفيديو الطويل (١٠–٢٠ دقيقة) هو اللي بيجيب وقت المشاهدة والمشتركين،
    # فلازم ياخد ميتاداتا على مقاسه — مش نفس معالجة الشورت:
    #   • **العنوان**: عنوان الجلسة زي ما هو (بالمدة المقيسة). العنوان القديم
    #     كان بيتولّد من أول سطر منطوق + اسم الجلسة ⇒ **مكرّر مرتين** بالحرف
    #     (باج حقيقي اتنشر على القناة: «ستر ورفق: رحلة ٨ دقيقة… | ستر ورفق…»).
    #   • **الوصف**: كان بيتكوّم فيه نص الحلقة كامل (١٥٠٠ كلمة ≈ ٨٥٠٠ حرف)
    #     ويوتيوب بيقصّ عند ٤٩٠٠ ⇒ الفايدة والإسناد والدعوة والهاشتاجات
    #     **كلها كانت بتضيع**. دلوقتي: مدخل قوي → مقتطف → إسناد → دعوة
    #     متنوّعة → هاشتاجات على مقاس الطويل (بلا #shorts) → **فهرس الجلسة**.
    #   • **الفهرس**: من حدود النص الحقيقية + المدة المقيسة (مش تخمين).
    if str(row.get("kind")) == "long":
        try:
            from xtrendaw.pro import integrate as _pro_int
            # المقتطف: أول **جمل كاملة** (مش قصّ في نص الجملة) وسقف ~٩٠ كلمة
            from xtrendaw.noor_next.timeline import sentences as _sents
            picked, acc = [], 0
            for line in _sents(body):
                picked.append(line.strip())
                acc += len(line.split())
                if acc >= 90 or len(picked) >= 4:
                    break
            excerpt = " ".join(picked) or " ".join(body.split()[:90])
            # اسم الجلسة **قبل النقطتين** أنضف كوسم من العنوان الطويل المقصوص
            kw_short = str(row.get("series_title") or "").split(":")[0].strip()
            em = _pro_int.upgrade_metadata(
                row, hook=str(row.get("hook") or ""), body=excerpt,
                sources=[credits] if credits else [], kind="long",
                kw=kw_short,
                reciter=str(row.get("reciter_name") or ""),
            )
            if em.get("title"):
                title = str(em["title"])[:95]
            if em.get("description"):
                desc = str(em["description"])
            if em.get("tags"):
                tags = list(em["tags"])
            pinned = str(em.get("pinned") or "")
            print(f"[one] 🎥 ميتاداتا الطويل: {title[:60]}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[one] ميتاداتا الطويل اتخطت: {type(exc).__name__}", flush=True)
        try:
            from xtrendaw.noor_next.chapters import block as _chblock
            ch = _chblock(row.get("chapters_hint"), len(body.split()),
                          float(made.get("duration") or 0))
            if ch:
                room = 4900 - len(desc)
                if room > 40:
                    desc = desc + "\n\n" + ch[:room]
                    print(f"[one] ⏱️  فهرس الجلسة اتضاف ({ch.count(chr(10))} قسم)",
                          flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[one] الفهرس اتخطى: {type(exc).__name__}", flush=True)
    # 🕰️ الطويل بينزل على **الكيو**: بنحجز له خانة في شبكة مواعيد الذروة
    #    بينزل فيها فعلًا (الفيديو يفضل Private لحد الموعد). الريلز تفضل
    #    فورية زي ما هي — الطلب كان على الطويل بس.
    at = None
    if str(row.get("kind")) == "long":
        at = _queue_at()
        if at:
            _queue_mark(at)
    url, err = runner._publish(made["video"], None, title[:95], desc, tags,
                               synthetic=True, publish_at=at, pinned=pinned)
    if not url and at and err and err not in ("quota_guard", "too_soon",
                                              "duplicate"):
        # احتياطي: لو الجدولة نفسها اترفضت (قناة غير موثّقة مثلًا)، الحلقة
        # **ما تضيعش** — بننزلها فورًا. الأهم إن المحتوى يوصل، مش الموعد.
        print(f"[one] ⚠️ الجدولة مشيت ({err}) — بننزل فورًا", flush=True)
        url, err = runner._publish(made["video"], None, title[:95], desc, tags,
                                   synthetic=True, publish_at=None, pinned=pinned)
        at = None
    if not pinned:
        try:
            from xtrendaw.pro import metadata as _pm
            pinned = _pm.pinned_comment(
                row, hook=str(row.get("hook") or ""),
                kind=str(row.get("kind") or ""))
        except Exception:                      # noqa: BLE001
            pinned = ""
    if err in ("quota_guard", "too_soon"):
        return 2
    if at:
        print(f"[one] 🕰️ الطويل دخل الكيو على {at} (UTC)", flush=True)
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
