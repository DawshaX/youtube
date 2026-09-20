# حلقة المصنع الدائمة v3 — كل دورة حلقة جديدة: عين ← ترند ← معرفة ← مخزون (بلا تكرار)
# سياسة الصوت: السحابة (edge-tts) ترندر أي موضوع · محليًا نرندر اللي ليه مخزون صوت فقط
# النشر معتمد من صاحب القناة — بينشر فعليًا أول ما الاعتمادات تتوفر (فشل آمن)
# التشغيل: python3 scripts/factory_loop.py  (XT_FACTORY_CYCLE بالثواني، الافتراضي 3600 = ساعي)
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PUBLISH_YOUTUBE", "1")
os.environ.setdefault("XT_NET_FOOTAGE", "1")
os.environ.setdefault("XT_SCENE_CUT", "2.0")

STATUS_PATH = ROOT / "data" / "factory_status.json"
META_DIR = ROOT / "data" / "publish_meta"
POOLS = Path(os.environ.get("XT_VOICE_POOLS", "/home/user/voice_pools"))
CYCLE = int(os.environ.get("XT_FACTORY_CYCLE", "3600"))
# --once: دورة واحدة تنتهي (لسير GitHub Actions) · --no-upload: رندر بلا نشر
ONCE = os.environ.get("XT_FACTORY_ONCE", "") == "1"
NO_PUBLISH = os.environ.get("XT_FACTORY_NO_PUBLISH", "") == "1"


def _load_status() -> dict:
    if STATUS_PATH.exists():
        try:
            return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"cycles": 0, "renders": [], "publish_attempts": [], "radar": [], "eye": []}


def _save_status(s: dict) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def _log(s: dict, key: str, entry: dict, keep: int = 40) -> None:
    s.setdefault(key, []).append(entry)
    s[key] = s[key][-keep:]


def _edge_tts_ok() -> bool:
    try:
        import asyncio
        import edge_tts

        async def _probe() -> None:
            c = edge_tts.Communicate("اختبار", "ar-EG-SalmaNeural")
            await asyncio.wait_for(c.save("/tmp/tts_probe.mp3"), timeout=25)

        asyncio.run(_probe())
        return True
    except Exception:
        return False


def _tts_adapter(pool: Path) -> None:
    """تركيب مُصدر صوت من مخزون الحلقة بنفس عقد synthesize_line (محلي فقط)."""
    from xtrendaw import tts

    def arena_line(text, lang, out_dir, name="line", rate=None, pitch=None, voice=None):
        idx = int(name.replace("seg", "")) if name.startswith("seg") else 0
        src = pool / f"seg{idx}.mp3"
        if not src.exists():
            src = pool / "seg0.mp3"
        wav = Path(out_dir) / f"{name}.wav"
        tts.to_wav(src, wav)
        dur = tts.probe_duration(wav)
        ws = text.split()
        step = dur / max(1, len(ws))
        words = [{"word": w, "start": round(j * step, 3),
                  "end": round(min(dur, (j + 1) * step), 3)} for j, w in enumerate(ws)]
        return {"wav": wav, "duration": dur, "timing_source": "voice-pool", "words": words}

    tts.synthesize_line = arena_line


def _brain_topic() -> dict | None:
    """المخ الطبيعي: طلبات ← عين ← ترند ← معرفة. بمعرّف مضمون."""
    from xtrendaw import brain, content
    t = brain.generate(content.load_topics(), want="auto")
    if t and not t.get("id"):
        t["id"] = "auto-" + content.fingerprint(t)[:10]
    return t


def _local_pool_topic() -> dict | None:
    """محليًا (edge مقفول): أول موضوع ثابت المعرف عنده مخزون صوت ولسه ما اتعملش."""
    from xtrendaw import content, state

    cands: list[dict] = []
    for base in (ROOT / "data" / "eye_topics.json", ROOT / "data" / "eye_consumed.json"):
        if base.exists():
            try:
                cands += [t for t in json.loads(base.read_text(encoding="utf-8")) if t.get("id")]
            except Exception:
                pass
    cands += [t for t in content.load_topics() if t.get("id")]

    for t in cands:
        if state.fingerprint_seen(t):
            continue
        vid = ROOT / "content" / "vids" / f"{t['id']}.mp4"
        if vid.exists() and vid.stat().st_size > 1_000_000:
            return t  # اتعمل قبل كده — محتاج نشر/تثبيت بس
        if (POOLS / t["id"]).is_dir() and list((POOLS / t["id"]).glob("seg*.mp3")):
            return t
    return None


