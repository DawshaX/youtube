"""مولّد مشاهد B-roll داخلية — لقطات حركة مملوكة 100% وبلا حدود.

## ليه الملف ده موجود (تشخيص حقيقي 2026-10-12)

المصنع كان بيوقف عن النشر **من غير ما حد يفهم ليه**. القياس أثبت السبب:

    [footage] ✗ مفيش لقطة لـ«sunlit floor» — هنكمل بمسار آخر
    [studio] المشاهد ناقصة (0 لقطة) — مش هننشر لوحة

الرندر محتاج **لقطتين فريدتين على الأقل** لكل حلقة. المخزن المحلي
(`assets/footage/`) كان **فاضي**، والمصادر الشبكية بتدّي 1–3 مرشحين
لللاستعلام الواحد وبعدين بتخلص (ذاكرة «اللقطة المستخدمة قبل كده» بتمنع
تكرارها). يعني الإنتاج مقيّد بـ «عدد اللقطات المتاحة في الدنيا» — وده سقف
حقيقي على مصنع بينشر طول العمر.

**الحل:** كل مشهد هنا **بيتولّد بالكود** (numpy + ffmpeg) → عدد لا نهائي،
صفر حقوق، صفر اعتماد على الشبكة، وترخيصه `Internal-Generated`.
كل مشهد **حلقة مثالية**: الإطار عند `t + L` = الإطار عند `t` — فينفع
يتكرر بلا قطع ظاهر.

## الاستخدام

    python3 -m xtrendaw.noor_next.scenes build          # يبني الخزنة كلها
    python3 -m xtrendaw.noor_next.scenes build --scene window_light
    python3 -m xtrendaw.noor_next.scenes list
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from xtrendaw import settings

OUT_DIR = settings.ASSETS / "footage"
W, H, FPS = 720, 1280, 30          # نولّد بجودة وسطى وffmpeg بيرفعها لـ1080×1920
LENGTH_S = 8.0                      # طول الحلقة — مثالي للتكرار
FF = "ffmpeg"


# ───────────────────────── أدوات الرسم ─────────────────────────

def _smooth_noise(h: int, w: int, res: int, seed: int, octaves: int = 3) -> np.ndarray:
    """ضجيج ناعم متعدد الطبقات — أساس كل المشاهد العضوية."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        rh = max(2, h // max(2, res * (2 ** o)))
        rw = max(2, w // max(2, res * (2 ** o)))
        g = (rng.random((rh, rw)) * 255).astype(np.uint8)
        up = Image.fromarray(g).resize((w, h), Image.BICUBIC)
        out += np.asarray(up, np.float32) / 255.0 * amp
        total += amp
        amp *= 0.5
    return out / max(total, 1e-6)


def _vignette(h: int, w: int, strength: float = 0.45) -> np.ndarray:
    y = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    x = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    r = np.sqrt(x * x * 0.85 + y * y)
    return np.clip(1.0 - strength * np.clip(r - 0.25, 0, None) ** 1.6, 0, 1)[..., None]


def _mix(a: np.ndarray, b: np.ndarray, t: np.ndarray | float) -> np.ndarray:
    return a * (1 - t) + b * t


def _hex(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def _vertical(top: str, bottom: str, h: int, w: int, ease: float = 1.0) -> np.ndarray:
    f = np.linspace(0, 1, h, dtype=np.float32)[:, None] ** ease
    top, bottom = _hex(top), _hex(bottom)
    band = _mix(top[None, None, :], bottom[None, None, :], f[..., None])
    return np.repeat(band, w, axis=1)


def _bokeh(h: int, w: int, count: int, seed: int, radius: tuple[int, int],
           color: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """دوائر ضوء ناعمة — للإضاءة والخلفيات الليلية."""
    rng = np.random.default_rng(seed)
    layer = np.zeros((h, w), np.float32)
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    for _ in range(count):
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        rad = rng.uniform(*radius)
        d = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        layer += np.clip(1 - d / rad, 0, 1) ** 2 * rng.uniform(0.4, 1.0)
    layer = np.clip(layer, 0, 1)[..., None] * alpha
    # مقياس 0–255 زي باقي الصورة (بَغ 2026-10-12: كان ×0–1 فبيختفي)
    return np.repeat(color[None, None, :], 1, axis=0)[..., :] * layer * 255.0


def _blur_mask(m: np.ndarray, radius: float) -> np.ndarray:
    """تنعيم قناع 0..1 — عشان الحواف تبان طبيعية (بلا قطع حاد)."""
    if radius <= 0:
        return m
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), mode="L")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255.0


def _calibrate(frame_fn, lo: float = 42.0, hi: float = 128.0, gamma: float = 0.94):
    """معايرة تلقائية لكل مشهد (درس 2026-10-12).

    القياس الحقيقي: كذا مشهد كان متوسط إضاءته 9–26/255 — يعني أسود فاضي،
    والناتج النهائي طلع مسطح مش جاذب. المعايرة دي بترفع المشهد الداكن
    لمدى مقروء، وبتهدّي الباهت المسطح، وبتضيف حبيبة فيلم (grain) بتخلي
    الإطار يحس إنه مادة حقيقية مش تدرّج فاضي.
    """
    probe = np.clip(frame_fn(0.0), 0, 255)
    mean = float(probe.mean()) or 1.0
    gain = 1.0
    if mean < lo:
        gain = min(lo / mean, 4.5)
    elif mean > hi:
        gain = max(hi / mean, 0.50)
    xs = np.clip(np.arange(256, dtype=np.float32) / 255.0, 0, 1)
    lut = np.clip(255.0 * np.power(xs, gamma) * gain, 0, 255).astype(np.float32)
    grain = np.random.default_rng(1717).normal(0.0, 2.0, (H, W, 1)).astype(np.float32)

    def wrapped(t: float) -> np.ndarray:
        f = np.clip(frame_fn(t), 0, 255)
        f = lut[np.clip(f, 0, 255).astype(np.uint8)]
        return np.clip(f + grain * (0.35 + f / 255.0), 0, 255)

    return wrapped


# ───────────────────────── المشاهد ─────────────────────────
# كل مشهد: (اسم, وسوم للبحث, دالة تبني base (H,W,3) + دالة الإطار)

def _scene_window_light(seed: int):
    base = _vertical("#2A2118", "#0D0A07", H, W, 1.4)
    rng = np.random.default_rng(seed)
    pane = np.zeros((H, W, 3), np.float32)
    gx0, gx1 = int(W * 0.10), int(W * 0.90)
    gy0, gy1 = int(H * 0.08), int(H * 0.62)
    warm = _mix(_hex("#FFE7B8"), _hex("#FFC978"), np.linspace(0, 1, gy1 - gy0, dtype=np.float32)[:, None, None])
    pane[gy0:gy1, gx0:gx1] = np.repeat(warm, gx1 - gx0, axis=1)
    mask = np.zeros((H, W), np.float32)
    mask[gy0:gy1, gx0:gx1] = 1.0
    mask = _blur_mask(mask, max(6.0, H * 0.035))      # حافة ناعمة = عمق حقيقي
    dust = _smooth_noise(H, W, 6, seed + 11, 2)[..., None]
    pane *= (0.82 + 0.30 * dust)
    base = _mix(base, pane, 0.90 * mask[..., None])
    motes = rng.random((H, W)).astype(np.float32)

    def frame(t: float) -> np.ndarray:
        shift = int((t / LENGTH_S) * W * 0.12) % W
        glow = np.roll(pane, shift, axis=1) * 0.35
        m = np.roll(motes, int(t * 22) % H, axis=0) > 0.9993
        img = base + glow
        img[m] += 120
        img *= _vignette(H, W, 0.5)
        return img

    return frame


def _scene_sunlit_floor(seed: int):
    base = _vertical("#E8C88F", "#8A6A3E", H, W, 0.7)
    grain = _smooth_noise(H, W, 3, seed + 3, 2)[..., None]
    base *= (0.88 + 0.22 * grain)
    patch = _bokeh(H, W, 3, seed + 9, (int(H * 0.30), int(H * 0.55)), np.array([1.0, 0.93, 0.72]))

    def frame(t: float) -> np.ndarray:
        drift = math.sin(t / LENGTH_S * math.tau) * 0.06
        img = base * (1.0 + 0.10 * ((t / LENGTH_S) * 1.0 + drift))
        p = np.roll(patch, int(drift * W), axis=1)
        img = _mix(img, np.array([255, 236, 190], np.float32), np.clip(p, 0, 0.55)[..., None] if p.ndim == 2 else p)
        img *= _vignette(H, W, 0.38)
        return img

    return frame


def _scene_kitchen_clean(seed: int):
    base = _vertical("#DCE6E9", "#7E8C93", H, W, 1.1)
    steel = _smooth_noise(H, W, 5, seed + 5, 2)[..., None]
    base *= (0.93 + 0.14 * steel)
    counter = _hex("#F3F5F4")
    base[int(H * 0.55):] = _mix(base[int(H * 0.55):], counter, 0.35)

    def frame(t: float) -> np.ndarray:
        steam = _smooth_noise(H, W, 8, seed + int(t * 30) % 97, 2)[..., None]
        img = base * (0.97 + 0.07 * steam)
        img *= _vignette(H, W, 0.30)
        return img

    return frame


def _scene_water_ripple(seed: int):
    base = _vertical("#0E2333", "#061019", H, W, 1.0)
    n = _smooth_noise(H, W, 4, seed + 7, 3)

    def frame(t: float) -> np.ndarray:
        phase = t / LENGTH_S * math.tau
        w1 = np.sin(n * 12.0 + phase * 2) * 0.5 + 0.5
        w2 = np.sin(np.roll(n, 40, axis=1) * 9.0 - phase * 3) * 0.5 + 0.5
        spark = np.clip(w1 * w2 - 0.55, 0, 1) * 2.4
        img = base + spark[..., None] * np.array([150, 200, 230], np.float32) * 0.9
        img *= _vignette(H, W, 0.42)
        return img

    return frame


def _scene_sky_clouds(seed: int):
    base = _vertical("#7FB2DE", "#DDEAF2", H, W, 0.85)
    cloud = _smooth_noise(H, W, 5, seed + 13, 3)[..., None]

    def frame(t: float) -> np.ndarray:
        shift = int((t / LENGTH_S) * W * 0.20)
        c = np.roll(cloud, shift, axis=1)
        img = base * (0.80 + 0.42 * c) + 40 * np.clip(c - 0.6, 0, 1)
        img *= _vignette(H, W, 0.26)
        return img

    return frame


def _scene_green_leaves(seed: int):
    base = _vertical("#123A1C", "#05140A", H, W, 1.2)
    leaves = _smooth_noise(H, W, 4, seed + 17, 3)
    bokeh = _bokeh(H, W, 14, seed + 21, (int(H * 0.06), int(H * 0.22)), np.array([0.55, 0.95, 0.55]))

    def frame(t: float) -> np.ndarray:
        sway = np.roll(leaves, int(math.sin(t / LENGTH_S * math.tau) * W * 0.03), axis=1)
        img = base * (0.75 + 0.75 * sway[..., None])
        img += bokeh * 0.55
        img *= _vignette(H, W, 0.50)
        return img

    return frame


def _scene_night_lights(seed: int):
    base = _vertical("#0A1024", "#02040B", H, W, 1.0)
    near = _bokeh(H, W, 26, seed + 23, (int(H * 0.02), int(H * 0.07)), np.array([1.0, 0.82, 0.45]), 0.65)
    far = _bokeh(H, W, 60, seed + 29, (int(H * 0.01), int(H * 0.03)), np.array([0.60, 0.75, 1.0]), 0.45)

    def frame(t: float) -> np.ndarray:
        tw = 0.86 + 0.24 * (0.5 + 0.5 * math.sin(t * 1.7))
        img = base + far * 0.7 * tw + np.roll(near, int(math.sin(t * 0.5) * 6), axis=0) * 0.9
        img *= _vignette(H, W, 0.45)
        return img

    return frame


def _scene_dust_sunbeam(seed: int):
    base = _vertical("#3A2E1E", "#0B0805", H, W, 1.3)
    beam = np.zeros((H, W), np.float32)
    for i in range(W):
        cx = W * 0.5 + (i - W * 0.5) * 0.0
        beam[:, i] = math.exp(-((i - W * 0.45) ** 2) / (2 * (W * 0.20) ** 2))
    beam = beam * np.linspace(0.2, 1.0, H, dtype=np.float32)[:, None]
    base += beam[..., None] * _hex("#FFDC9E") * 0.55
    motes = np.random.default_rng(seed + 31).random((H, W)).astype(np.float32)

    def frame(t: float) -> np.ndarray:
        m = np.roll(motes, int(t * 26) % H, axis=0) > 0.9990
        img = base.copy()
        img[m] += 150
        img *= _vignette(H, W, 0.48)
        return img

    return frame


def _scene_stone_wall(seed: int):
    base = _vertical("#6E6558", "#2C2721", H, W, 0.9)
    tex = _smooth_noise(H, W, 2, seed + 37, 3)[..., None]
    base *= (0.72 + 0.55 * tex)

    def frame(t: float) -> np.ndarray:
        shade = 0.94 + 0.12 * math.sin(t / LENGTH_S * math.tau)
        img = base * shade
        img *= _vignette(H, W, 0.44)
        return img

    return frame


def _scene_calm_sea(seed: int):
    horizon = int(H * 0.55)
    sky = _vertical("#1B3A4B", "#7FA8C0", horizon, W, 0.8)
    sea = _vertical("#0A1B26", "#040A10", H - horizon, W, 0.7)
    n = _smooth_noise(H - horizon, W, 5, seed + 41, 3)

    def frame(t: float) -> np.ndarray:
        phase = t / LENGTH_S * math.tau
        rows = (np.arange(H - horizon, dtype=np.float32) / max(1, H - horizon))[:, None]
        wave = np.sin(n * 10 + phase * 2 + rows * 7) * 0.5 + 0.5
        foam = np.clip(wave - 0.72, 0, 1) * 3.0
        s = sea + foam[..., None] * 0.75
        img = np.concatenate([sky, s], axis=0)
        img *= _vignette(H, W, 0.34)
        return img

    return frame


def _scene_desert_dunes(seed: int):
    base = _vertical("#C79A5B", "#3A2716", H, W, 0.9)
    dune = _smooth_noise(H, W, 4, seed + 43, 3)
    ridge = (dune > 0.52).astype(np.float32)

    def frame(t: float) -> np.ndarray:
        s = np.roll(dune, int((t / LENGTH_S) * W * 0.05), axis=1)
        img = base * (0.85 + 0.35 * s[..., None])
        img += (np.clip(s - 0.62, 0, 1) * 220)[..., None]
        img *= _vignette(H, W, 0.40)
        return img

    return frame


def _scene_mountain_mist(seed: int):
    layers = []
    for i in range(4):
        ln = _smooth_noise(H, W, 5 + i * 3, seed + 47 + i, 3)
        shade = 0.30 + i * 0.13
        layers.append(ln * shade)
    mist = _smooth_noise(H, W, 7, seed + 59, 2)

    def frame(t: float) -> np.ndarray:
        acc = np.zeros((H, W), np.float32)
        for i, ln in enumerate(layers):
            acc += np.roll(ln, int((t / LENGTH_S) * W * (0.02 + i * 0.015)), axis=1)
        m = np.roll(mist, int((t / LENGTH_S) * W * 0.09), axis=1)
        img = (_hex("#4E6B84")[None, None, :] * acc[..., None]
               + _hex("#C7D6E0")[None, None, :] * np.clip(m - 0.35, 0, 1)[..., None] * 0.55)
        img *= _vignette(H, W, 0.34)
        return img

    return frame


def _scene_palm_sunset(seed: int):
    base = _vertical("#FFB26B", "#6E2C4E", H, W, 0.75)
    sun = _bokeh(H, W, 1, seed + 61, (int(H * 0.12), int(H * 0.16)), np.array([1.0, 0.86, 0.55]), 0.9)
    sil = _smooth_noise(H, W, 3, seed + 67, 2)

    def frame(t: float) -> np.ndarray:
        img = base * (0.96 + 0.06 * math.sin(t / LENGTH_S * math.tau))
        img += np.roll(sun, int(math.sin(t * 0.4) * 4), axis=0) * 0.85
        dark = np.clip(sil - 0.55, 0, 1)[..., None] * 2.2
        img *= (1 - np.clip(dark, 0, 0.85))
        img *= _vignette(H, W, 0.35)
        return img

    return frame


def _scene_fabric_fold(seed: int):
    base = _vertical("#8A7A6A", "#2A241E", H, W, 0.8)
    folds = _smooth_noise(H, W, 3, seed + 71, 3)

    def frame(t: float) -> np.ndarray:
        s = np.roll(folds, int(math.sin(t / LENGTH_S * math.tau) * W * 0.05), axis=1)
        img = base * (0.78 + 0.45 * s[..., None])
        img *= _vignette(H, W, 0.42)
        return img

    return frame


def _dot(acc: np.ndarray, cy: float, cx: float, rad: float, val: float) -> None:
    """نقطة ضوء صغيرة — بترسم على نافذة صغيرة بس (سرعة)."""
    h, w = acc.shape
    r = int(max(1, rad))
    y0, y1 = max(0, int(cy) - r), min(h, int(cy) + r + 1)
    x0, x1 = max(0, int(cx) - r), min(w, int(cx) + r + 1)
    if y1 <= y0 or x1 <= x0:
        return
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    d = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    acc[y0:y1, x0:x1] += np.clip(1 - d / max(rad, 1e-3), 0, 1) ** 2 * val


def _scene_rain_glass(seed: int):
    base = _vertical("#22323E", "#0A1118", H, W, 1.0)
    bg = _smooth_noise(H, W, 3, seed + 3, 3)
    glow = _bokeh(H, W, 7, seed + 5, (int(H * 0.10), int(H * 0.30)),
                  np.array([0.50, 0.66, 0.80]))
    rng = np.random.default_rng(seed + 11)
    drops = [(rng.uniform(0, W), rng.uniform(0, 1), rng.uniform(2.0, 6.5),
              rng.uniform(0.20, 1.0)) for _ in range(110)]

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        img = base * (0.70 + 0.50 * bg[..., None]) + glow * 0.85
        acc = np.zeros((H, W), np.float32)
        for (x0, sy, rad, sp) in drops:
            cy = ((sy + p * sp) % 1.0) * H
            _dot(acc, cy, x0, rad, 0.85)
        streak = np.clip(np.roll(bg, 12, axis=1) - 0.62, 0, 1) * 0.5
        acc += streak * (0.6 + 0.4 * math.sin(t * 4.0))
        img += np.clip(acc, 0, 1)[..., None] * np.array([185, 212, 232], np.float32) * 0.85
        img *= _vignette(H, W, 0.44)
        return img

    return frame


def _scene_candle_flame(seed: int):
    base = _vertical("#241605", "#070402", H, W, 1.0)
    n = _smooth_noise(H, W, 4, seed + 2, 3)
    yy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S * math.tau
        flick = 0.87 + 0.13 * math.sin(p * 3.0) + 0.05 * math.sin(p * 7.0)
        wob = 0.07 * math.sin(p * 2.0)
        body = np.exp(-(((xx - wob) / 0.15) ** 2 + ((yy + 0.14) / (0.30 * flick)) ** 2) * 1.7)
        halo = np.exp(-(((xx - wob) / 0.46) ** 2 + (yy / 0.58) ** 2) * 1.2)
        img = base * (0.80 + 0.50 * n[..., None])
        img += body[..., None] * np.array([255, 196, 96], np.float32) * 1.10 * flick
        img += halo[..., None] * np.array([255, 142, 52], np.float32) * 0.30
        img *= _vignette(H, W, 0.58)
        return img

    return frame


def _scene_open_book(seed: int):
    paper = _vertical("#F6ECD6", "#DFCFAC", H, W, 0.65)
    grain = _smooth_noise(H, W, 3, seed + 4, 3)
    rows = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    lines = np.clip(np.sin(rows * 74 * math.pi) * 0.5 + 0.5, 0, 1)
    warm = _bokeh(H, W, 5, seed + 9, (int(H * 0.22), int(H * 0.52)),
                  np.array([0.32, 0.24, 0.14]))

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        shade = 0.90 + 0.10 * math.sin(p * math.tau)
        shift = int(p * H * 0.02)
        lns = np.roll(lines, shift, axis=0)
        ink = np.clip(0.60 - lns, 0, 1) * 0.30
        img = paper * (0.90 + 0.16 * grain[..., None]) * shade
        img *= (1 - ink[..., None] * 0.55)
        img += warm * 0.55
        img *= _vignette(H, W, 0.32)
        return img

    return frame


def _scene_tea_steam(seed: int):
    base = _vertical("#2B1E13", "#0A0704", H, W, 1.2)
    n = _smooth_noise(H, W, 4, seed + 6, 3)
    n2 = _smooth_noise(H, W, 5, seed + 8, 3)
    yy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    cup = np.exp(-((yy / 0.26) ** 2 + (xx / 0.34) ** 2) * 1.5)

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        up = np.roll(n, int(-p * H * 0.55), axis=0)
        up2 = np.roll(n2, int(-p * H * 0.95), axis=0)
        steam = np.clip(up * 0.72 + up2 * 0.55 - 0.44, 0, 1) * 1.5
        img = base * (0.85 + 0.40 * n[..., None])
        img += np.clip(steam, 0, 1)[..., None] * np.array([214, 205, 190], np.float32) * 0.55
        img += cup[..., None] * np.array([130, 86, 48], np.float32) * 0.55
        img *= _vignette(H, W, 0.50)
        return img

    return frame


def _scene_wheat_field(seed: int):
    base = _vertical("#CB9C41", "#6A4A18", H, W, 0.9)
    stalks = _smooth_noise(H, W, 6, seed + 10, 2)
    cols = np.linspace(0, 1, W, dtype=np.float32)[None, :]

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S * math.tau
        sway = np.roll(stalks, int(math.sin(p) * W * 0.04), axis=1)
        fine = np.clip(np.sin(cols * 430 * math.pi + sway * 7.0) * 0.5 + 0.5, 0, 1)
        img = base * (0.70 + 0.58 * sway[..., None])
        img += fine[..., None] * np.array([255, 224, 148], np.float32) * 0.17
        img *= _vignette(H, W, 0.38)
        return img

    return frame


def _scene_mashrabiya(seed: int):
    base = _vertical("#3A2A16", "#0B0703", H, W, 1.0)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    center = np.clip(1 - np.abs(xx - 0.5) * 1.7, 0, 1)

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S * math.tau
        drift = 0.05 * math.sin(p)
        lat = np.sin((xx + drift) * math.pi * 24) * np.sin((yy + drift * 0.35) * math.pi * 17)
        pat = np.clip(lat, 0, 1) ** 1.5
        img = base * (0.55 + 1.15 * pat[..., None])
        img += (center[..., None] * pat[..., None]) * np.array([255, 216, 142], np.float32) * 0.42
        img *= _vignette(H, W, 0.55)
        return img

    return frame


def _scene_night_stars(seed: int):
    base = _vertical("#050B1E", "#01030A", H, W, 1.0)
    band = _smooth_noise(H, W, 4, seed + 14, 3)
    rng = np.random.default_rng(seed + 12)
    stars = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.0, 2.8),
              rng.uniform(0, math.tau), rng.uniform(0.6, 1.6)) for _ in range(150)]

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        img = base * (0.75 + 0.55 * band[..., None])
        img += np.clip(band - 0.66, 0, 1)[..., None] * np.array([70, 90, 150], np.float32) * 0.55
        acc = np.zeros((H, W), np.float32)
        for (x0, y0, rad, ph, sp) in stars:
            x = (x0 + p * W * 0.012) % W
            _dot(acc, y0, x, rad, 0.55 + 0.45 * math.sin(ph + t * sp))
        img += np.clip(acc, 0, 1)[..., None] * np.array([235, 240, 255], np.float32) * 0.95
        img *= _vignette(H, W, 0.40)
        return img

    return frame


