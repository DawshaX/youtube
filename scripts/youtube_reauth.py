#!/usr/bin/env python3
"""تجديد موافقة يوتيوب بصلاحية الحذف (youtube.force-ssl) — تشغيل محلي بس.

ليه؟ (2026-09-20) المصنع حاول يحذف حلقة قديمة/فاسدة من القناة فجاله
`403 insufficientPermissions` — التوكن الحالي عنده صلاحية الرفع بس. الحذف
محتاج `https://www.googleapis.com/auth/youtube.force-ssl`.

⚠️ ممنوع تشغيله على GitHub Actions: التوكن بيطبع على الشاشة.

الخطوات:
  1) جهّز Client ID و Client Secret (نفس بتوع Actions):
     Google Cloud Console → APIs & Services → Credentials → OAuth client (Desktop)
  2) شغّل:
       YOUTUBE_CLIENT_ID=... YOUTUBE_CLIENT_SECRET=... python scripts/youtube_reauth.py
  3) افتح اللينك اللي هيطلع → وافق → هتحول على صفحة فيها كود
  4) الصق الكود هنا → هيطلع Refresh Token
  5) حدّث سرّ `YOUTUBE_REFRESH_TOKEN` في مستودع GitHub بالتوكن الجديد
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",   # ← الحذف
    "https://www.googleapis.com/auth/youtube.readonly",
]
REDIRECT = "http://localhost"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"


def main() -> int:
    if os.environ.get("GITHUB_ACTIONS"):
        sys.exit("⛔ ممنوع في Actions — التوكن هيتطبع في لوج عام. شغّله على جهازك.")
    cid = (os.environ.get("YOUTUBE_CLIENT_ID") or "").strip()
    csec = (os.environ.get("YOUTUBE_CLIENT_SECRET") or "").strip()
    if not cid or not csec:
        sys.exit("⛔ محتاج YOUTUBE_CLIENT_ID و YOUTUBE_CLIENT_SECRET في البيئة")

    url = AUTH + "?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent",
    })
    print("\n1) افتح اللينك ده في المتصفح ووافق:\n")
    print(url)
    code = input("\n2) الصق الكود اللي ظهرلك (أو الرابط كامل): ").strip()
    if "code=" in code:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(code).query)["code"][0]
    data = urllib.parse.urlencode({
        "code": code, "client_id": cid, "client_secret": csec,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN, data=data), timeout=60) as r:
            tok = json.load(r)
    except Exception as exc:
        sys.exit(f"✗ فشل التبديل: {exc}")
    rt = tok.get("refresh_token")
    if not rt:
        sys.exit("✗ مفيش refresh_token في الرد — جرّب تاني بـ prompt=consent")
    print("\n3) حدّث سرّ YOUTUBE_REFRESH_TOKEN في مستودع GitHub بالتوكن ده:\n")
    print(rt)
    print("\n(التوكن ده بيطبع على شاشتك بس — ما ترفعوش في أي لوج)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
