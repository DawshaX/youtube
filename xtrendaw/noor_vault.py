"""خزّان نور — حلقات جاهزة مستنية الحصة اليومية بتاعة يوتيوب.

ليه الخزّان؟ يوتيوب بـAPI بيدي **6 رفعات في اليوم** (10,000 وحدة ÷ 1,600).
فالمصنع بينتج أكتر من كده، والزيادة بتستنى في إصدار GitHub خاص (vault) —
وأول ما الحصة تفتح، بنرفع من الخزّان من غير ما نعيد رندر (أسرع + مفيش فاقد).

التدفق في الدورة الواحدة:
    حصة مفتوحة؟ ── أيوة → فيه حلقة في الخزّان؟ → ارفعها (FIFO) → امسحها
                 │                          └ لا → ارندر حلقة جديدة وانشرها
                 └ لا  → الخزّان أقل من السقف؟ → ارندر + خزّن (بلا محاولة رفع)
                                          └ لا → استريح (مفيش فايدة من زيادة)

كل ده على إصدار خاص في نفس المستودع (`vault`) — مفيش تكلفة ومفيش خدمات.
"""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

BACKLOG_CAP = 12          # أقصى عدد حلقات مستنية في الخزّان


def _api():
    from . import github_store as gs
    tok = gs._token()
    if not tok:
        return None, None
    return tok, gs._vault_id(tok)


def pending() -> list[dict]:
    """حلقات جاهزة في الخزّان (الأقدم الأول) — بلا تحميل أي حاجة."""
    from . import github_store as gs
    tok, rel = _api()
    if not tok:
        return []
    try:
        entries = gs._vault_entries(tok, rel)
    except Exception:
        return []
    out = []
    for e in entries:
        if not str(e.get("name", "")).endswith(".mp4"):
            continue
        kind = str((e.get("meta") or {}).get("kind") or "")
        # ⚠️ حلقات المصنع القديم (بلا بيانات نشر) مالهاش دعوة تتنشر على قناة
        # النور — نرفع بس حلقات المحرك الجديد (kind = noor / noor_long).
        if not kind.startswith("noor"):
            continue
        out.append(e)
    out.sort(key=lambda e: str(e.get("name", "")))
    return out


def dedupe() -> int:
    """يشيل النسخ المكررة من الخزّان (نفس العنوان) — بيسيب أقدم نسخة."""
    from . import github_store as gs
    tok, rel = _api()
    if not tok:
        return 0
    try:
        entries = gs._vault_entries(tok, rel)
    except Exception:
        return 0
    seen: dict[str, dict] = {}
    n = 0
    for e in sorted([x for x in entries if str(x.get("name","")).endswith(".mp4")],
                    key=lambda x: str(x.get("name",""))):
        title = str((e.get("meta") or {}).get("title") or "").strip()
        if not title:
            continue
        if title in seen:
            for a in (e.get("asset"), e.get("cover"), e.get("meta_asset")):
                if a and gs.delete_asset(tok, a["id"]):
                    n += 1
            print(f"[vault] 🗑 نسخة مكررة اتشالت: {title[:50]}", flush=True)
        else:
            seen[title] = e
    return n


def purge_foreign() -> int:
    """يشيل من الخزّان أي حلقة مش من محرك نور (حلقات المصنع القديم المتروكة)."""
    from . import github_store as gs
    tok, rel = _api()
    if not tok:
        return 0
    try:
        entries = gs._vault_entries(tok, rel)
    except Exception:
        return 0
    n = 0
    for e in entries:
        if not str(e.get("name", "")).endswith(".mp4"):
            continue
        kind = str((e.get("meta") or {}).get("kind") or "")
        if kind.startswith("noor"):
            continue
        for a in (e.get("asset"), e.get("cover"), e.get("meta_asset")):
            if a and gs.delete_asset(tok, a["id"]):
                n += 1
        print(f"[vault] 🗑 شيلت حلقة قديمة من الخزّان: {e.get('name')}", flush=True)
    return n


def count() -> int:
    return len(pending())


def can_push(cap: int = BACKLOG_CAP) -> bool:
    """لسه ينفع نخزّن حلقة جديدة؟"""
    n = count()
    if n >= cap:
        print(f"[vault] 🈵 الخزّان فيه {n} حلقة (السقف {cap}) — مش بنخزّن زيادة",
              flush=True)
        return False
    return True


def push(video: Path, cover: Path | None, meta: dict) -> str:
    """يخزّن حلقة جاهزة (مقطع + غلاف + بيانات النشر) في الخزّان.

    🛡️ حماية من التكرار (بق حقيقي 2026-09-21): لو نفس العنوان موجود في الخزّان
    (حصل لأن الحارس المحلي والسحابة اشتغلوا على نفس العنصر في نفس الوقت)،
    ما نخزّنش نسخة تانية — إحنا أصلًا عندنا النسخة دي.
    """
    from . import github_store as gs
    want = str((meta or {}).get("title") or "").strip()
    if want:
        for e in pending():
            have = str((e.get("meta") or {}).get("title") or "").strip()
            if have == want:
                print(f"[vault] ↺ نفس الحلقة موجودة في الخزّان — مش نخزّن نسخة "
                      f"تانية: {want[:50]}", flush=True)
                return (e.get("asset") or {}).get("browser_download_url", "")
    meta = dict(meta or {})
    meta.setdefault("at", time.strftime("%Y-%m-%d %H:%M", time.gmtime()))
    urls = gs.upload_to_vault(video, cover, meta)
    return urls.get("video", "")


def _download(asset: dict, dst: Path) -> None:
    import requests
    r = requests.get(asset["browser_download_url"], timeout=600)
    r.raise_for_status()
    dst.write_bytes(r.content)


def take_oldest(tmp: Path | None = None) -> dict | None:
    """ينزّل أقدم حلقة من الخزّان ويرجّع (المقطع، الغلاف، البيانات، مفاتيح الأصول).

    بياخدها من غير ما يمسحها — المسح بعد نجاح الرفع (drop) عشان ما نضيّعش حلقة.
    """
    from . import github_store as gs
    tok, rel = _api()
    if not tok:
        return None
    items = pending()
    if not items:
        return None
    e = items[0]
    tmp = Path(tmp or tempfile.mkdtemp())
    tmp.mkdir(parents=True, exist_ok=True)
    video = tmp / "spare.mp4"
    try:
        _download(e["asset"], video)
    except Exception as exc:                     # noqa: BLE001
        print(f"[vault] ✗ تحميل الحلقة فشل: {type(exc).__name__}", flush=True)
        return None
    cover = None
    if e.get("cover"):
        cover = tmp / "spare.png"
        try:
            _download(e["cover"], cover)
        except Exception:
            cover = None
    meta = dict(e.get("meta") or {})
    if not meta and e.get("meta_asset"):
        try:
            import requests
            meta = json.loads(requests.get(
                e["meta_asset"]["browser_download_url"], timeout=60).text)
        except Exception:
            meta = {}
    return {"video": video, "cover": cover, "meta": meta, "entry": e}


def drop(entry: dict) -> None:
    """يمسح أصول حلقة من الخزّان (بعد ما اترفعت على يوتيوب)."""
    from . import github_store as gs
    tok, _rel = _api()
    if not tok:
        return
    n = 0
    for a in (entry.get("asset"), entry.get("cover"), entry.get("meta_asset")):
        if a and gs.delete_asset(tok, a["id"]):
            n += 1
    print(f"[vault] 🗑 اتمسحت الحلقة من الخزّان ({n} أصل)", flush=True)