# ─────────── العيلة السينمائية (درس الحلقات القديمة 2026-10-12) ───────────
# قارنّا مشاهدنا بمشاهد الحلقات المنشورة قديمًا (release: episodes) — طلع
# الفرق واضح: اللي بيخلي الإطار حلو هو (١) مصدر ضوء مركزي، (٢) تدرّج سماوي
# بألوان قوية، (٣) صورة ظليلة واضحة (ridge/palm)، (٤) سطح بيعكس (بحر/رمل).
# العيلة دي بتبني الأربعة دول هندسيًا — مش ضجيج بس.

def _grad_stops(stops, h: int, w: int) -> np.ndarray:
    """تدرّج متعدد المحطات (لونين أو أكتر) — أساس السما الحلوة."""
    pos = np.array([p for p, _ in stops], np.float32)
    cols = np.stack([_hex(c) for _, c in stops])
    f = np.linspace(0, 1, h, dtype=np.float32)
    idx = np.clip(np.searchsorted(pos, f, side="right") - 1, 0, len(pos) - 2)
    t = np.clip((f - pos[idx]) / np.maximum(pos[idx + 1] - pos[idx], 1e-6), 0, 1)[:, None]
    band = cols[idx] * (1 - t) + cols[idx + 1] * t        # (H,3)
    return np.repeat(band[:, None, :], w, axis=1)          # (H,W,3)


