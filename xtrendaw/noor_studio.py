"""🎬 مكتبة الاستوديو — لقطات حرة من الأسرار والمصادر المفتوحة.

الأطراف (المصانع) تختار الحلو من هنا. القاعدة:
  • Pexels / Pixabay: تجاري بلا إسناد إجباري — المفتاح في سيكرتس جيت هب.
  • NASA: صور وفيديو الكون — NASA أو NASA_API_KEY، ولو فاضي DEMO_KEY.
  • Wikimedia Commons: لكل ملف ترخيصه، والمصنع أصلًا بيسجّل النسبة.
  • Openverse: فلتر commercial — OPENVERSE.
  • Mixkit: ترخيص حر بلا إسناد، ومفيش API عام — مصدر يدوي، مش بنسحب عشوائي.
  • صفر موسيقى · صفر وجوه · صفر سلاح قريب.

maybe_enrich بيضيف مشاهد بس، وميعندّلش نص الآية.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

UA = {"User-Agent": "NoorFactory/1.0 (studio catalog; free licenses)"}

# جمل بحث مجرّبة — الاستوديو يقدر يبدّل بينها
QUERIES = {
    "dawn": "mosque minaret silhouette sunrise",
    "night": "crescent moon desert stars",
    "water": "calm ocean waves aerial",
    "light": "light through arabesque window",
    "green": "green valley after rain mist",
    "cosmos": "earth from space night",
}


def _get(url: str, headers: dict | None = None, timeout: int = 12):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace"))


def probe() -> dict:
    """يجرّب كل طرف ويرجّع اللي رد. النقص مش بيفشل المصنع."""
    out: dict = {"ok": [], "miss": []}

    # ويكيميديا — بلا مفتاح
    try:
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": QUERIES["dawn"], "gsrnamespace": "6", "gsrlimit": "1",
            "prop": "imageinfo", "iiprop": "url|mime|extmetadata",
        })
        data = _get("https://commons.wikimedia.org/w/api.php?" + q)
        pages = (data.get("query") or {}).get("pages") or {}
        page = next(iter(pages.values()), {})
        ii = (page.get("imageinfo") or [{}])[0]
        lic = ((ii.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", "")
        out["ok"].append({"source": "Wikimedia Commons", "license": lic or "per-file",
                          "sample": str(page.get("title") or "")[:80],
                          "note": "النسبة مطلوبة لو الترخيص BY/BY-SA"})
    except Exception as exc:  # noqa: BLE001
        out["miss"].append({"source": "Wikimedia Commons", "err": type(exc).__name__})

    # ناسا — مفتاح أو DEMO
    try:
        key = os.environ.get("NASA_API_KEY") or os.environ.get("NASA") or "DEMO_KEY"
        url = ("https://images-api.nasa.gov/search?q="
               + urllib.parse.quote(QUERIES["cosmos"]) + "&media_type=image")
        data = _get(url, {"X-Api-Key": key} if False else None)
        items = (data.get("collection") or {}).get("items") or []
        title = ""
        if items:
            title = str((items[0].get("data") or [{}])[0].get("title") or "")[:80]
        out["ok"].append({"source": "NASA", "license": "NASA Media Usage",
                          "sample": title, "key": "secret" if key != "DEMO_KEY" else "DEMO_KEY"})
    except Exception as exc:  # noqa: BLE001
        out["miss"].append({"source": "NASA", "err": type(exc).__name__})

    pex = os.environ.get("PEXELS_API_KEY") or os.environ.get("PEXELS")
    if pex:
        try:
            data = _get("https://api.pexels.com/videos/search?query="
                        + urllib.parse.quote(QUERIES["water"]) + "&per_page=1",
                        {"Authorization": pex})
            vid = (data.get("videos") or [{}])[0]
            out["ok"].append({"source": "Pexels", "license": "Pexels — بلا إسناد إجباري",
                              "sample": str(vid.get("url") or "")[:80]})
        except Exception as exc:  # noqa: BLE001
            out["miss"].append({"source": "Pexels", "err": type(exc).__name__})
    else:
        out["miss"].append({"source": "Pexels", "err": "no-key"})

    pix = os.environ.get("PIXABAY_API_KEY")
    if pix:
        try:
            data = _get("https://pixabay.com/api/videos/?key=" + urllib.parse.quote(pix)
                        + "&q=" + urllib.parse.quote("ocean sunrise") + "&per_page=3")
            hit = (data.get("hits") or [{}])[0]
            out["ok"].append({"source": "Pixabay", "license": "Pixabay — بلا إسناد إجباري",
                              "sample": str(hit.get("tags") or "")[:80]})
        except Exception as exc:  # noqa: BLE001
            out["miss"].append({"source": "Pixabay", "err": type(exc).__name__})
    else:
        out["miss"].append({"source": "Pixabay", "err": "no-key"})

    ov = os.environ.get("OPENVERSE_API_KEY") or os.environ.get("OPENVERSE")
    headers = {"Authorization": f"Bearer {ov}"} if ov else None
    try:
        data = _get("https://api.openverse.org/v1/images/?q="
                    + urllib.parse.quote("desert dawn")
                    + "&license_type=commercial&page_size=1", headers, timeout=8)
        rec = (data.get("results") or [{}])[0]
        out["ok"].append({"source": "Openverse", "license": str(rec.get("license") or "commercial-filter"),
                          "sample": str(rec.get("title") or "")[:80]})
    except Exception as exc:  # noqa: BLE001
        out["miss"].append({"source": "Openverse", "err": type(exc).__name__})

    out["mixkit"] = {
        "source": "Mixkit",
        "license": "Mixkit License — تجاري بلا إسناد",
        "note": "مفيش API عام. الاستوديو يستخدمه يدويًا أو من الخزنة، مش سحب عشوائي.",
    }
    brain = "on" if (os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY")
                     or os.environ.get("LLM_API_KEY")) else "off"
    out["brain"] = brain
    return out


def maybe_enrich(item: dict) -> dict:
    """يضيف مشاهد من الجدول، ولو NOOR_STUDIO_LLM=1 يطلب اقتراح ويكمّل مش يستبدل النص."""
    from .noor_grid import SCENES
    kind = str(item.get("kind") or item.get("plan_kind") or "")
    if not item.get("scenes"):
        item["scenes"] = list(SCENES.get(kind) or SCENES.get("spirit") or [])
    if os.environ.get("NOOR_STUDIO_LLM") != "1":
        return item
    try:
        from .noor_ideas import suggest_scenes
        extra = suggest_scenes(str(item.get("theme") or kind or "calm nature"))
    except Exception:
        extra = None
    if extra:
        merged = list(item.get("scenes") or [])
        for s in extra:
            if s not in merged:
                merged.append(s)
        item["scenes"] = merged[:6]
    return item
