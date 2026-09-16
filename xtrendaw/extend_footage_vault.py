"""توسعة خزنة اللقطات — 5 مشاهد حركة إضافية مولّدة برمجيًا 100%.

نفس نمط `generate_footage_vault.py` (numpy + PIL → ffmpeg rawvideo):
مفيش أي تنزيل من النت، والترخيص ملك المشروع بالكامل (يُسجل في
`vault/index.json` كـ Internal-Generated بعد التوليد).
"""
from __future__ import annotations

import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xtrendaw.tts import ffmpeg  # noqa: E402

W, H, FPS = 1080, 1920, 30
FOOTAGE_DIR = Path(__file__).resolve().parent.parent / "assets" / "footage"


def _pipe(output_path: Path):
    return subprocess.Popen(
        [ffmpeg(), "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", str(output_path)],
        stdin=subprocess.PIPE)


def _finish(proc) -> None:
    proc.stdin.close()
    proc.wait(timeout=600)


def generate_ocean_waves(duration=5.0, filename="10_ocean_deep_waves.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    random.seed(10)
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (4, 22, 46, 255))
        d = ImageDraw.Draw(img)
        for k in range(14):
            base = int(H * (0.28 + k * 0.05))
            pts = []
            for x in range(0, W + 24, 24):
                y = base + int(42 * math.sin(x / 130 + t * 2.4 + k * 1.7)
                               + 20 * math.sin(x / 61 - t * 3.1 + k))
                pts.append((x, y))
            pts += [(W, H), (0, H)]
            alpha = 120 + k * 8
            d.polygon(pts, fill=(8 + k * 2, 70 + k * 7, 130 + k * 7, alpha))
        for _ in range(26):
            x = random.randint(0, W)
            y = random.randint(int(H * 0.3), H)
            r = random.randint(2, 6)
            d.ellipse([x, y, x + r, y + r], fill=(210, 240, 255, 120))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("ocean ok")


def generate_desert_dunes(duration=5.0, filename="11_desert_dunes_gold.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (66, 32, 8, 255))
        d = ImageDraw.Draw(img)
        sun_y = int(H * 0.30 + 26 * math.sin(t))
        for r, a in [(300, 26), (220, 46), (150, 90), (90, 200)]:
            d.ellipse([W // 2 - r, sun_y - r, W // 2 + r, sun_y + r],
                      fill=(255, 190, 90, a))
        for k in range(10):
            base = int(H * (0.45 + k * 0.055))
            pts = []
            for x in range(0, W + 20, 20):
                y = base + int(60 * math.sin(x / 260 + k * 2.1 + t * 0.9)
                               + 24 * math.sin(x / 90 + k))
                pts.append((x, y))
            pts += [(W, H), (0, H)]
            shade = 90 + k * 14
            d.polygon(pts, fill=(shade + 40, shade // 2 + 30, 22, 235))
        for _ in range(40):
            x = int((random.random() * W + t * 260) % W)
            y = random.randint(int(H * 0.5), H)
            d.line([(x, y), (x + 14, y - 3)], fill=(255, 220, 150, 70), width=2)
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("desert ok")


def generate_gold_rain(duration=5.0, filename="12_gold_treasure_rain.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    random.seed(12)
    coins = []
    for _ in range(70):
        coins.append({"x": random.random() * W, "y": random.random() * H,
                      "v": random.uniform(380, 780), "r": random.uniform(8, 22),
                      "ph": random.uniform(0, 6.28)})
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (22, 12, 2, 255))
        d = ImageDraw.Draw(img)
        cx, cy = W // 2, int(H * 0.82)
        for r, a in [(420, 30), (300, 56), (190, 96)]:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 200, 70, a))
        for c in coins:
            y = (c["y"] + t * c["v"]) % (H + 60) - 30
            x = c["x"] + 26 * math.sin(t * 3 + c["ph"])
            r = c["r"]
            d.ellipse([x - r, y - r * 0.62, x + r, y + r * 0.62],
                      fill=(255, 214, 90, 235), outline=(150, 96, 10, 255))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("gold ok")


def generate_green_energy(duration=5.0, filename="13_green_energy_pulse.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (2, 18, 10, 255))
        d = ImageDraw.Draw(img)
        cx, cy = W // 2, int(H * 0.45)
        pulse = 0.5 + 0.5 * math.sin(t * 4.2)
        for r, a in [(360, 22), (260, 44), (170, int(70 + 70 * pulse))]:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 255, 140, a))
        for k in range(22):
            ang = k / 22 * 6.283 + t * 1.4
            r0 = 120 + 40 * math.sin(t * 3 + k)
            x1 = cx + r0 * math.cos(ang)
            y1 = cy + r0 * math.sin(ang)
            x2 = cx + (r0 + 180) * math.cos(ang)
            y2 = cy + (r0 + 180) * math.sin(ang)
            d.line([(x1, y1), (x2, y2)], fill=(120, 255, 180, 120), width=3)
        for _ in range(60):
            x = random.randint(0, W)
            y = int((random.random() * H - t * 300) % H)
            d.ellipse([x, y, x + 4, y + 4], fill=(160, 255, 200, 150))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("energy ok")


def generate_lava_embers(duration=5.0, filename="14_lava_embers_flow.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    random.seed(14)
    embers = []
    for _ in range(90):
        embers.append({"x": random.random() * W, "y": random.random() * H,
                       "v": random.uniform(120, 420), "r": random.uniform(2, 7),
                       "ph": random.uniform(0, 6.28)})
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (24, 4, 2, 255))
        d = ImageDraw.Draw(img)
        for k in range(9):
            base = int(H * (0.55 + k * 0.05))
            pts = []
            for x in range(0, W + 22, 22):
                y = base + int(34 * math.sin(x / 120 + t * 2.6 + k * 1.9))
                pts.append((x, y))
            pts += [(W, H), (0, H)]
            d.polygon(pts, fill=(120 + k * 14, 26 + k * 4, 4, 200))
        for e in embers:
            y = (e["y"] - t * e["v"]) % (H + 40) - 20
            x = e["x"] + 30 * math.sin(t * 2 + e["ph"])
            a = int(140 + 100 * math.sin(t * 5 + e["ph"]))
            d.ellipse([x - e["r"], y - e["r"], x + e["r"], y + e["r"]],
                      fill=(255, 150, 40, max(30, a)))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("lava ok")


if __name__ == "__main__":
    FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)
    generate_ocean_waves()
    generate_desert_dunes()
    generate_gold_rain()
    generate_green_energy()
    generate_lava_embers()
    print("5 NEW CLIPS DONE")