def _sun(cx: float, cy: float, rad: float,
         core: str = "#FFF7E0", glow: str = "#FFC46B") -> tuple[np.ndarray, np.ndarray]:
    """قرص شمس + هالة — بيحوّل أي مشهد من مسطح لمشهد فيه مصدر ضوء."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    d = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    disk = np.clip(1 - d / max(rad, 1e-3), 0, 1) ** 0.30
    halo = np.clip(1 - d / max(rad * 6.0, 1e-3), 0, 1) ** 2.4
    img = (halo[..., None] * _hex(glow) * 0.80
           + disk[..., None] * _hex(core))
    return img, halo


def _rays(cx: float, cy: float, n: int = 16, strength: float = 0.30) -> np.ndarray:
    """أشعة شعاعية من الشمس — للحظات «نور»."""
    yy = np.arange(H, dtype=np.float32)[:, None] - cy
    xx = np.arange(W, dtype=np.float32)[None, :] - cx
    ang = np.arctan2(yy, xx)
    r = np.sqrt(yy ** 2 + xx ** 2)
    beams = np.clip(np.cos(ang * n) * 0.5 + 0.5, 0, 1) ** 2.2
    fall = np.clip(1 - r / (H * 0.85), 0, 1) ** 1.6
    return beams * fall * strength


def _ridge(y_at: np.ndarray, colour: str, soft: float = 6.0,
           sky_frac: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """تلة/كثيب ظليلة — الصورة الواضحة اللي العين بتحبها."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    mask = np.clip((yy - y_at[None, :]) / max(soft, 1e-3), 0, 1)
    return mask[..., None] * _hex(colour)[None, None, :], mask


