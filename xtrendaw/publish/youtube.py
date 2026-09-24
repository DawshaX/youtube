"""يوتيوب — OAuth refresh token + رفع Resumable.

تحذير معروف: لو مشروع Google معملش Compliance Audit، الفيديو بيطلع Private.
فالمحوّل بيرجع الرابط أيًا كان، والحالة بتتبين من يوتيوب نفسه.
"""
from pathlib import Path

import os

import requests
from .. import settings

def _token(acc: dict | None = None):
    """توكن وصول لحساب الرفع (المشروع الأساسي افتراضيًا)."""
    acc = acc or settings.YOUTUBE
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": acc["client_id"],
        "client_secret": acc["client_secret"],
        "refresh_token": acc["refresh_token"],
        "grant_type": "refresh_token"}, timeout=30)
    return r.json().get("access_token") if r.ok else None


def _reason_of(init) -> str:
    try:
        return str(((init.json().get("error") or {}).get("errors") or [{}])[0]
                   .get("reason") or "")
    except Exception:                             # noqa: BLE001
        return ""

def publish(video_path, title, caption, tags, cover=None,
            synthetic: bool = False, category: str = "27",
            publish_at: str | None = None):
    """يرفع الفيديو ويرجّع (رابط، خطأ).

    synthetic: إفصاح إلزامي عن أي وسائط معدّلة/مولّدة (سياسة يوتيوب 2026).
    publish_at: نشر مجدول (UTC ISO) — يخلي الفيديو Private لحد الموعد.
    """
    if not settings.has_youtube():
        return None, "no_credentials"
    # ترتيب الأفضلية: الحسابات المرقّمة (مشاريع جوجل الإضافية) → وإلا المشروع
    # الأساسي مباشرة (توافق كامل مع أي إعداد قديم أو اختبار).
    accounts = list(settings.YOUTUBE_ACCOUNTS) or [settings.YOUTUBE]

    def _meta(status: dict) -> dict:
        return {"snippet": {"title": title[:100], "description": caption[:4900],
                            "tags": tags[:15], "categoryId": category,
                            "defaultLanguage": "ar",
                            "defaultAudioLanguage": "ar"},
                "status": status}

    _status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
               "containsSyntheticMedia": bool(synthetic)}
    if publish_at:
        _status["privacyStatus"] = "private"
        _status["publishAt"] = publish_at

    URL = ("https://www.googleapis.com/upload/youtube/v3/videos"
           "?uploadType=resumable&part=snippet,status")
    init = tok = None
    last = "init_?"
    # 🔁 تناوب مشاريع جوجل: كل مشروع ليه حصته اليومية (6 رفعات). لو مشروع
    # خلصت حصته، بنكمّل بالمشروع اللي بعده تلقائيًا — يعني قناة تنشر كل ساعة
    # لو صاحبها ضاف 4 مشاريع، بلا أي تدخّل يدوي.
    for i, acc in enumerate(accounts):
        tk = _token(acc)
        if not tk:
            last = "refresh_failed"
            continue
        init = requests.post(
            URL, headers={"Authorization": f"Bearer {tk}",
                          "Content-Type": "application/json",
                          "X-Upload-Content-Type": "video/mp4",
                          "X-Upload-Content-Length": str(video_path.stat().st_size)},
            json=_meta(_status), timeout=60)
        if init.status_code == 200:
            tok = tk
            if i:
                print(f"[yt] ↪ رفعت من «{acc.get('label')}» (المشروع الأساسي "
                      f"حصته خلصت)", flush=True)
            break
        reason = _reason_of(init)
        if init.status_code == 400 and publish_at:
            # جوجل رفض الجدولة → نرفع فورًا بدل ما نضيّع الحلقة
            print("SCHEDULE-rejected → نشر فوري", flush=True)
            _fallback = {"privacyStatus": "public",
                         "selfDeclaredMadeForKids": False,
                         "containsSyntheticMedia": bool(synthetic)}
            init = requests.post(
                URL, headers={"Authorization": f"Bearer {tk}",
                              "Content-Type": "application/json",
                              "X-Upload-Content-Type": "video/mp4",
                              "X-Upload-Content-Length":
                                  str(video_path.stat().st_size)},
                json=_meta(_fallback), timeout=60)
            if init.status_code == 200:
                publish_at = None
                tok = tk
                break
        if init.status_code == 403 and "quota" in reason.lower():
            last = "quota_exceeded"
            print(f"[yt] ⚠ حصة «{acc.get('label')}» خلصت — بجرّب مشروع تاني",
                  flush=True)
            continue
        if init.status_code in (401, 403) and "quota" not in reason.lower():
            last = f"auth_{init.status_code}"
            continue
        last = f"init_{init.status_code}"
    if init is None or init.status_code != 200 or not tok:
        return None, last
    up = requests.put(init.headers["Location"],
                      headers={"Content-Length": str(video_path.stat().st_size)},
                      data=open(video_path, "rb"), timeout=900)
    if up.status_code not in (200, 201):
        return None, f"upload_{up.status_code}"
    vid = up.json().get("id", "")
    if cover and Path(cover).exists():
        try:
            th = requests.post(
                "https://www.googleapis.com/upload/youtube/v3/thumbnails/set",
                params={"videoId": vid},
                headers={"Authorization": f"Bearer {tok}",
                         "Content-Type": "image/png"},
                data=Path(cover).read_bytes(), timeout=120)
            print("THUMB:", th.status_code)
        except Exception as e:
            print("THUMB-err:", str(e)[:80])
    return f"https://www.youtube.com/watch?v={vid}", None


