"""فحص الحالة (الدكتور) — كل المفاتيح والخدمات في تقرير واحد واضح.

  python -m xtrendaw.doctor           # كل الفحوص (شبكية + محلية)
  python -m xtrendaw.doctor --local   # المحلي بس (بلا نت)
  python -m xtrendaw.doctor --json    # مخرَج JSON
  python -m xtrendaw.doctor --md      # ملخص Markdown (للسير والإشعارات)
  python -m xtrendaw.doctor --fail    # exit 1 لو في فشل (افتراضي 0)

الحالات:
  ok   ✅ شغال
  warn ⚠️  غير مضبوط/اختياري (مش فشل — بس معلوم)
  fail ❌ مضبوط بس مش شغال

كل فحص مستقل: فشل واحد ما يوقفش الباقي. بلا نت: الفحوص الشبكية
تقف وبتتحط ⚠️ بلا ادعاء. المخرج: data/health.json (قابل للتدقيق).
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import settings

HEALTH_PATH = settings.ROOT / "data" / "health.json"

_TIMEOUT = 20


def _http_get(url: str, **kw) -> tuple[int, str]:
    import requests
    try:
        r = requests.get(url, timeout=_TIMEOUT, **kw)
        return r.status_code, r.text[:300]
    except Exception as exc:
        return -1, f"{type(exc).__name__}: {exc}"


def _http_post(url: str, **kw) -> tuple[int, str]:
    """(الحالة, النص) — النص كامل 4000 حرف: الردود القصيرة كانت بتتقطع
    (رد توكن جوجل أطول من 300 حرف) فيفشل تحليل JSON ويطلع «فشل تجديد» كاذب
    — وأسوأ: التوكن نفسه كان بيتطبع في اللوج. الاتنين اتصلحوا."""
    import requests
    try:
        r = requests.post(url, timeout=_TIMEOUT, **kw)
        return r.status_code, r.text[:4000]
    except Exception as exc:
        return -1, f"{type(exc).__name__}: {exc}"


def mask_secrets(text: str) -> str:
    """يشيل أي سر من أي نص قبل ما يتكتب في اللوج/التقرير.

    الدرس (2026-09-20): فحص OAuth طبع توكن وصول كامل في لوج Actions لأن
    الرد اتنشر كنص خطأ. قاعدة صارمة: أي رد من خدمة مصادقة بيتفلتر قبل الطبع.
    """
    if not text:
        return ""
    s = str(text)
    # توكنات جوجل
    s = re.sub(r"ya29\.[A-Za-z0-9_\-\.]+", "ya29.●●●", s)
    s = re.sub(r"1//[A-Za-z0-9_\-\.]{10,}", "1//●●●", s)
    # JWT وأي base64 طويل
    s = re.sub(r"eyJ[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}",
               "eyJ●●●", s)
    s = re.sub(r"[A-Za-z0-9_\-]{40,}", "●●●", s)
    # أي قيمة سرية معروفة بالحرف
    try:
        from . import settings as _st
        for name in ("YOUTUBE_API_KEY", "YOUTUBE_CLIENT_SECRET",
                     "YOUTUBE_REFRESH_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY",
                     "PIXABAY_API_KEY", "PEXELS_API_KEY", "NASA_API_KEY"):
            v = (_st.get(name) or "").strip()
            if len(v) >= 8:
                s = s.replace(v, "●●●")
    except Exception:
        pass
    return s


# ─────────────────────────────────────────────────────────────
# الفحوص الشبكية (كل مفتاح: exists? and works?)
# ─────────────────────────────────────────────────────────────

def check_youtube_api_key() -> dict:
    key = settings.get("YOUTUBE_API_KEY")
    if not key:
        return {"name": "YOUTUBE_API_KEY (الرادار)", "status": "warn",
                "detail": "غير مضبوط — الرادار مش هيشتغل"}
    code, body = _http_get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"part": "snippet", "id": "2Vv-BfVoq4g", "key": key})
    if code == 200 and '"items"' in body:
        return {"name": "YOUTUBE_API_KEY (الرادار)", "status": "ok",
                "detail": "شغال — استجابة حقيقية من يوتيوب"}
    return {"name": "YOUTUBE_API_KEY (الرادار)", "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def check_groq() -> dict:
    key = settings.get("GROQ_API_KEY")
    if not key:
        return {"name": "GROQ_API_KEY (مخ الذكاء 1)", "status": "warn",
                "detail": "غير مضبوط"}
    code, body = _http_get("https://api.groq.com/openai/v1/models",
                           headers={"Authorization": f"Bearer {key}"})
    if code == 200:
        return {"name": "GROQ_API_KEY (مخ الذكاء 1)", "status": "ok",
                "detail": "شغال — قائمة الموديلات اتجابت"}
    return {"name": "GROQ_API_KEY (مخ الذكاء 1)", "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def check_gemini() -> dict:
    key = settings.get("GEMINI_API_KEY")
    if not key:
        return {"name": "GEMINI_API_KEY (مخ الذكاء 2)", "status": "warn",
                "detail": "غير مضبوط"}
    code, body = _http_get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": key})
    if code == 200:
        return {"name": "GEMINI_API_KEY (مخ الذكاء 2)", "status": "ok",
                "detail": "شغال — قائمة الموديلات اتجابت"}
    return {"name": "GEMINI_API_KEY (مخ الذكاء 2)", "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def check_custom_llm() -> dict:
    base, key, model = settings.LLM["base"], settings.LLM["key"], settings.LLM["model"]
    # لو ده نفسه Groq اتفحص فوق — نبت
    if not base or (key and base.rstrip("/").endswith("api.groq.com/openai/v1")
                    and key == settings.get("GROQ_API_KEY")):
        return {"name": "LLM_API_* (مزوّد مخصص)", "status": "warn",
                "detail": "غير مضبوط منفصلًا — بيستخدم Groq بدل مكانه"}
    if not key:
        return {"name": "LLM_API_* (مزوّد مخصص)", "status": "warn",
                "detail": "غير مضبوط"}
    code, body = _http_get(f"{base.rstrip('/')}/models",
                           headers={"Authorization": f"Bearer {key}"})
    if code == 200:
        return {"name": f"LLM مخصص ({model})", "status": "ok", "detail": "شغال"}
    return {"name": f"LLM مخصص ({model})", "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def check_youtube_oauth() -> dict:
    """فحص **كل** مشاريع الرفع، مش المشروع الأساسي بس.

    ⚠️ بق حقيقي (2026-09-25): الفحص القديم كان بيعتبر المشروع الأساسي مقياسًا
    للحالة. المشروع الأساسي كان توكنه ميّت، والمشروع الثاني (قناة XTreNDAW)
    **حيّ وشغال والنشر ماشي بيه** — فالتقرير كان بيقول «النشر واقف» وهو شغال.
    الصح: شغال = **مشروع واحد على الأقل** بيجدد وبيوصل قناة.
    """
    accounts = list(settings.YOUTUBE_ACCOUNTS)
    if not accounts:
        cid = settings.get("YOUTUBE_CLIENT_ID")
        sec = settings.get("YOUTUBE_CLIENT_SECRET")
        rtk = settings.get("YOUTUBE_REFRESH_TOKEN")
        if not (cid and sec and rtk):
            missing = [n for n, v in (("CLIENT_ID", cid), ("CLIENT_SECRET", sec),
                                      ("REFRESH_TOKEN", rtk)) if not v]
            return {"name": "YouTube OAuth (النشر)", "status": "warn",
                    "detail": "غير مكتمل — ناقص: " + ", ".join(missing)}
        accounts = [{"client_id": cid, "client_secret": sec,
                     "refresh_token": rtk, "label": "المشروع الأساسي"}]

    alive, dead = [], []
    for acc in accounts:
        label = str(acc.get("label") or "مشروع")
        code, body = _http_post(
            "https://oauth2.googleapis.com/token",
            data={"client_id": acc.get("client_id"),
                  "client_secret": acc.get("client_secret"),
                  "refresh_token": acc.get("refresh_token"),
                  "grant_type": "refresh_token"})
        try:
            j = json.loads(body)
        except Exception:
            j = {}
        at = j.get("access_token")
        if code == 200 and at:
            # نعرف القناة اللي التوكن ده بيوصلها (من غير أي سر في اللوج)
            ch = ""
            c2, b2 = _http_get(
                "https://www.googleapis.com/youtube/v3/channels"
                "?part=snippet&mine=true",
                headers={"Authorization": f"Bearer {at}"})
            if c2 == 200:
                try:
                    it = (json.loads(b2).get("items") or [{}])[0]
                    ch = it.get("snippet", {}).get("title", "")
                except Exception:
                    ch = ""
            alive.append(f"{label} → {ch or 'قناة غير معروفة'}")
        else:
            err = (j.get("error_description") or j.get("error")
                   or body[:120] or f"HTTP {code}")
            dead.append(f"{label}: {err}")

    if alive:
        detail = "شغال — " + " · ".join(alive)
        if dead:
            detail += f" | ⚠ احتياطي ميّت ({len(dead)}): " + " · ".join(dead)
        return {"name": "YouTube OAuth (النشر)", "status": "ok", "detail": detail}
    return {"name": "YouTube OAuth (النشر)", "status": "fail",
            "detail": "كل توكنات الرفع مرفوضة: " + " · ".join(dead)}


def _simple_key_check(env_name: str, label: str, url: str,
                      headers: dict | None = None,
                      params: dict | None = None) -> dict:
    key = settings.get(env_name)
    if not key:
        return {"name": label, "status": "warn", "detail": "غير مضبوط (اختياري)"}
    code, body = _http_get(url, headers=headers or {}, params=params or {})
    if code == 200:
        return {"name": label, "status": "ok", "detail": "شغال — استجابة 200"}
    return {"name": label, "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def check_pixabay() -> dict:
    return _simple_key_check(
        "PIXABAY_API_KEY", "PIXABAY_API_KEY (لقطات فيديو)",
        "https://pixabay.com/api/videos/",
        params={"key": settings.get("PIXABAY_API_KEY"), "q": "cat", "per_page": "3"})


def check_pexels() -> dict:
    key = settings.PEXELS_API_KEY          # بيدوّر على PEXELS_API_KEY أو PEXELS
    if not key:
        return {"name": "PEXELS (لقطات احتياطية)", "status": "warn",
                "detail": "غير مضبوط — لقطات بكسلز بتزيد تنوّع الفيديو (اختياري)"}
    return _simple_key_check(
        "PEXELS_API_KEY", "PEXELS (لقطات احتياطية)",
        "https://api.pexels.com/videos/1",
        headers={"Authorization": key})


def check_nasa() -> dict:
    key = settings.NASA_API_KEY or "DEMO_KEY"
    code, body = _http_get("https://api.nasa.gov/planetary/apod",
                           params={"api_key": key})
    if code == 200:
        st = "ok" if settings.NASA_API_KEY else "warn"
        return {"name": "NASA_API_KEY (فضاء)", "status": st,
                "detail": "شغال" + ("" if settings.get("NASA_API_KEY")
                                   else " (بمفتاح تجريبي — اختياري)")}
    return {"name": "NASA_API_KEY (فضاء)", "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def check_restcountries() -> dict:
    key = settings.get("RESTCOUNTRIES_API_KEY") or settings.get("RESTCOUNTRIES")
    h = {"Authorization": key} if key else {}
    code, body = _http_get("https://restcountries.com/v3.1/alpha/EG", headers=h)
    if code == 200:
        return {"name": "RESTCOUNTRIES (مكتبة العالم)", "status": "ok",
                "detail": "شغال — بيانات مصر الحقيقية اتجابت" +
                          (" (مفتاح مفعّل)" if key else " (بلا مفتاح)")}
    return {"name": "RESTCOUNTRIES (مكتبة العالم)", "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def check_openverse() -> dict:
    h = {}
    key = settings.get("OPENVERSE_API_KEY")
    if key:
        h["Authorization"] = f"Token {key}"
    code, body = _http_get("https://api.openverse.org/v1/images/",
                           params={"page_size": "1"}, headers=h)
    if code == 200:
        return {"name": "OPENVERSE (صور/ميديا)", "status": "ok",
                "detail": "شغال (المفتاح اختياري)" if not key else "شغال"}
    return {"name": "OPENVERSE (صور/ميديا)", "status": "fail",
            "detail": f"HTTP {code} — {body[:160]}"}


def _alias_note() -> str:
    """ملاحظة الأسماء البديلة: نفس المفتاح بأسماء مختلفة في الأسرار."""
    have = [n for n in ("PEXELS", "NASA", "OPENVERSE", "RESTCOUNTRIES")
            if settings.get(n)]
    return (" · الأسماء البديلة المضبوطة: " + ", ".join(have)) if have else ""


def check_freesound() -> dict:
    return _simple_key_check(
        "FREESOUND_API_KEY", "FREESOUND_API_KEY (مؤثرات CC)",
        "https://freesound.org/apiv2/search/",
        params={"token": settings.get("FREESOUND_API_KEY"),
                "q": "a", "fields": "id", "pageSize": "1"})


def check_gnews() -> dict:
    return _simple_key_check(
        "GNEWS_API_KEY", "GNEWS_API_KEY (أخبار)",
        "https://gnews.io/api/v4/top-headlines",
        params={"token": settings.get("GNEWS_API_KEY"), "max": "1",
                "category": "technology", "lang": "en"})


def check_currents() -> dict:
    return _simple_key_check(
        "CURRENTS_API_KEY", "CURRENTS_API_KEY (أخبار لحظية)",
        "https://api.currentsapi.services/v1/latest-news",
        params={"apiKey": settings.get("CURRENTS_API_KEY")})


def check_youtube_cookies() -> dict:
    """الكوكيز مش بتتجدد أوتوماتيك (تصميم أمان من جوجل) — بنكشف موتها مبكرًا.

    بنجرّب **نفس** مسار العين الفعلي: قراءة الكوكيز بنفس التحويل +
    بيانات الفيديو العامة + جلسة المشغل (مشاهد/كلام) — بلا أي تنزيل.
    بق حقيقي (2026-09-20): الفحص كان بيختبر قدرة تنزيل الفيديو، وهي ميتة
    من خوادم Actions أصلاً («The page needs to be reloaded») — فكان بيفشّل
    الفحص كل ساعة على حاجة المصنع مش بيستخدمها.
    """
    b64 = settings.get("YOUTUBE_COOKIES_B64")
    if not b64:
        return {"name": "YOUTUBE_COOKIES_B64 (كوكيز العين)", "status": "fail",
                "detail": "غير مضبوط — العين مش هتشوف أي فيديو من خوادم Actions"}
    path = None
    try:
        from . import eye as _eye
        _hdr, path = _eye._load_cookies()
        if path is None:
            return {"name": "YOUTUBE_COOKIES_B64 (كوكيز العين)",
                    "status": "fail",
                    "detail": "المحتوى مش صالح — لازم Netscape أو JSON "
                              "مصدَّر من المتصفح (Cookie-Editor)"}
        n_pairs = (_hdr.count(";") + 1) if _hdr else 0
        # اختبار حقيقي لمسار العين (بلا تنزيل): بيانات + جلسة المشغل
        info = _eye._public_metadata("2Vv-BfVoq4g") or {}
        player = _eye._player_response("2Vv-BfVoq4g") or {}
        sb = bool(player.get("storyboards") or
                  (player.get("captions") or {}).get("playerCaptionsTracklistRenderer"))
        if info.get("title") or player.get("playabilityStatus"):
            return {"name": "YOUTUBE_COOKIES_B64 (كوكيز العين)", "status": "ok",
                    "detail": f"الجلسة شغالة ({n_pairs} زوج كوكي) — مسار العين "
                              f"(بيانات {'+ مشاهد/كلام' if sb else 'بس'}) بلا تنزيل"}
        return {"name": "YOUTUBE_COOKIES_B64 (كوكيز العين)", "status": "warn",
                "detail": f"الكوكيز اتقرت ({n_pairs} زوج) بس جلسة المشغل ما "
                          "رجعتش بيانات — العين هتمشي ببيانات الـoEmbed"}
    except Exception as exc:
        return {"name": "YOUTUBE_COOKIES_B64 (كوكيز العين)", "status": "fail",
                "detail": mask_secrets(
                    "الكوكيز ماتت/مرفوضة — أعد تصديرها (دقيقتين): "
                    f"{type(exc).__name__}: {exc}")}
    finally:
        # تنظيف مضمون للملف المؤقت (حتى لو الاختبار فشل في النص)
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass


def check_edge_tts() -> dict:
    """edge-tts: اختبار وصول حقيقي بخيط صغير (الخدمة غير رسمية)."""
    import asyncio
    import edge_tts

    async def _probe():
        c = edge_tts.Communicate("اختبار", "ar-SA-HamedNeural")
        async for _ in c.stream():
            return True
        return False

    try:
        ok = asyncio.run(asyncio.wait_for(_probe(), timeout=25))
        return {"name": "edge-tts (صوت حقيقي)", "status": "ok" if ok else "fail",
                "detail": "صوت حقيقي اتولّد (اختبار قصير)" if ok
                else "فشل توليد الصوت"}
    except Exception as exc:
        return {"name": "edge-tts (صوت حقيقي)", "status": "fail",
                "detail": f"{type(exc).__name__}: {exc} — لو من أوفلاين: طبيعي محليًا"}


# ─────────────────────────────────────────────────────────────
# الفحوص المحلية
# ─────────────────────────────────────────────────────────────

def check_ffmpeg() -> dict:
    f = shutil.which("ffmpeg")
    if not f:
        try:
            import imageio_ffmpeg
            f = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            f = None
    if f:
        return {"name": "ffmpeg (المونتاج)", "status": "ok", "detail": f}
    return {"name": "ffmpeg (المونتاج)", "status": "fail",
            "detail": "ملوش — المونتاج مش هيشتغل"}


def check_packages() -> dict:
    needed = ["requests", "PIL", "numpy", "edge_tts"]
    optional = ["yt_dlp", "imageio_ffmpeg"]
    missing = [p for p in needed if importlib.util.find_spec(p) is None]
    miss_opt = [p for p in optional if importlib.util.find_spec(p) is None]
    detail = "كل الحزم الأساسية متاحة"
    if miss_opt:
        detail += f" · اختياري ناقص: {', '.join(miss_opt)}"
    if missing:
        return {"name": "حزم بايثون", "status": "fail",
                "detail": "ناقصة: " + ", ".join(missing)}
    return {"name": "حزم بايثون", "status": "ok", "detail": detail}


def check_voice_library() -> dict:
    from . import voice
    v = voice.load_ar_voices()
    f = settings.ROOT / "state" / "ar_voices.txt"
    if not v:
        return {"name": "مكتبة الأصوات", "status": "fail", "detail": "فارغة"}
    return {"name": "مكتبة الأصوات", "status": "ok",
            "detail": f"{len(v)} صوت عربي" + (" (ملف حقيقي)" if f.exists()
                                             else " (قائمة الاحتياط)")}


def check_data_integrity() -> dict:
    problems = []
    for rel in ("data/production_log.json", "data/eye_topics.json",
                "vault/index.json"):
        p = settings.ROOT / rel
        if p.exists():
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                problems.append(rel)
    if problems:
        return {"name": "سلامة ملفات البيانات", "status": "fail",
                "detail": "JSON فاسد في: " + ", ".join(problems)}
    return {"name": "سلامة ملفات البيانات", "status": "ok",
            "detail": "كل الملفات القابلة للفحص سليمة"}


NETWORK_CHECKS = [
    check_youtube_api_key, check_youtube_cookies, check_groq, check_gemini,
    check_custom_llm,
    check_youtube_oauth, check_pixabay, check_pexels, check_nasa,
    check_openverse, check_restcountries, check_freesound, check_gnews, check_currents,
    check_edge_tts,
]
LOCAL_CHECKS = [
    check_ffmpeg, check_packages, check_voice_library, check_data_integrity,
]


def _sanitize(checks: list[dict]) -> list[dict]:
    """أي تفصيل بيتطبع — يعدّي على فلتر الأسرار. حماية عامة مش حالة بحالة."""
    out = []
    for c in checks:
        c = dict(c)
        if c.get("detail"):
            c["detail"] = mask_secrets(str(c["detail"]))
        out.append(c)
    return out


def run(local_only: bool = False) -> dict:
    checks = [c() for c in LOCAL_CHECKS]
    if not local_only:
        checks += [c() for c in NETWORK_CHECKS]
    else:
        # نسمّي الفحوص المتخطاة بأسماء خدماتها مش بأسماء دوالها
        skip_names = {
            "check_youtube_api_key": "YOUTUBE_API_KEY (الرادار)",
            "check_youtube_cookies": "YOUTUBE_COOKIES_B64 (كوكيز العين)",
            "check_groq": "GROQ_API_KEY (مخ الذكاء 1)",
            "check_gemini": "GEMINI_API_KEY (مخ الذكاء 2)",
            "check_custom_llm": "LLM_API_* (مزوّد مخصص)",
            "check_youtube_oauth": "YouTube OAuth (النشر)",
            "check_pixabay": "PIXABAY_API_KEY (لقطات فيديو)",
            "check_pexels": "PEXELS_API_KEY (لقطات احتياطية)",
            "check_nasa": "NASA_API_KEY (فضاء)",
            "check_openverse": "OPENVERSE (صور/ميديا)",
            "check_restcountries": "RESTCOUNTRIES (مكتبة العالم)",
            "check_freesound": "FREESOUND_API_KEY (مؤثرات CC)",
            "check_gnews": "GNEWS_API_KEY (أخبار)",
            "check_currents": "CURRENTS_API_KEY (أخبار لحظية)",
            "check_edge_tts": "edge-tts (صوت حقيقي)",
        }
        checks += [{"name": skip_names.get(c.__name__, c.__name__),
                    "status": "warn", "detail": "تم تخطيه (--local)"}
                   for c in NETWORK_CHECKS]
    checks = _sanitize(checks)
    fails = [c for c in checks if c["status"] == "fail"]
    report = {
        "checkedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "runner": "local" if local_only else "actions-or-local",
        "all_ok": not fails,
        "fails": len(fails),
        "warns": sum(1 for c in checks if c["status"] == "warn"),
        "checks": checks,
    }
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    return report


_ICONS = {"ok": "✅", "warn": "⚠️", "fail": "❌"}


def summary_md(report: dict) -> str:
    L = [
        f"## فحص الحالة — {report['checkedAt']}",
        "",
        f"**النتيجة: {'كل حاجة تمام ✅' if report['all_ok'] else 'في مشاكل ❌ (' + str(report['fails']) + ')'}** "
        f"· تحذيرات: {report['warns']}",
        "",
        "| الخدمة | الحالة | تفاصيل |",
        "|---|---|---|",
    ]
    for c in report["checks"]:
        L.append(f"| {c['name']} | {_ICONS[c['status']]} {c['status']} | {c['detail']} |")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="فحص حالة المفاتيح والخدمات")
    ap.add_argument("--local", action="store_true", help="بلا فحوص شبكية")
    ap.add_argument("--json", action="store_true", help="مخرَج JSON كامل")
    ap.add_argument("--md", action="store_true", help="ملخص Markdown")
    ap.add_argument("--fail", action="store_true", help="exit 1 لو في فشل")
    args = ap.parse_args()

    report = run(local_only=args.local)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    elif args.md:
        print(summary_md(report))
    else:
        print(f"🩺 فحص الحالة — {report['checkedAt']}")
        for c in report["checks"]:
            print(f"  {_ICONS[c['status']]} {c['name']}: {c['detail']}")
        print(f"\nالنتيجة: {'كل حاجة تمام ✅' if report['all_ok'] else 'في فشل ❌ ' + str(report['fails'])} "
              f"| تحذيرات: {report['warns']} | التقرير: data/health.json")

    if args.fail and not report["all_ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