def _scene_sunset_sea(seed: int):
    horizon = H * 0.60
    sky = _grad_stops([(0.00, "#1E2E52"), (0.30, "#6E4470"), (0.55, "#D96A45"),
                       (0.78, "#FFB255"), (1.00, "#FFDCA0")], H, W)
    sea = _grad_stops([(0.00, "#101E2C"), (1.00, "#03060B")], H, W)
    ripple = _smooth_noise(H, W, 6, seed + 3, 3)
    sun_img, _ = _sun(W * 0.5, horizon - H * 0.015, H * 0.040)
    rays = _rays(W * 0.5, horizon - H * 0.015, 13, 0.22)
    rows = np.arange(H, dtype=np.float32)[:, None]
    col = np.clip(1 - np.abs(np.arange(W, dtype=np.float32)[None, :] - W * 0.5) / (W * 0.15), 0, 1) ** 1.7
    below = np.clip((rows - horizon) / max(H - horizon, 1.0), 0, 1)
    horizon_glow = np.exp(-((rows - horizon) ** 2) / (2 * 4.0 ** 2))

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        skew = math.sin(p * math.tau) * 3.0
        sky_f = np.roll(sky, int(p * W * 0.05), axis=1) * (0.94 + 0.06 * p)
        img = sky_f + sun_img + rays[..., None] * _hex("#FFE0A8")
        sea_f = sea * (0.62 + 0.75 * ripple[..., None])
        refl = col * (1 - below) ** 1.2 * (0.45 + 0.55 * np.abs(np.sin(rows * 0.55 + p * 22.0)))
        sea_f = sea_f + refl[..., None] * _hex("#FFC978") * 0.85
        sea_f = sea_f + horizon_glow[..., None] * _hex("#FFD9A0") * 0.22
        blend = _blur_mask((rows > horizon).astype(np.float32), 5.0)[..., None]
        img = img * (1 - blend) + sea_f * blend
        return img

    return frame


