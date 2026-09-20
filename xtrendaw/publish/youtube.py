"""يوتيوب — OAuth refresh token + رفع Resumable.

تحذير معروف: لو مشروع Google معملش Compliance Audit، الفيديو بيطلع Private.
فالمحوّل بيرجع الرابط أيًا كان، والحالة بتتبين من يوتيوب نفسه.
"""
from pathlib import Path

import os

import requests
from .. import settings

def _token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": settings.YOUTUBE["client_id"],
        "client_secret": settings.YOUTUBE["client_secret"],
        "refresh_token": settings.YOUTUBE["refresh_token"],
        "grant_type": "refresh_token"}, timeout=30)
    return r.json().get("access_token") if r.ok else None

def publish(video_path, title, caption, tags, cover=None,
            synthetic: bool = False, category: str = "27",
            publish_at: str | None = None):
    """يرفع الفيديو ويرجّع (رابط، خطأ).

    synthetic: إفصاح إلزامي عن أي وسائط معدّلة/مولّدة (سياسة يوتيوب 2026).
    publish_at: نشر مجدول (UTC ISO) — يخلي الفيديو Private لحد الموعد.
    """
    if not settings.has_youtube():
        return None, "no_credentials"
    tok = _token()
    if not tok:
        return None, "refresh_failed"
    _status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
               "containsSyntheticMedia": bool(synthetic)}
    if publish_at:
        _status["privacyStatus"] = "private"
        _status["publishAt"] = publish_at
    meta = {"snippet": {"title": title[:100], "description": caption[:4900],
                        "tags": tags[:15], "categoryId": category,
                        "defaultLanguage": "ar", "defaultAudioLanguage": "ar"},
            "status": _status}
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(video_path.stat().st_size)},
        json=meta, timeout=60)
    if init.status_code != 200:
        # فرّق بين «الحصة خلصت» و«رفض تاني» — الكوتة بتتفتح لوحدها،
        # والفرق ده بيخلّي المصنع يهدى بدل ما يحاول ويحاول بلا فايدة.
        try:
            _why = (init.json().get("error", {}).get("errors") or [{}])[0]
            _reason = str(_why.get("reason") or "")
        except Exception:
            _reason = ""
        if init.status_code == 403 and "quota" in _reason.lower():
            return None, "quota_exceeded"
        if init.status_code in (401, 403) and "quota" not in _reason.lower():
            return None, f"auth_{init.status_code}"
        return None, f"init_{init.status_code}"
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