# ─────────────── 🗂️ قوائم التشغيل (مصدر مشاهدات إضافي) ───────────────
# ليه: قائمة التشغيل بتخلي يوتيوب يقترح «شاهد التالي» جوه القناة، فبتزوّد
# وقت المشاهدة الجلسي (= أهم رقم عند يوتيوب للمونيتايزيشن والانتشار).
# ⚠️ حساب الحصة (مهم جدًا): كل رفعة = 1600 وحدة، وكوتة المشروع 10,000/يوم.
#    عملية القائمة الواحدة = 50 (بحث) + 50 (إضافة) = 100 وحدة. لو شغّلناها
#    على 24 حلقة يوميًا = 2,400 وحدة = حسابات كوتة كاملة بتتبهدل والنشر
#    الساعي يقف. فالتشغيل الافتراضي: الفيديو الطويل بس (100 وحدة/يوم)،
#    والشورتس بمفتاح env (NOOR_PLAYLIST_SHORTS=1) لما نتأكد إن فيها هامش.
PLAYLISTS = {
    "ayah":   "🕌 آية وسكينة — تلاوات خاشعة",
    "hadith": "📖 أحاديث صحيحة — كنوز السنة",
    "reel":   "🌙 سلاسل وتدبّر — آيات مختارة",
    "long":   "🌌 سور كاملة — تلاوة هادئة قبل النوم",
}


def add_to_playlist(video_id: str, kind: str = "ayah") -> str:
    """يضيف الفيديو لقائمة تشغيل (ويولّدها لو مش موجودة). يرجّع اسم القائمة.

    أي فشل هنا (صلاحية/كوتة/شبكة) **ما يوقفش النشر أبدًا** — يرجّع "" وخلاص.
    """
    if not video_id or not settings.has_youtube():
        return ""
    title = PLAYLISTS.get(kind) or PLAYLISTS["ayah"]
    accounts = list(settings.YOUTUBE_ACCOUNTS) or [settings.YOUTUBE]
    for acc in accounts:
        tk = _token(acc)
        if not tk:
            continue
        h = {"Authorization": f"Bearer {tk}", "Content-Type": "application/json"}
        try:
            pid = ""
            r = requests.get("https://www.googleapis.com/youtube/v3/playlists",
                             headers=h, timeout=60,
                             params={"part": "snippet", "mine": "true",
                                     "maxResults": "50"})
            if r.status_code == 200:
                for it in r.json().get("items", []):
                    if (it.get("snippet", {}).get("title", "").strip() == title):
                        pid = it["id"]
                        break
            elif r.status_code in (401, 403):
                continue
            if not pid:
                c = requests.post(
                    "https://www.googleapis.com/youtube/v3/playlists",
                    headers=h, timeout=60, params={"part": "snippet,status"},
                    json={"snippet": {"title": title, "defaultLanguage": "ar",
                                      "description":
                                      "تلاوات هادئة وتدبّر — بلا موسيقى."},
                          "status": {"privacyStatus": "public"}})
                if c.status_code not in (200, 201):
                    continue
                pid = c.json().get("id", "")
            if not pid:
                continue
            a = requests.post(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                headers=h, timeout=60, params={"part": "snippet"},
                json={"snippet": {"playlistId": pid,
                                  "resourceId": {"kind": "youtube#video",
                                                 "videoId": video_id}}})
            if a.status_code in (200, 201):
                return title
        except Exception:                                     # noqa: BLE001
            continue
    return ""