def _scene_golden_dunes(seed: int):
    sky = _grad_stops([(0.00, "#26365C"), (0.35, "#8A5566"), (0.60, "#E4844B"),
                       (0.82, "#FFB65E"), (1.00, "#FFE0A8")], H, W)
    n = _smooth_noise(H, W, 6, seed + 5, 2)
    sun_img, _ = _sun(W * 0.62, H * 0.36, H * 0.052)
    x = np.linspace(0, math.tau, W, dtype=np.float32)
    r_back = (H * 0.60 + np.sin(x * 1.3 + 1.1) * H * 0.035).astype(np.float32)
    r_mid = (H * 0.72 + np.sin(x * 0.9 + 3.0) * H * 0.045).astype(np.float32)
    r_front = (H * 0.86 + np.sin(x * 0.7 + 5.2) * H * 0.030).astype(np.float32)
    m_back, back = _ridge(r_back, "#C08A4E", 3.0)
    m_mid, mid = _ridge(r_mid, "#8A5A2E", 4.0)
    m_front, front = _ridge(r_front, "#4A2F16", 6.0)

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        sway = math.sin(p * math.tau) * 0.5 + 0.5
        img = sky * (0.96 + 0.04 * p)
        img = img * (1 - back[..., None]) + m_back * (0.85 + 0.30 * n[..., None])
        img = img * (1 - mid[..., None]) + m_mid * (0.80 + 0.35 * np.roll(n, 18, axis=1)[..., None])
        img = img * (1 - front[..., None]) + m_front * (0.75 + 0.40 * np.roll(n, 42, axis=0)[..., None])
        img = img + sun_img * (1 - front[..., None]) * (0.75 + 0.25 * sway)
        return img

    return frame


