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
from PIL import Image

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
    return np.repeat(color[None, None, :], 1, axis=0)[..., :] * layer + layer * 0


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
    dust = _smooth_noise(H, W, 6, seed + 11, 2)[..., None]
    pane *= (0.82 + 0.30 * dust)
    base = _mix(base, pane, 0.90)
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
        img = base + spark[..., None] * np.array([150, 200, 230], np.float32) / 255 * 0.9
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
    base += beam[..., None] * _hex("#FFDC9E") / 255 * 0.55
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


SCENES: dict[str, dict] = {
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
        frame_fn = spec["fn"](seed)
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