def _caption_with_credits(topic: dict, credits: list[str]) -> str:
    from xtrendaw import content
    cap = content.make_caption(topic)
    if credits:
        cap += "\n\n——\n" + "\n".join(f"🎬 {c}" for c in credits)
    return cap


def _save_meta(topic: dict, credits: list[str]) -> Path:
    META_DIR.mkdir(parents=True, exist_ok=True)
    p = META_DIR / f"{topic['id']}.json"
    p.write_text(json.dumps({
        "title": (topic.get("title_ar") or topic["id"])[:100],
        "caption": _caption_with_credits(topic, credits),
        "tags": [t.strip() for t in topic.get("tags", "").split(",") if t.strip()],
    }, ensure_ascii=False), encoding="utf-8")
    return p


def _media_ok(topic: dict) -> bool:
    """هل الحلقة فيها ميديا حقيقية (لقطة فيديو حية أو صورة حقيقية)؟

    بق حقيقي (2026-09-20): حلقة تقليد اتخزنت واتنشرت وهي كلها خلفيات
    مولّدة — صفر لقطة حية. القاعدة: تقليد/عين لازم لقطة فيديو حية،
    وأي حلقة تانية لازم ميديا حقيقية (فيديو أو صورة) مش خلفيات بس.
    """
    from xtrendaw import state
    try:
        ms = state.media_summary_for(topic.get("id") or "")
    except Exception:
        return True                      # ما نوقفش النشر بسبب خطأ قياس
    if not ms.get("total"):
        return True                      # حلقة قديمة/مسار مش مسجّل
    shots = topic.get("shots") or []
    if shots or topic.get("_replication"):
        return int(ms.get("video") or 0) > 0
    return (int(ms.get("video") or 0) + int(ms.get("images") or 0)) > 0


def _promote_from_vault() -> None:
    """ينزّل أقدم حلقة من المخزون على القناة (بوصف كامل) لو الكوتة مفتوحة.

    لو النشر فشل (كوتة/صلاحية) بنرجّع الحلقة للمخزون تاني — صفر ضياع.
    """
    from xtrendaw import github_store, settings, state
    from xtrendaw.publish import youtube as _yt

    res = github_store.promote_next()
    if not res:
        return
    meta = res.get("meta") or {}
    video = res.get("local_video")
    title = meta.get("title") or meta.get("title_ar") or res["id"]
    caption = meta.get("caption") or ""
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    credits = [c for c in (meta.get("credits") or []) if str(c).strip()]
    if credits:
        caption += "\n\n" + "\n".join(str(c)[:200] for c in credits[:6])
    url, err = _yt.publish(video, title, caption, tags)
    if err or not url:
        print(f"[factory] ⚠ الفرجة فشلت ({err}) — الحلقة رجعت للمخزون", flush=True)
        try:
            github_store.upload_to_vault(video, None, meta)
        except Exception:
            pass
        return
    vid_id = url.split("watch?v=")[-1].split("&")[0] if "watch?v=" in url else ""
    print(f"[factory] 📺 نزلت من المخزون على القناة: {url}", flush=True)
    if vid_id:
        state.push_published({"id": vid_id, "title": title,
                              "kind": meta.get("kind", ""), "ts": time.time()})
        state.push_yt_recent({"id": vid_id, "title": title, "reciter": "",
                              "ts": time.time()})
    state.set_last_kind(meta.get("kind", "know"))