def _scene_sunrays_clouds(seed: int):
    sky = _grad_stops([(0.00, "#3C6FA8"), (0.45, "#9CC3DE"), (1.00, "#F4E3C4")], H, W)
    cloud = _blur_mask(_smooth_noise(H, W, 5, seed + 7, 3), 6.0)
    puffs = _blur_mask(_smooth_noise(H, W, 3, seed + 11, 3), 14.0)
    sun_img, halo = _sun(W * 0.5, H * 0.30, H * 0.050, "#FFFDF2", "#FFD98A")
    rays = _rays(W * 0.5, H * 0.30, 15, 0.34)

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        c1 = np.roll(cloud, int(p * W * 0.10), axis=1)
        c2 = np.roll(puffs, int(p * W * 0.05), axis=1)
        layer = np.clip(c1 * 0.8 + c2 * 0.6 - 0.62, 0, 1) * 2.2
        img = sky + rays[..., None] * _hex("#FFF3D0")
        img = img * (1 - np.clip(layer, 0, 1)[..., None] * 0.85) \
            + np.clip(layer, 0, 1)[..., None] * _hex("#FFF8EA") * 0.95
        img = img + sun_img * 0.9
        img = img + halo[..., None] * _hex("#FFE9B8") * 0.25
        return img

    return frame


def _scene_palms_sunset(seed: int):
    sky = _grad_stops([(0.00, "#2B2B52"), (0.34, "#8C4F6A"), (0.58, "#E07A4A"),
                       (0.80, "#FFB75F"), (1.00, "#FFE4B0")], H, W)
    sun_img, _ = _sun(W * 0.30, H * 0.46, H * 0.045)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    dune_y = (H * 0.86 + np.sin(np.linspace(0, math.tau * 1.2, W, dtype=np.float32)) * H * 0.02).astype(np.float32)
    dune, dune_m = _ridge(dune_y, "#3A2412", 6.0)
    trunks = np.zeros((H, W), np.float32)
    fronds = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(seed + 13)
    for (bx, sc) in [(0.16, 1.0), (0.80, 0.82), (0.90, 0.62)]:
        cx = bx * W + rng.uniform(-8, 8)
        top = H * 0.40 + rng.uniform(-H * 0.03, H * 0.03)
        cur = (xx - cx) / (24.0 * sc)
        trunk = np.exp(-(cur ** 2)) * np.clip((yy - top) / (dune_y[0] - top + 1), 0, 1)
        trunks = np.maximum(trunks, trunk)
        for k in range(7):
            ang = math.pi * (0.12 + 0.13 * k)
            L = H * (0.10 + 0.05 * math.sin(k * 1.7)) * sc
            px = cx + math.cos(ang) * L * 1.5
            py = top + math.sin(ang) * L * 0.55
            for frac in np.linspace(0.15, 1.0, 14):
                qx = cx + math.cos(ang) * L * 1.45 * frac
                qy = top + math.sin(ang) * L * 0.62 * frac + L * 0.85 * frac * frac
                wdt = (26.0 - 13.0 * frac) * sc
                seg = np.exp(-(((xx - qx) / wdt) ** 2 + ((yy - qy) / (8.5 * sc)) ** 2))
                fronds = np.maximum(fronds, seg)
    tree = np.clip(trunks + fronds * 0.95, 0, 1)

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        sway = np.roll(tree, int(math.sin(p * math.tau) * 4), axis=1)
        img = sky * (0.95 + 0.05 * p) + sun_img
        img = img * (1 - dune_m[..., None]) + dune * (0.7 + 0.4 * _smooth_noise(H, W, 5, seed + 2, 2)[..., None])
        img = img * (1 - np.clip(sway[..., None], 0, 1)) + np.clip(sway[..., None], 0, 1) * _hex("#1A0F08") * 0.96
        return img

    return frame


def _scene_mountain_layers(seed: int):
    sky = _grad_stops([(0.00, "#37527A"), (0.40, "#9FB6C9"), (0.75, "#E8D3AE"),
                       (1.00, "#F6E7C8")], H, W)
    sun_img, _ = _sun(W * 0.72, H * 0.30, H * 0.038, "#FFFBF0", "#FFE7B0")
    x = np.linspace(0, math.tau, W, dtype=np.float32)
    layers = []
    for i, (base, col, amp, ph) in enumerate([
            (0.52, "#7C93AB", 0.030, 0.4), (0.60, "#5F7A93", 0.040, 2.1),
            (0.70, "#41596F", 0.050, 3.6), (0.82, "#26394A", 0.045, 5.0),
            (0.94, "#132029", 0.035, 1.2)]):
        y = (H * base + np.sin(x * (1.1 + i * 0.37) + ph) * H * amp
             + np.sin(x * (2.9 + i * 0.5) + ph * 2) * H * amp * 0.35).astype(np.float32)
        m, mask = _ridge(y, col, 2.5 + i)
        layers.append((m, mask, i))

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        img = sky * (0.97 + 0.05 * p) + sun_img
        for m, mask, i in layers:
            haze = 1.0 - i * 0.045
            tint = 0.10 + i * 0.05
            img = img * (1 - mask[..., None]) + (m * haze + _hex("#93ADC0") * tint * mask[..., None])
        fog = _smooth_noise(H, W, 5, seed + 17, 3)
        img = img + np.clip(fog - 0.55, 0, 1)[..., None] * _hex("#E9F0F5") * 0.10 * (0.35 + 0.25 * p)
        return img

    return frame


