#!/usr/bin/env python3
"""مشغّل نور — ينتج وينشر حلقات دينية بجودة عالية، بأمان كامل.

الوضعيات:
  --short            : شورت واحد (آية أو حديث) + نشر لو الكوتة مفتوحة
  --long             : فيديو طويل (سورة كاملة) — مرة كل يوم
  --cycle            : اللي محتاج يتعمل دلوقتي (شورت كل ساعة + طويل يوميًا)

حراسات السلامة (سياسات يوتيوب 2026 + حقوق الملكية):
  1) نص الآية/التفسير من API (مفيش كتابة من الذاكرة) — صفر أخطاء شرعية.
  2) الحديث من مجموعات صحيحة بالـAPI بالنص الأصلي + رقمه + اسم الكتاب.
  3) التلاوة من مصدر بيسمح بالاستخدام التعليمي + **ننسب القارئ باسمه**.
  4) بلا موسيقى خالص (خطر Content ID = صفر).
  5) إفصاح تلقائي عن الوسائط المولّدة (containsSyntheticMedia) لو استخدمنا AI.
  6) فحص التكرار: مفيش آية/حديث يتكرر قبل ما يخلص المخزون.
  7) حارس الكوتة: 1,600 وحدة للرفعة → مش بنحرق حصة على محاولات فاشلة.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
WORK = ROOT / "work" / "noor"
STATE = ROOT / "state" / "noor_state.json"

# قصص/سور للفيديو الطويل بالتبادل (السلامة: سور قصيرة معروفة)
# (الاسم، السورة، الثيم، حد الآيات، إضافات [(سورة، حد)]) — الطويل لازم
# يعدّي 3 دقايق عشان يوتيوب ما يعتبرهوش شورت (ساعات المشاهدة بتحسب للمونيتايزيشن)
LONG_PLAN = [
    ("الرحمن", 55, "رحمن", 78, []),                     # ~5.5 دقيقة
    ("الملك والقلم", 67, "ملك", 30, [(68, 52)]),        # إضافة ~6.5 دقيقة
    ("يس", 36, "يس", 60, [(37, 20)]),
    ("الواقعة", 56, "واقعة", 60, [(57, 29)]),
    ("الرحمن والملك", 55, "رحمن", 40, [(67, 30)]),
]


def _load() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"shorts": [], "longs": [], "bad_reciters": []}


def _save(d: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                     encoding="utf-8")


DRY = os.environ.get("NOOR_DRY") == "1"



def _slots() -> list[int]:
    """ساعات النشر (UTC) — الفيديو بيتحجز عليها فبيتنشر لوحده في وقته.

    يوتيوب بيدّي 6 رفعات بالـAPI في اليوم (10,000 وحدة ÷ 1,600). عشان القناة
    تنشر على مدار اليوم كله، بنرفع الرفعة وبنحجزها على الساعة الجاية في
    القائمة (publishAt) — فالجمهور يشوف نشر متوزّع، والحصة محترمة.
    """
    from xtrendaw import settings
    # لو القناة بقى عندها أكتر من مشروع جوجل (حصة أكبر) → مواعيد أكتر تلقائيًا:
    #  24 رفعة/يوم (4 مشاريع) = نشرة كل ساعة بالظبط
    #  12 رفعة/يوم (مشروعين)   = نشرة كل ساعتين
    cap = settings.YOUTUBE_DAILY_CAPACITY
    raw = os.environ.get("NOOR_SLOTS", "")
    if not raw:
        if cap >= 24:
            raw = ",".join(str(h) for h in range(24))
        elif cap >= 12:
            raw = ",".join(str(h) for h in range(0, 24, 2))
        else:
            raw = "5,9,13,16,19,22"
    out = []
    for x in raw.split(","):
        try:
            h = int(x.strip())
            if 0 <= h <= 23:
                out.append(h)
        except ValueError:
            continue
    return sorted(set(out)) or [5, 9, 13, 16, 19, 22]


def _next_slot(used: list[str]) -> str | None:
    """أقرب ساعة نشر فاضية النهاردة (UTC) — ولا None لو اليوم اتغطى."""
    now = time.gmtime()
    today = time.strftime("%Y-%m-%d", now)
    cur = now.tm_hour * 60 + now.tm_min
    for h in _slots():
        tag = f"{today}T{h:02d}"
        if tag in used:
            continue
        if h * 60 - cur >= 12:              # لازم يفضل 12 دقيقة قبل الموعد
            return f"{today}T{h:02d}:00:00Z"
    return None


def _publish(video, cover, title, desc, tags, synthetic=False):
    from xtrendaw import settings, state
    if DRY:
        return None, "dry_run"
    from xtrendaw.publish import youtube as yt
    cap = settings.DAILY_CAP or 6
    if state.published_today_pt() >= cap:
        return None, "quota_guard"
    url, err = yt.publish(video, title, desc, tags, cover=cover,
                          synthetic=synthetic, category="27")
    if url and "watch?v=" in url:
        vid = url.split("watch?v=")[-1].split("&")[0]
        state.push_published({"id": vid, "title": title, "kind": "noor",
                              "ts": time.time()})
        if at:
            st.setdefault("slots", []).append(at[:13])       # اتشغلت الساعة دي
            _save(st)
    return url, err


def _vault(video, cover, meta) -> str:
    """يخزّن الحلقة في الخزّان (لو فيه مكان) — وتتنشر أول ما الحصة تفتح."""
    try:
        from xtrendaw import noor_vault
        if not noor_vault.can_push():
            return ""
        return noor_vault.push(video, cover, meta) or ""
    except Exception as exc:                      # noqa: BLE001
        print(f"[vault] ✗ تخزين فشل: {type(exc).__name__}", flush=True)
        return ""


def short_once(tries: int = 3) -> int:
    """ينتج شورت واحد (آية/حديث) وينشره لو الكوتة مفتوحة.

    🛡️ لو عنصر فشل (نص/تلاوة/مشهد)، بنسجّله كـ«مكسور» ونجرّب عنصر تاني —
    الدورة ما تفشلش أبدًا بسبب عنصر واحد (بق حقيقي 2026-09-21).
    """
    st0 = _load()
    broken = set(st0.get("broken", []))
    for attempt in range(tries):
        rc = _short_one()
        if rc == 0:
            return 0
        # العنصر اللي فشل يتسجّل عشان ما نرجعش له
        try:
            from xtrendaw import noor_pool
            done = {str(x.get("id")) for x in noor_pool.history()}
            last = (st0.get("shorts") or [None])[-1]
            _ = last
            st_now = _load()
            tried = str(st_now.get("last_try") or "")
            if tried:
                broken.add(tried)
            st_now["broken"] = sorted(broken)
            _save(st_now)
        except Exception:
            pass
        print(f"[noor] ↻ محاولة {attempt + 2}/{tries} بحلقة تانية…", flush=True)
    return 1


def _short_one() -> int:
    """حلقة واحدة فعلية (من غير منطق الإعادة)."""
    from xtrendaw import noor_build, noor_pool
    item = noor_pool.pick()
    _st = _load()
    _st["last_try"] = item["id"]
    _save(_st)
    wid = f"short_{int(time.time())}"
    work = WORK / wid
    work.mkdir(parents=True, exist_ok=True)
    print(f"[noor] 🎬 حلقة {item['kind']} · ثيم {item['theme']} · قارئ "
          f"{item.get('reciter')} · {item['id']}", flush=True)

    if item["kind"] == "reel":
        # 🎬 ريلز الثيم: ٣ آيات + تعليق + تطبيق (لحد ٣ دقايق) — صوت من أوله لآخره
        from xtrendaw import noor_premium as np2
        from xtrendaw.noor_pool import APPLY
        res = np2.render({
            "ayahs": item["ayahs"], "reciter": item.get("reciter", "husary"),
            "scenes": item.get("scenes"), "hook": item["hook"],
            "outro": APPLY.get(item["theme"], "تابعنا… فيديو جديد كل ساعة"),
            "brand": f"نور — {item['theme']}", "meaning": None}, work)
        title = f"{item['hook']} | {item['theme']} 🤍"
        body = f"آيات عن {item['theme']} · {res['ayahs_count']} آيات"
        src_line = f"🎙️ تلاوة: {res['reciter']}"
    elif item["kind"] == "hadith":
        res = noor_build.build_hadith_short(item, work)
        title = f"{item['hook']} — حديث اليوم 📖"
        body = res["text"]
        src_line = f"📖 {res['book']} — حديث رقم {res['number']}"
    else:
        from xtrendaw import noor_premium as np
        from xtrendaw.noor_pool import APPLY
        res = np.render({"surah": item["surah"], "ayah": item["ayah"],
                         "ayah_to": item.get("ayah_to"),
                         "reciter": item.get("reciter", "husary"),
                         "scenes": item.get("scenes"),
                         "hook": item.get("hook"),
                         "outro": APPLY.get(item.get("theme", ""),
                                            "تابعنا… آية وحديث كل ساعة")}, work)
        short = (res["text"][:60] + "…") if len(res["text"]) > 60 else res["text"]
        title = f"{item['hook']} — آية وسكينة ﴿{res['surah']}﴾"
        body = res["text"]
        src_line = f"🎙️ تلاوة: {res['reciter']}"

    tags = ["قرآن", "تلاوة", "إسلاميات", "أدعية", "ذكر", "shorts", "quran",
            "islamic", "تفسير", "هدوء"][:15]
    desc = (
        f"{body}\n\n"
        f"{src_line}\n"
        f"المصادر: نص القرآن والتفسير من alquran.cloud · التلاوة من "
        f"islamic.network (تُنسب للقارئ) · مشاهد برخص حرة (Pexels/Pixabay).\n"
        f"لا موسيقى في هذا الفيديو.\n\n"
        f"🤍 شاركها لو عجبتك — واكتب في تعليق: إيه اللي غيرت فيك الآية دي؟\n"
        f"قناة «نور»: آية وسكينة كل ساعة، وحديث صحيح، وسورة كاملة كل يوم.\n\n"
        f"#قرآن #تلاوة #إسلاميات #ذكر #shorts #حديث #تفسير"
    )
    url, err = _publish(res["video"], res.get("cover"), title[:95], desc, tags)
    status = "📺 اتنشر" if url else f"⏸ اتخزن ({err})"
    vault_url = ""
    if not url and not DRY:
        vault_url = _vault(res["video"], res.get("cover"),
                           {"kind": "noor", "title": title, "tags": ",".join(tags),
                            "caption": desc, "live_clips": 1, "synthetic": False})
    noor_pool.mark_done(item, str(res["video"]), url or vault_url)
    st = _load()
    st.setdefault("shorts", []).append({
        "id": item["id"], "kind": item["kind"], "theme": item["theme"],
        "title": title, "reciter": item.get("reciter", ""),
        "video": str(res["video"]),
        "url": url or "", "vault": vault_url, "err": err,
        "at": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
        "duration": round(res.get("duration", 0), 1)})
    _save(st)
    print(f"[noor] {status} — {url or vault_url}", flush=True)
    print(f"[noor] ⏱️ مدة {res.get('duration', 0):.1f}ث · ملف "
          f"{res['video'].stat().st_size/1e6:.1f}MB", flush=True)
    if DRY:
        print("[noor] 🧪 معاينة فقط — مفيش رفع ومفيش تخزين", flush=True)
        return 0
    _site_sync()
    return 0 if (url or vault_url) else 1


def long_once() -> int:
    """فيديو طويل: سورة كاملة (مرة كل يوم) — ده محرّك ساعات المشاهدة."""
    from xtrendaw import noor_build
    st = _load()
    idx = len(st.get("longs", [])) % len(LONG_PLAN)
    name, surah, theme, maxa, extra = LONG_PLAN[idx]
    work = WORK / f"long_{surah}_{int(time.time())}"
    print(f"[noor] 🎥 فيديو طويل: {name}", flush=True)
    reciters = ["husary", "minshawi", "shatri", "ghamdi"]
    rec = reciters[len(st.get("longs", [])) % len(reciters)]
    res = noor_build.build_long_surah(surah, work, reciter=rec, theme=theme,
                                      max_ayahs=maxa, extra=extra)
    dur_min = res["duration"] / 60
    title = f"سورة {name} كاملة | تلاوة هادئة تريح القلب 🌙"
    if dur_min < 4:
        print(f"[noor] ⚠️ الفيديو قصير ({dur_min:.1f} دقيقة) — ممكن للشورتس الطويلة")
    tags = ["قرآن", name, "تلاوة", "سورة", "إسلاميات", "quran", "relaxing",
            "تلاوة هادئة", "sleep quran"]
    desc = (
        f"تلاوة سورة {name} كاملة بصوت القارئ "
        f"{'محمود خليل الحصري' if rec == 'husary' else 'محمد صديق المنشاوي' if rec == 'minshawi' else 'أبو بكر الشاطري' if rec == 'shatri' else 'سعد الغامدي'}.\n"
        f"مدة التلاوة: {dur_min:.1f} دقيقة · عدد الآيات: {res['ayahs']}\n\n"
        f"نص القرآن الكريم والتفسير: alquran.cloud\n"
        f"التلاوة: islamic.network (حُقوق التلاوة لأصحابها — تُنسب للقارئ)\n"
        f"المشاهد: مكتبات مجانية برخص حرة (Pexels/Pixabay)\n"
        f"بدون موسيقى — للتلاوة والتدبر.\n\n"
        f"#قرآن #تلاوة #" + name
    )
    url, err = _publish(res["video"], res.get("cover"), title[:95], desc, tags)
    vault_url = ""
    if not url and not DRY:
        vault_url = _vault(res["video"], res.get("cover"),
                           {"kind": "noor_long", "title": title,
                            "tags": ",".join(tags), "caption": desc,
                            "live_clips": 1})
    st = _load()
    st.setdefault("longs", []).append({
        "surah": name, "ayahs": res["ayahs"], "reciter": rec,
        "video": str(res["video"]), "url": url or "", "vault": vault_url,
        "at": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
        "duration": round(res["duration"], 1), "err": err})
    _save(st)
    print(f"[noor] {'📺 اتنشر' if url else '⏸ اتخزن'} — {url or vault_url} "
          f"({dur_min:.1f} دقيقة)", flush=True)
    _site_sync()
    return 0




# ─────────────────────── واجهة الموقع (مجانية وبلا حدود) ───────────────────────
SITE_JSON = ROOT / "public" / "noor.json"
REC_NAMES = {"husary": "محمود خليل الحصري", "minshawi": "محمد صديق المنشاوي",
             "shatri": "أبو بكر الشاطري", "ghamdi": "سعد الغامدي"}


def _site_sync() -> None:
    """يحدّث قائمة الموقع: كل حلقة اتنشرت أو اتخزنت بتبان على صفحة نور.

    الموقع على GitHub Pages (مجاني وبلا حد نشر) — يعني «نشر كل ساعة» حقيقي:
    كل دورة بتضيف الحلقة للصفحة فورًا، حتى والكوتة مقفولة على يوتيوب.
    """
    try:
        st = _load()
        from xtrendaw import noor_vault
        spare = []
        try:
            for e in noor_vault.pending():
                m = e.get("meta") or {}
                spare.append({"title": m.get("title", ""), "kind": m.get("kind", ""),
                              "theme": m.get("theme", ""),
                              "reciter_name": REC_NAMES.get(m.get("reciter", ""), ""),
                              "duration": float(m.get("duration") or 0),
                              "at": m.get("at", ""),
                              "video_url": e.get("asset", {}).get("browser_download_url", ""),
                              "cover_url": (e.get("cover") or {}).get("browser_download_url", "")})
        except Exception:
            spare = []
        eps = []
        import re as _re
        for s in reversed(st.get("shorts", [])[-40:]):
            _yt = s.get("url", "") or ""
            _m = _re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{6,})", _yt)
            eps.append({"yt_id": _m.group(1) if _m else "",
                        "title": s.get("title", ""), "kind": s.get("kind", "ayah"),
                        "theme": s.get("theme", ""),
                        "reciter_name": REC_NAMES.get(s.get("reciter", ""), ""),
                        "duration": float(s.get("duration") or 0),
                        "at": s.get("at", ""), "youtube": s.get("url", "")})
        for l in reversed(st.get("longs", [])[-10:]):
            eps.append({"title": l.get("title", ""), "kind": "long",
                        "theme": "", "duration": float(l.get("duration") or 0),
                        "at": l.get("at", ""), "youtube": l.get("url", "")})
        # ✅ المتاح للعرض فورًا (خزّان) يمشي الأول — عشان الصفحة ما تفضاش أبدًا
        all_eps = spare + eps
        seen, uniq = set(), []
        for e in all_eps:
            k = (e.get("title"), e.get("at"))
            if k in seen or not (e.get("video_url") or e.get("youtube")):
                continue
            seen.add(k)
            uniq.append(e)
        SITE_JSON.parent.mkdir(parents=True, exist_ok=True)
        SITE_JSON.write_text(json.dumps(
            {"at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
             "count": len(uniq), "episodes": uniq[:60]},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[noor] 🌐 الموقع اتحدّث: {len(uniq)} حلقة معروضة", flush=True)
    except Exception as exc:                      # noqa: BLE001
        print(f"[noor] ⚠ تحديث الموقع فشل: {type(exc).__name__}", flush=True)


def _fill_quota(max_n: int = 6) -> int:
    """يرفع كل الحلقات الجاهزة من الخزّان لحد ما حصة يوتيوب تخلص.

    ليه؟ عشان أول ثانية الحصة تفتح (منتصف ليل PT = 10:00 بتوقيتك) تنزل الرفعات
    الستة كلها مرة واحدة، كل واحدة محجوزة على ساعتها — بدل ما نستنى 6 دورات
    ساعية. صفر وحدة زيادة: أي فشل (حصة/شبكة) بيوقف الحلقة فورًا.
    """
    if DRY:
        return 0
    from xtrendaw import noor_vault, settings, state
    done = 0
    while done < max_n:
        if state.published_today_pt() >= (settings.DAILY_CAP or 6):
            break
        try:
            if noor_vault.count() == 0:
                break
        except Exception:
            break
        if _publish_spare() != 0:
            break                      # فشل (حصة خلصت أو الشبكة) — نوقف بهدوء
        done += 1
        time.sleep(6)                  # فاصل صغير بين الرفعات
    if done:
        print(f"[noor] ⚡ اترفع {done} حلقة جاهزة من الخزّان في الدورة دي", flush=True)
    return done


def _publish_spare() -> int:
    """يرفع أقدم حلقة من الخزّان على يوتيوب (مفيش رندر = أسرع وأرخص)."""
    from xtrendaw import noor_vault, settings, state
    if DRY:
        return 1
    cap = settings.DAILY_CAP or 6
    if state.published_today_pt() >= cap:
        return 1
    got = noor_vault.take_oldest(WORK / "spare")
    if not got:
        return 1
    meta = got["meta"] or {}
    title = str(meta.get("title") or "قرآن وتدبّر")
    print(f"[noor] 📤 رفع حلقة من الخزّان: {title[:60]}", flush=True)
    st = _load()
    at = _next_slot(st.get("slots", []))
    from xtrendaw.publish import youtube as yt
    url, err = yt.publish(got["video"], title[:95],
                          str(meta.get("caption") or ""),
                          [x for x in str(meta.get("tags") or "").split(",") if x],
                          cover=got["cover"], synthetic=bool(meta.get("synthetic")),
                          category="27", publish_at=at)
    if not url:
        print(f"[noor] ⏸ الرفع من الخزّان فشل ({err}) — الحلقة رجعت مكانها",
              flush=True)
        return 1
    vid = url.split("watch?v=")[-1].split("&")[0]
    state.push_published({"id": vid, "title": title, "kind": "noor",
                          "ts": time.time()})
    if at:
        st.setdefault("slots", []).append(at[:13])
        _save(st)
    noor_vault.drop(got["entry"])
    st.setdefault("shorts", []).append({
        "id": "vault:" + str(got["entry"].get("name")), "kind": "vault",
        "video": "", "url": url, "at": time.strftime("%Y-%m-%d %H:%M",
                                                     time.gmtime())})
    _save(st)
    print(f"[noor] 📺 اتنشر من الخزّان — {url}", flush=True)
    return 0


def cycle() -> int:
    """دورة الساعة: ارفع من الخزّان لو الحصة مفتوحة، وإلا ارندر/خزّن.

    الترتيب ده مقصود: الحلقة الجاهزة بتترفع فورًا (صفر وقت رندر)، والرندر
    بيشتغل بس لما يكون فيه فرصة نشر حقيقية أو مكان في الخزّان.
    """
    from xtrendaw import noor_vault, settings, state
    st = _load()
    today = time.strftime("%Y-%m-%d", time.gmtime())
    did_long = any(str(l.get("at", "")).startswith(today)
                   for l in st.get("longs", []))
    cap = settings.DAILY_CAP or 6
    left = cap - state.published_today_pt()
    if left > 0:
        try:
            n = noor_vault.count()
        except Exception:
            n = 0
        if n > 0:
            # ⚡ املأ الحصة الموجودة: ارفع الجاهز (وممكن أكتر من حلقة في الدورة)
            got = _fill_quota(max_n=min(left, 6))
            if got and state.published_today_pt() >= cap:
                return 0                      # الحصة اتقفلت — نستنى الدورة الجاية
            if got:
                return 0                      # اترفع جاهز = الدورة دي نجحت
        if not did_long:
            print(f"[noor] فيديو اليوم الطويل (فاضل {left} رفعة)", flush=True)
            return long_once()
        return short_once()
    # الحصة مقفولة: ننتج للخزّان (لو فيه مكان) ونستريح لو مليان
    try:
        if not noor_vault.can_push():
            # 🧹 دورة صيانة: الخزّان مليان (الحصة مقفولة) — بننضّفه ونطمّن
            # على الجاهز بدل ما نحرق وقت رندر على حلقات مش هتتنشر.
            print("[noor] 🧹 الخزّان مليان والحصة مقفولة — دورة صيانة", flush=True)
            try:
                n = noor_vault.dedupe()
                print(f"[noor] 🧹 نسخ مكررة اتشالت: {n}", flush=True)
            except Exception as exc:              # noqa: BLE001
                print(f"[noor] ⚠ الصيانة: {type(exc).__name__}", flush=True)
            _site_sync()
            return 0
    except Exception:
        pass
    return short_once()


def purge(ids: list[str]) -> int:
    """🗑️ حذف حلقات مرفوعة + تنضيفها من الذاكرة.

    ليه؟ أي حلقة اترفعت بالمحرك القديم (اللي كان فيه فترات صمت بتقتل الفيديو)
    لازم تختفي من القناة، والذاكرة (السجل اليومي والإحصاءات) تتظبط معاها.
    """
    sys.path.insert(0, str(ROOT))
    from xtrendaw import state
    from xtrendaw.publish import youtube as yt

    want = [v.strip() for v in ids if v and v.strip()]
    if not want:
        print("[purge] مفيش معرّفات", flush=True)
        return 1
    done: list[str] = []
    for v in want:
        print(f"[purge] 🗑️ بنحذف {v} …", flush=True)
        if yt.delete(v):
            done.append(v)
            print(f"[purge] ✓ اتحذف {v}", flush=True)
    if done:
        try:
            log = [p for p in state.published_log() if p.get("id") not in done]
            state._wr(state.PUBLISHED_FILE, log)
        except Exception as exc:
            print(f"[purge] ⚠ ذاكرة الإحصاءات: {type(exc).__name__}", flush=True)
        st = _load()
        st["shorts"] = [s for s in st.get("shorts", [])
                        if s.get("id") not in done]
        _save(st)
    print(f"[purge] ✅ اتحذف {len(done)}/{len(want)}", flush=True)
    return 0 if len(done) == len(want) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--short", action="store_true")
    g.add_argument("--long", action="store_true")
    g.add_argument("--cycle", action="store_true")
    g.add_argument("--purge", nargs="+", metavar="VIDEO_ID")
    a = ap.parse_args()
    sys.path.insert(0, str(ROOT))
    if a.short:
        return short_once()
    if a.long:
        return long_once()
    if a.purge:
        return purge(a.purge)
    return cycle()


if __name__ == "__main__":
    raise SystemExit(main())