def cycle_once() -> None:
    from xtrendaw import github_store, produce, settings, state
    s = _load_status()
    s["cycles"] = s.get("cycles", 0) + 1
    s["last_cycle_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    now = time.strftime("%H:%M")

    # 1) رادار — يفشل نظيف بلا مفتاح/نت
    try:
        from xtrendaw import radar
        radar.scan()
        _log(s, "radar", {"at": now, "ok": True})
    except Exception as exc:
        _log(s, "radar", {"at": now, "ok": False, "err": type(exc).__name__})

    # 2) عين — تشوف ترندات حقيقية (تدهور آمن) وتغذي الطابور
    try:
        r = subprocess.run([sys.executable, "-m", "xtrendaw.eye", "--auto", "--max", "2"],
                           cwd=ROOT, capture_output=True, text=True, timeout=900)
        tail = (r.stdout or r.stderr or "").strip().splitlines()
        _log(s, "eye", {"at": now, "rc": r.returncode,
                        "note": tail[-1][:120] if tail else ""})
    except Exception as exc:
        _log(s, "eye", {"at": now, "rc": -1, "err": type(exc).__name__})

    # 3) اختيار الحلقة: سحابة = المخ الكامل · محلي = اللي ليه مخزون صوت
    edge = _edge_tts_ok()
    if edge:
        print("[factory] edge-tts متاح — المخ الكامل (عين/ترند/معرفة) شغال", flush=True)
        topic = _brain_topic()
    else:
        print(f"[factory] edge محجوب محليًا — اختيار من اللي ليه مخزون صوت في {POOLS}", flush=True)
        topic = _local_pool_topic()

    if topic is None:
        _log(s, "renders", {"at": now, "ok": False,
                            "note": "مفيش موضوع متاح للرندر (انتظر مخزون صوت جديد أو السحابة)"})
        _save_status(s)
        print(f"[factory] cycle {s['cycles']}: مفيش موضوع متاح — الدورة الجاية بعد {CYCLE}s", flush=True)
        return

    vid = settings.OUT / f"{topic['id']}.mp4"
    meta_p = META_DIR / f"{topic['id']}.json"
    need_render = not vid.exists() or vid.stat().st_size < 1_000_000 or not meta_p.exists()
    if need_render:
        pool = POOLS / topic["id"]
        if not edge and not (pool.is_dir() and list(pool.glob("seg*.mp3"))):
            _log(s, "renders", {"at": now, "ok": False,
                                "note": f"{topic['id']}: مستني مخزون صوت"})
            _save_status(s)
            print(f"[factory] cycle {s['cycles']}: {topic['id']} مؤجلة لحد الصوت", flush=True)
            return
        if not edge:
            _tts_adapter(pool)
        try:
            t0 = time.time()
            out = produce.produce_episode(topic, ROOT / "work" / f"loop_{topic['id']}")
            rep = out.get("report", {})
            credits = list(rep.get("credits") or [])
            _save_meta(topic, credits)
            if rep.get("ok"):
                try:
                    import re as _re
                    m = _re.search(r"Duration: (\d+):(\d+):(\d+)",
                                   subprocess.run([str(out.get("video"))], capture_output=True).stderr or "")
                except Exception:
                    pass
                state.mark_produced(topic, str(out.get("video")), rep.get("info", {}).get("duration", 0))
            _log(s, "renders", {"at": now, "video": str(out.get("video")),
                                "ok": bool(rep.get("ok")), "sec": round(time.time() - t0)})
            # دليل الميديا: فيديو حي/صور/مخزون — يبان في لوج كل دورة
            try:
                _ms = state.media_summary_for(topic["id"])
                if _ms.get("total"):
                    print(f"[factory] 🎬 ميديا {topic['id']}: فيديو حي="
                          f"{_ms['video']} · صور={_ms['images']} · مخزون="
                          f"{_ms['static']}"
                          + (" ⚠️" if _ms["static"] else " ✓"), flush=True)
            except Exception:
                pass
        except Exception as exc:
            _log(s, "renders", {"at": now, "ok": False,
                                "err": f"{type(exc).__name__}: {exc}"[:160]})

    # 4) نشر معتمد — اعتمادات كاملة + وصف كامل بالإسناد (فشل آمن)
    # ⚠️ حارس الكوتة: يوتيوب 10,000 وحدة/يوم ÷ 1,600 للرفعة = 6 رفعات.
    # فوق السقف: الحلقة تتحفظ في المخزون وترفع أول ما الكوتة تفتح —
    # صفر محاولات مهدورة وصفر أخطاء حصة.
    # ⚠️ في وضع "بلا نشر" (معاينة/فحص) بنوقف قبل أي رفع خالص.
    # 📸 ورقة إطارات الحلقة — دليل بصري حقيقي في state/latest_sheet.jpg
    # (كانت بتتولد في run_cycle بس، فالأرتيفاكت بتاع الدورة كان بيطلع ورقة
    #  قديمة — يعني الدليل اللي بنشوفه مش بتاع الفيديو الجديد.)
    if vid.exists():
        try:
            from xtrendaw import sheetshot
            if sheetshot.shoot(vid, topic.get("_kind", "know"),
                               topic.get("title_ar", "")):
                print("[factory] 📸 ورقة الإطارات اتصورت للحلقة دي", flush=True)
        except Exception as exc:
            print(f"[factory] ⚠ ورقة الإطارات: {type(exc).__name__}", flush=True)

    # 📺 فرّج أقدم حلقة من المخزون (لو الكوتة متاحة) — الساعية مش بتتوهش
    # بق حقيقي (2026-09-20): الحلقة اللي اتعملت والكوتة مقفولة كانت بتفضل
    # في المخزون للأبد — مفيش حاجة بتفرّجها. دلوقتي كل دورة تفرّج أقدم حلقة
    # مستنية قبل ما تنتج الجديدة.
    try:
        if not NO_PUBLISH and not state.published_today_pt() >= (settings.DAILY_CAP or 999):
            _promote_from_vault()
    except Exception as exc:
        print(f"[factory] ⚠ الفرجة من المخزون: {type(exc).__name__}: "
              f"{str(exc)[:90]}", flush=True)

    # 📦 خزّن في المخزون (vault) — الفيديو ما يضيعش لو الكوتة مقفولة
    # بق حقيقي (2026-09-20): الدورة أنتجت حلقة التقليد والكوتة كانت 6/6،
    # فالفيديو راح مع الـrunner ومات — يعني شغل ضاع بالكامل.
    _quota_hold = state.published_today_pt() >= (settings.DAILY_CAP or 999)
    if vid.exists() and github_store.available():
        try:
            # دليل الميديا بيتسجل مع الحلقة: لو الحلقة طلعت بصفر لقطة حية
            # (خلفيات مولّدة بس) الفخ يعرف وما ينشّرهاش — والحلقة تتشال.
            try:
                _ms = state.media_summary_for(topic["id"])
            except Exception:
                _ms = {}
            _meta = {"id": topic["id"], "title_ar": topic.get("title_ar", ""),
                     "tags": topic.get("tags", ""), "kind": topic.get("_kind", "know"),
                     "shots": len(topic.get("shots") or []),
                     "live_clips": int(_ms.get("video") or 0),
                     "images_used": int(_ms.get("images") or 0),
                     "static_used": int(_ms.get("static") or 0),
                     "_eye": topic.get("_eye"),
                     "credits": list((rep.get("credits") or []))}
            _urls = github_store.upload_to_vault(vid, out.get("cover"), _meta)
            print(f"[factory] 📦 الحلقة في المخزون: {_urls.get('video', '')[:70]}",
                  flush=True)
        except Exception as exc:
            print(f"[factory] ⚠ تخزين المخزون: {str(exc)[:110]}", flush=True)

    if vid.exists() and not NO_PUBLISH and state.published_today_pt() >= (settings.DAILY_CAP or 999):
        _log(s, "publish_attempts", {"at": now, "topic": topic["id"], "ok": False,
                                     "why": f"daily_cap {state.published_today_pt()}/{settings.DAILY_CAP}"})
        print(f"[factory] ⏸ حارس الكوتة: {state.published_today_pt()}/{settings.DAILY_CAP} "
              "رفعة النهاردة (يوم يوتيوب PT) — الفيديو اتحفظ ومستني الدور", flush=True)
    elif vid.exists() and not NO_PUBLISH and not _media_ok(topic):
        # ⛔ حارس الميديا: حلقة بلا ولا لقطة حية (خلفيات مولّدة) ما تتنشرش —
        # دي بالظبط الشكوى: «فيديو حي مش صور مركبة». بتتخزن في المخزون
        # بحالة live_clips=0 والفخ بيشيلها لوحده.
        _log(s, "publish_attempts", {"at": now, "topic": topic["id"], "ok": False,
                                     "why": "no_live_media"})
        print(f"[factory] ⛔ الحلقة {topic['id']} فيها صفر لقطة حية — "
              "مش هتتنشر (خلفيات مولّدة)", flush=True)
    elif vid.exists() and not NO_PUBLISH:
        try:
            if not meta_p.exists():
                meta_p = _save_meta(topic, [])
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
            from xtrendaw.publish import youtube as _yt
            res, why = _yt.publish(vid, meta["title"], meta["caption"], meta["tags"])
            _log(s, "publish_attempts", {"at": now, "topic": topic["id"],
                                         "ok": bool(res),
                                         "why": why or ("published" if res else "unknown")})
            # سجل الرفعات: أساس حارس الكوتة ورادار البقاء
            if res and "watch?v=" in res:
                state.push_published({
                    "id": res.split("watch?v=")[-1].split("&")[0],
                    "title": meta["title"], "kind": topic.get("_din") or topic.get("_kind", "trend"),
                    "ts": time.time()})
            # التعليم بعد المحاولة — الدوران يتحرك للحلقة اللي بعدها
            if not state.fingerprint_seen(topic):
                from xtrendaw import tts as _tts
                state.mark_produced(topic, str(vid), _tts.probe_duration(vid))
        except Exception as exc:
            _log(s, "publish_attempts", {"at": now, "topic": topic["id"],
                                         "ok": False, "err": type(exc).__name__})

    # 4.5) الدبلجة العالمية — على السحابة: رندر دبلجة بلغة مختلفة كل دورة
    # (محليًا edge مقفول فبتتسجل بنظافة — السحابة بتنفذها فورًا)
    if edge and vid.exists():
        try:
            from xtrendaw import dub as _dub
            lang = _dub.rotate([d.get("lang", "") for d in s.get("dubs", [])])
            dtopic = _dub.dub_topic_for(topic, lang)
            if dtopic:
                d_out = produce.produce_episode(
                    dtopic, ROOT / "work" / f"loop_{dtopic['id']}", narration_lang=lang)
                drep = d_out.get("report", {})
                _log(s, "dubs", {"at": now, "lang": lang, "topic": dtopic["id"],
                                 "ok": bool(drep.get("ok"))})
            else:
                _log(s, "dubs", {"at": now, "lang": lang, "ok": False,
                                 "note": "الترجمة محتاجة LLM (متاحة على السحابة)"})
        except Exception as exc:
            _log(s, "dubs", {"at": now, "ok": False, "err": type(exc).__name__})

    # 5) تخزين دائم — سجلات الدورة في git
    try:
        subprocess.run(["git", "add", "data/factory_status.json", "data/publish_meta",
                        "data/production_log.json"], cwd=ROOT, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", f"factory: cycle {s['cycles']} @ {now} — {topic['id']}"],
                       cwd=ROOT, capture_output=True)
        s["last_commit"] = "saved"
    except Exception:
        pass

    _save_status(s)
    print(f"[factory] cycle {s['cycles']} done @ {now} — {topic['id']}", flush=True)


def main() -> int:
    global ONCE, NO_PUBLISH
    if "--once" in sys.argv:
        ONCE = True
    if "--no-upload" in sys.argv or "--no-publish" in sys.argv:
        NO_PUBLISH = True
    if ONCE:
        print(f"[factory] دورة واحدة (بلا حلقة دائمة)"
              f"{' — رندر بلا نشر' if NO_PUBLISH else ''}", flush=True)
        try:
            cycle_once()
        except Exception:
            print("[factory] الدورة فشلت:", traceback.format_exc()[-400:], flush=True)
            return 1
        return 0
    print(f"[factory] الحلقة الدائمة v3 — دورة كل {CYCLE}s (ساعي) — كل دورة حلقة جديدة", flush=True)
    while True:
        try:
            cycle_once()
        except Exception:
            print("[factory] دورة فشلت:", traceback.format_exc()[-400:], flush=True)
            s = _load_status()
            s["last_error"] = time.strftime("%Y-%m-%d %H:%M:%S")
            _save_status(s)
        time.sleep(CYCLE)


if __name__ == "__main__":
    raise SystemExit(main())