def _scene_night_milky(seed: int):
    sky = _grad_stops([(0.00, "#050A1C"), (0.45, "#0B1533"), (0.75, "#1B2A4A"),
                       (1.00, "#3A4A66")], H, W)
    band = _smooth_noise(H, W, 4, seed + 19, 3)
    fine = _smooth_noise(H, W, 6, seed + 23, 2)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    diag = np.clip(1 - np.abs((xx * 0.35 + yy * 0.9) / H - 0.55) / 0.30, 0, 1) ** 1.5
    milky = np.clip((band * 0.7 + fine * 0.5 - 0.30), 0, 1) * diag * 1.8
    horizon_y = (H * 0.86 + np.sin(np.linspace(0, math.tau, W, dtype=np.float32)) * H * 0.012).astype(np.float32)
    hill, hill_m = _ridge(horizon_y, "#050A10", 5.0)
    rng = np.random.default_rng(seed + 29)
    stars = [(rng.uniform(0, W), rng.uniform(0, H * 0.88),
              rng.uniform(1.8, 4.2), rng.uniform(0, math.tau), rng.uniform(0.5, 1.5))
             for _ in range(230)]

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        img = sky * (0.9 + 0.1 * band[..., None])
        img = img + milky[..., None] * _hex("#9FB6E8") * 0.55
        acc = np.zeros((H, W), np.float32)
        for (x0, y0, rad, ph, sp) in stars:
            x = (x0 + p * W * 0.02) % W
            _dot(acc, y0, x, rad, 0.55 + 0.45 * math.sin(ph + t * sp))
        halo = _blur_mask(np.clip(acc, 0, 1), 3.0)
        img = img + np.clip(acc, 0, 1)[..., None] * _hex("#EEF2FF") * 0.95
        img = img + halo[..., None] * _hex("#B9CCFF") * 0.30
        img = img * (1 - hill_m[..., None]) + hill * 0.96
        return img

    return frame


def _scene_rain_window_v2(seed: int):
    sky = _grad_stops([(0.00, "#2E4557"), (0.55, "#43606F"), (1.00, "#243642")], H, W)
    rng = np.random.default_rng(seed + 31)
    drops = [(rng.uniform(0, W), rng.uniform(0, 1), rng.uniform(3.5, 11.0), rng.uniform(0.25, 1.15))
             for _ in range(130)]
    glow = _bokeh(H, W, 11, seed + 37, (int(H * 0.05), int(H * 0.20)),
                  np.array([0.85, 0.90, 1.0]), alpha=0.75)

    def frame(t: float) -> np.ndarray:
        p = t / LENGTH_S
        img = sky * (0.95 + 0.05 * p) + glow * 0.75
        acc = np.zeros((H, W), np.float32)
        for (x0, sy, rad, sp) in drops:
            cy = ((sy + p * sp) % 1.0) * H
            _dot(acc, cy, x0, rad, 0.80)
            _dot(acc, cy + rad * 2.6, x0, rad * 0.55, 0.35)   # ذيل القطرة
        img = img + np.clip(acc, 0, 1)[..., None] * _hex("#D8E8F6") * 0.95
        return img

    return frame


SCENES: dict[str, dict] = {
    "sunset_sea":    {"fn": _scene_sunset_sea,    "ar": "غروب على البحر", "tags": ("sunset", "sea", "golden", "horizon", "غروب", "بحر", "شمس", "نور", "تأمل", "راحة")},
    "golden_dunes":  {"fn": _scene_golden_dunes,  "ar": "كثبان الدهب", "tags": ("dunes", "desert", "golden", "sand", "صحراء", "رمل", "كثبان", "غروب", "شمس")},
    "sunrays_clouds": {"fn": _scene_sunrays_clouds, "ar": "أشعة وسحاب", "tags": ("rays", "clouds", "sky", "hope", "سحاب", "سماء", "نور", "أمل", "رحمة")},
    "palms_sunset":  {"fn": _scene_palms_sunset,  "ar": "نخل وقت الغروب", "tags": ("palm", "sunset", "silhouette", "نخل", "غروب", "شمس", "صحراء")},
    "mountain_layers": {"fn": _scene_mountain_layers, "ar": "جبال متطبقة", "tags": ("mountain", "layers", "mist", "جبل", "ضباب", "سكون", "خلق")},
    "night_milky":   {"fn": _scene_night_milky,   "ar": "مجرّة الليل", "tags": ("stars", "milkyway", "night", "sky", "نجوم", "مجرّة", "ليل", "تأمل", "كون")},
    "rain_window_v2": {"fn": _scene_rain_window_v2, "ar": "مطر على الشباك", "tags": ("rain", "window", "drops", "مطر", "شتا", "شباك", "رحمة")},

    "rain_glass":    {"fn": _scene_rain_glass,    "ar": "مطر على الزجاج", "tags": ("rain", "drops", "glass", "wet", "مطر", "شتا", "زجاج", "غيث")},
    "candle_flame":  {"fn": _scene_candle_flame,  "ar": "شمعة", "tags": ("candle", "flame", "warm", "glow", "شمعة", "نور", "دفء", "دعاء")},
    "open_book":     {"fn": _scene_open_book,     "ar": "كتاب مفتوح", "tags": ("book", "pages", "paper", "read", "كتاب", "مصحف", "قرآن", "علم", "صفحة")},
    "tea_steam":     {"fn": _scene_tea_steam,     "ar": "شاي وبخار", "tags": ("tea", "steam", "cup", "calm", "شاي", "بخار", "ضيافة", "هدوء")},
    "wheat_field":   {"fn": _scene_wheat_field,   "ar": "زرع وغلّة", "tags": ("wheat", "field", "harvest", "golden", "زرع", "غلّة", "حصاد", "خير", "رزق")},
    "mashrabiya":    {"fn": _scene_mashrabiya,    "ar": "مشربية ونور", "tags": ("mosque", "arch", "lattice", "prayer", "مسجد", "مشربية", "صلاة", "أذان", "صلات")},
    "night_stars":   {"fn": _scene_night_stars,   "ar": "نجوم الليل", "tags": ("stars", "milky", "night", "sky", "نجوم", "تأمل", "ليل", "كون")},

    "window_light":  {"fn": _scene_window_light,  "ar": "ضوء شباك", "tags": ("window", "light", "curtain", "sunrise", "morning", "نور", "شباك", "ضوء", "صبح", "فجر")},
    "sunlit_floor":  {"fn": _scene_sunlit_floor,  "ar": "أرضية بالشمس", "tags": ("floor", "sunlit", "wood", "home", "بيت", "أرضية", "تراب", "نضافة")},
    "kitchen_clean": {"fn": _scene_kitchen_clean, "ar": "مطبخ نضيف", "tags": ("kitchen", "counter", "clean", "sink", "مطبخ", "حوض", "نضافة", "أكل")},
    "water_ripple":  {"fn": _scene_water_ripple,  "ar": "ميه رايقة", "tags": ("water", "ripple", "reflection", "ميه", "ماء", "بحر", "هدوء")},
    "sky_clouds":    {"fn": _scene_sky_clouds,    "ar": "سما وسحاب", "tags": ("sky", "clouds", "blue", "سماء", "سحاب", "صبح")},
    "green_leaves":  {"fn": _scene_green_leaves,  "ar": "زرع وأوراق", "tags": ("leaves", "green", "plant", "garden", "زرع", "نبات", "شجر", "حديقة")},
    "night_lights":  {"fn": _scene_night_lights,  "ar": "أنوار الليل", "tags": ("night", "lights", "bokeh", "city", "ليل", "نجوم", "أنوار")},
    "dust_sunbeam":  {"fn": _scene_dust_sunbeam,  "ar": "شعاع وتراب", "tags": ("beam", "dust", "sunbeam", "dark", "تراب", "نور", "ضوء")},
    "stone_wall":    {"fn": _scene_stone_wall,    "ar": "حيطة حجر", "tags": ("stone", "wall", "texture", "حجر", "حيطة", "باب")},
    "calm_sea":      {"fn": _scene_calm_sea,      "ar": "بحر هادي", "tags": ("sea", "ocean", "horizon", "بحر", "إسكندرية", "نيل")},
    "desert_dunes":  {"fn": _scene_desert_dunes,  "ar": "كثبان", "tags": ("desert", "dunes", "sand", "صحراء", "رمل")},
    "mountain_mist": {"fn": _scene_mountain_mist, "ar": "جبال وضباب", "tags": ("mountain", "mist", "fog", "جبل", "ضباب")},
    "palm_sunset":   {"fn": _scene_palm_sunset,   "ar": "غروب ونخل", "tags": ("sunset", "palm", "warm", "مغرب", "غروب", "نخل")},
    "fabric_fold":   {"fn": _scene_fabric_fold,   "ar": "قماش ناعم", "tags": ("fabric", "cloth", "soft", "قماش", "هدوء")},
}


