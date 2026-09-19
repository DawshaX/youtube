"""طبقة الصور الاحتياطية — لما مفيش فيديو متاح، صورة مرخصة تتحول حركة.

الترتيب (زي البلوبرنت): ويكيميديا كومنز ← أوبنفيرس ← ستيبل هورد
(بولّينيشنز و`render_bg` لسه الملاذ الأخير في `scenes`).

القواعد:
  * ترخيص كل صورة بيتفحص قبل القبول — المسموح: ملك عام/CC0/CC-BY فقط.
  * كل صورة مقبولة بتتحول **فيديو حركة** (زوم/بان 1080×1920@30) —
    المخرج دايمًا فيديو مش صورة (بند الاستوديو).
  * التسجيل في `vault/index.json` إلزامي قبل إتاحة الملف للمونتاج.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import requests

from . import settings
from .footage import MAX_DL, UA, _dl, _has_captions, net_footage_enabled
from .tts import ffmpeg

IMG_DIR = settings.STATE / "imagelib"

# ─────────────────────────────────────────────────────────────
# 1) ويكيميديا كومنز — صور بترخيص مستخرج من الـmetadata
# ─────────────────────────────────────────────────────────────
def _commons_images(query: str) -> list[dict]:
    if not query:
        return []
    try:
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "format": "json",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6, "gsrlimit": 8,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiurlwidth": 1080,
            },
            headers=UA, timeout=25,
        )
        if not r.ok:
            return []
        pages = r.json().get("query", {}).get("pages", {})
        out = []
        for p in pages.values():
            info = (p.get("imageinfo") or [{}])[0]
            out.append({
                "url": info.get("thumburl") or info.get("url", ""),
                "extmeta": info.get("extmetadata", {}),
                "title": p.get("title", ""),
                "_source": "wikimedia-commons",
            })
        return out
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
# 2) أوبنفيرس — بحث مفلتر بالترخيص من المنبع (بلا مفتاح بحدود أقل)
# ─────────────────────────────────────────────────────────────
_OPENVERSE_LIC = {
    "cc0": ("CC0", False),
    "publicdomain": ("Public-Domain", False),
    "by": ("CC-BY-4.0", True),
}


def _openverse_images(query: str) -> list[dict]:
    if not query:
        return []
    headers = dict(UA)
    if settings.OPENVERSE_API_KEY:
        headers["Authorization"] = f"Token {settings.OPENVERSE_API_KEY}"
    try:
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": query, "license": "cc0,by,publicdomain",
                    "page_size": 8},
            headers=headers, timeout=25,
        )
        if not r.ok:
            return []
        out = []
        for h in r.json().get("results", []):
            url = h.get("thumbnail") or h.get("url", "")
            lic = (h.get("license") or "").lower()
            if not url or lic not in _OPENVERSE_LIC:
                continue
            out.append({
                "url": url,
                "license": lic,
                "creator": h.get("creator", ""),
                "foreign": h.get("foreign_landing_url", ""),
                "_source": "openverse",
            })
        return out
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
# 3) ستيبل هورد — توليد جماعي مجاني بلا مفتاح (ملاذ، مش أساس)
# ─────────────────────────────────────────────────────────────
def _stablehorde_image(prompt: str, timeout_s: int = 150) -> bytes | None:
    import time
    try:
        r = requests.post(
            "https://stablehorde.net/api/v2/generate/async",
            json={"prompt": prompt,
                  "params": {"width": 768, "height": 1344, "steps": 20}},
            headers={**UA, "apikey": "0000000000"},  # مجهول = مجاني بطيء
            timeout=25,
        )
        if not r.ok:
            return None
        job = r.json().get("id")
        if not job:
            return None
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            st = requests.get(f"https://stablehorde.net/api/v2/generate/status/{job}",
                              headers=UA, timeout=25).json()
            if st.get("done"):
                gens = st.get("generations", [])
                if gens and gens[0].get("img"):
                    import base64
                    return base64.b64decode(gens[0]["img"])
                return None
            if st.get("faulted"):
                return None
            time.sleep(5)
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# التحويل: صورة → فيديو حركة 1080×1920
# ─────────────────────────────────────────────────────────────
def _image_to_motion(img: Path, seconds: float, out: Path, seed: str) -> bool:
    # زوم بطيء 10% على مدة القطعة — حركة حقيقة بدل الإطار الثابت
    frames = max(1, int(seconds * 30))
    z = f"min(1+0.0012*on,1.12)"
    flip = int(hashlib.sha256(seed.encode()).hexdigest()[:4], 16) % 2
    x_expr = "iw/2-(iw/zoom/2)" if flip else "0+((iw-iw/zoom)*on/%d)" % frames
    vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,"
          f"crop=1080:1920,"
          f"zoompan=z='{z}':x='{x_expr}':y='ih/2-(ih/zoom/2)'"
          f":d={frames}:s=1080x1920:fps=30")
    r = subprocess.run([ffmpeg(), "-y", "-loop", "1", "-i", str(img),
                        "-vf", vf, "-t", f"{seconds:.2f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                        "-pix_fmt", "yuv420p", str(out)],
                       capture_output=True, text=True)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 30_000


def fetch_image_clip(query: str, seconds: float, workdir: Path, seed: str) -> Path | None:
    """صورة مرخصة → مقطع حركة مظبوط، أو None. نفس بوابة النت بتاعة الفيديو."""
    if not net_footage_enabled():
        return None
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"img:{query}".encode()).hexdigest()[:12]
    cached_clip = IMG_DIR / f"{key}.mp4"

    if not cached_clip.exists():
        from . import vault
        from .footage import _commons_license
        raw = workdir / f"img_{key}.bin"
        accepted = None
        # أ) كومنز
        try:
            from . import state as _st
            _seen_media = _st.media_used()
        except Exception:
            _seen_media = {}
        _ep = str(seed).split(":")[0]
        for c in _commons_images(query):
            lic = _commons_license(c.get("extmeta", {}))
            if (lic not in vault.ALLOWED_LICENSES or c["url"] in _seen_media
                    or _st.episode_seen(_ep, c["url"])):
                continue
            if not _dl(c["url"], raw):
                continue
            accepted = (raw, lic, c["title"], c["_source"], c["url"],
                        lic.startswith("CC-BY"))
            break
        # ب) أوبنفيرس
        if accepted is None:
            for c in _openverse_images(query):
                lic, attribution = _OPENVERSE_LIC[c["license"]]
                if lic not in vault.ALLOWED_LICENSES or c["url"] in _seen_media:
                    continue
                if not _dl(c["url"], raw):
                    continue
                title = f"{c['creator'] or 'unknown'} (Openverse)"
                accepted = (raw, lic, title, c["_source"], c["url"], attribution)
                break
        # ج) ستيبل هورد (بلا استعلام شبكة ثابت — ملاذ أخير)
        if accepted is None:
            data = _stablehorde_image(query)
            if data:
                raw.write_bytes(data)
                accepted = (raw, "Internal-Generated", "AI Horde generation",
                            "stable-horde", "", False)
        if accepted is None:
            raw.unlink(missing_ok=True)
            return None
        raw_path, lic, title, source, url, attribution = accepted
        try:
            from . import state as _st
            _st.mark_media_used(url, f"image:{source or 'web'}",
                                str(seed).split(":")[0])
            _st.episode_mark(str(seed).split(":")[0], url)
        except Exception:
            pass
        credit = f"Image: {title} via {source}, {lic}" if attribution else ""
        tmp_clip = workdir / f"motion_{key}.mp4"
        ok = _image_to_motion(raw_path, min(seconds + 1, 12), tmp_clip, seed)
        raw_path.unlink(missing_ok=True)
        if not ok or _has_captions(tmp_clip):
            tmp_clip.unlink(missing_ok=True)
            return None
        tmp_clip.rename(cached_clip)
        vault.register(cached_clip, source=source, license=lic,
                       attribution_required=attribution,
                       credit_line=credit, url=url)

    if not cached_clip.exists():
        return None
    from .footage import _prep, _probe_dur
    out = workdir / f"imgclip_{key}.mp4"
    dur = _probe_dur(cached_clip)
    room = max(1, int(max(0, dur - seconds)))
    off = int(hashlib.sha256(seed.encode()).hexdigest()[:6], 16) % room
    if not _prep(str(cached_clip), seconds, out, offset=off):
        return None
    return out


def fetch_pollinations_clip(query: str, seconds: float, workdir: Path,
                            seed: str) -> Path | None:
    """ملاذ AI المجاني المحدد: Pollinations، مع رفض النص المحروق."""
    if not net_footage_enabled() or not query:
        return None
    from . import vault
    from .scenes import fetch_ai_visual

    workdir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"pollinations:{query}:{seed}".encode()).hexdigest()[:12]
    raw = workdir / f"pollinations_{key}.png"
    numeric_seed = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    prompt = f"cinematic vertical documentary photograph, no words, no text, {query}"
    if not fetch_ai_visual(prompt, raw, numeric_seed):
        return None
    out = workdir / f"pollinations_{key}.mp4"
    if not _image_to_motion(raw, seconds, out, seed) or _has_captions(out):
        out.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)
        return None
    vault.register(out, source="pollinations", license="Internal-Generated",
                   attribution_required=False, url="https://pollinations.ai/")
    raw.unlink(missing_ok=True)
    return out