def autodelete_enabled() -> bool:
    """هل الحذف التلقائي مسموح؟ لازم مطلب صريح بالبيئة — الافتراضي: لا."""
    return os.environ.get("XT_ALLOW_YOUTUBE_AUTODELETE", "").strip() == "1"


def should_autodelete(api_verdict: str | None) -> bool:
    """قرار الحذف: لازم **فحص الـAPI الرسمي** يأكد الحظر + المفتاح مفتوح صراحة.

    الدرس (2026-09-19): الحارس القديم كان بيحذف الفيديو لما oEmbed يرجّع 403
    — و403 بتيجي كتير من rate-limit أو حماية مؤقتة أو شبكة، يعني فيديوهات
    حقيقية اتمسحت من القناة غلط. oEmbed لوحده مش دليل أبدًا.
    """
    return autodelete_enabled() and api_verdict == "blocked"


def check_blocked(video_id: str):
    """oEmbed: 200 = ظاهر، 401/403 = محظور/خاص، 404 = محذوف."""
    try:
        r = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}",
                    "format": "json"}, timeout=20)
        if r.status_code == 404:
            return False, "gone"
        if r.status_code in (401, 403):
            return True, "blocked"
        return False, "ok"
    except Exception:
        return False, "error"


def delete(video_id: str) -> bool:
    """حذف فيديو (محتاج توكن فيه صلاحية youtube.force-ssl).

    الدرس (2026-09-19): أول محاولة رجعت فشل صامت — والسبب إن التوكن مفيهوش
    صلاحية الحذف. فبقينا نرجّع سبب واضح في اللوج بدل «فشل» وخلاص.
    """
    tok = _token()
    if not tok:
        print("✗ الحذف: مفيش توكن")
        return False
    r = requests.delete(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"id": video_id},
        headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    if r.status_code in (200, 204):
        return True
    why = ""
    try:
        err = (r.json().get("error") or {})
        why = (err.get("errors") or [{}])[0].get("reason") or err.get("message", "")
    except Exception:
        pass
    print(f"✗ الحذف فشل ({r.status_code}) {str(why)[:120]}")
    if r.status_code in (401, 403) and "scope" in str(why).lower():
        print("   السبب: التوكن ناقص صلاحية youtube.force-ssl — "
              "محتاج تجديد موافقة OAuth بصلاحية الحذف")
    return False


def check_blocked_api(video_id: str):
    """الفحص الرسمي: regionRestriction.blocked = محظور ولو جزئيًا."""
    tok = _token()
    if not tok:
        return None
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"id": video_id, "part": "contentDetails,status"},
            headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        if not r.ok:
            return None
        items = r.json().get("items", [])
        if not items:
            return "gone"
        rr = (items[0].get("contentDetails") or {}).get("regionRestriction") or {}
        if rr.get("blocked"):
            return "blocked"
        if (items[0].get("status") or {}).get("uploadStatus") == "rejected":
            return "blocked"
        return "ok"
    except Exception:
        return None