# ───────────────────────── البناء ─────────────────────────

def _write_clip(frames, out: Path, w: int = W, h: int = H) -> None:
    """يرفع الدقة لـ1080×1920 ويكتب H.264 (متوافق مع باقي المصنع)."""
    cmd = [
        FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
        "-vf", f"scale=1080:1920:flags=bicubic,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-movflags", "+faststart", str(out),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for img in frames:
        proc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg فشل في كتابة {out}")


def build(names: list[str] | None = None, length_s: float = LENGTH_S) -> list[Path]:
    """يبني (أو يعيد بناء) مشاهد الخزنة ويسجّلها بترخيص Internal-Generated."""
    from xtrendaw import vault

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    targets = names or list(SCENES)
    total_frames = int(length_s * FPS)
    for name in targets:
        spec = SCENES.get(name)
        if not spec:
            print(f"[scenes] ⚠ مشهد غير معروف: {name}", flush=True)
            continue
        out = OUT_DIR / f"gen_{name}.mp4"
        if out.exists() and out.stat().st_size > 10_000:
            made.append(out)
            print(f"[scenes] ✔ موجود: {out.name}", flush=True)
            continue
        seed = abs(hash(name)) % (2 ** 31)
        frame_fn = _calibrate(spec["fn"](seed))
        print(f"[scenes] ⏳ برسم «{spec['ar']}» ({name})…", flush=True)
        frames = (frame_fn(i / FPS) for i in range(total_frames))
        _write_clip(frames, out)
        try:
            vault.register(out, source="مصنع نور — توليد برمجي داخلي",
                           license="Internal-Generated", attribution_required=False,
                           credit_line="", url="")
        except Exception as exc:
            print(f"[scenes] ⚠ التسجيل: {type(exc).__name__}: {exc}", flush=True)
        made.append(out)
        print(f"[scenes] ✅ {out.name} ({out.stat().st_size // 1024} ك.ب)", flush=True)
    return made


def matches(query: str) -> list[str]:
    """كل المشاهد اللي ليها صلة بالاستعلام (عربي أو إنجليزي)، الأقرب الأول."""
    q = (query or "").lower()
    scored = [(sum(1 for tag in spec["tags"] if tag in q), name)
              for name, spec in SCENES.items()]
    best = max((h for h, _ in scored), default=0)
    if best == 0:
        return []
    return [name for hits, name in sorted(scored, key=lambda x: (-x[0], x[1])) if hits >= best]


def _seed_num(seed: str) -> int:
    s = str(seed or "")
    if s.isdigit():
        return int(s)
    return sum((i + 1) * ord(c) for i, c in enumerate(s))


def pick(query: str, seed: str = "", require_match: bool = True) -> str | None:
    """يختار مشهد واحد — البذرة بتنوّع الاختيار.

    require_match=True: لازم المشهد له صلة حقيقية بالاستعلام (جودة المعنى).
    require_match=False: ملاذ أخير — أي مشهد عام بالبذرة، عشان المصنع
    ما يتوقفش أبدًا على «المشاهد ناقصة» (قرار 2026-10-12).
    """
    cands = matches(query)
    if not cands:
        if require_match or not SCENES:
            return None
        cands = sorted(SCENES)
    return cands[_seed_num(seed) % len(cands)]


def match(query: str) -> str | None:
    """توافق للخلف: أقرب مشهد واحد."""
    return pick(query)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "build"
    if cmd == "list":
        for name, spec in SCENES.items():
            print(f"  {name:16} {spec['ar']:14} {', '.join(spec['tags'][:6])}")
        return 0
    if cmd == "build":
        names = None
        if "--scene" in argv:
            names = [argv[argv.index("--scene") + 1]]
        made = build(names)
        print(f"[scenes] 🎬 {len(made)} مشهد جاهز في {OUT_DIR}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
