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


def generate_city_nights(duration=5.0, filename="15_blue_city_nights.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    random.seed(15)
    windows = []
    for _ in range(420):
        windows.append((random.randint(0, W - 14), random.randint(int(H * 0.35), H - 40),
                        random.random() * 6.28, random.choice([(255, 214, 110), (120, 220, 255)])))
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (6, 10, 34, 255))
        d = ImageDraw.Draw(img)
        for k in range(9):
            bw = 90 + (k * 53) % 130
            bx = (k * 137) % (W - bw)
            bh = int(H * (0.30 + 0.06 * ((k * 7) % 5)))
            d.rectangle([bx, H - bh, bx + bw, H], fill=(10 + k * 2, 16 + k * 2, 44, 255))
        for wx, wy, ph, col in windows:
            if math.sin(t * 1.4 + ph) > -0.6:
                d.rectangle([wx, wy, wx + 10, wy + 14], fill=col + (210,))
        for _ in range(3):
            cx = random.randint(0, W)
            cy = random.randint(0, int(H * 0.3))
            d.ellipse([cx, cy, cx + 3, cy + 3], fill=(255, 255, 255, 160))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("city ok")


def generate_red_alert(duration=5.0, filename="16_red_alert_siren.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    for f in range(n):
        t = f / FPS
        pulse = 0.5 + 0.5 * math.sin(t * 5.0)
        img = Image.new("RGBA", (W, H), (30, 2, 4, 255))
        d = ImageDraw.Draw(img)
        cx, cy = W // 2, H // 2
        for r, a in [(560, 20), (430, 34), (300, int(40 + 70 * pulse)), (180, int(70 + 120 * pulse))]:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 30, 30, a))
        ang = t * 2.6
        for delta, a in ((-0.5, 70), (0, 130), (0.5, 70)):
            rad = ang + delta
            d.polygon([(cx, cy),
                       (cx + 900 * math.cos(rad - 0.16), cy + 900 * math.sin(rad - 0.16)),
                       (cx + 900 * math.cos(rad + 0.16), cy + 900 * math.sin(rad + 0.16))],
                      fill=(255, 60, 40, a))
        d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(255, 90, 60, 255))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("alert ok")


def generate_galaxy_swirl(duration=5.0, filename="17_purple_galaxy_swirl.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    random.seed(17)
    stars = [(random.random() * W, random.random() * H, random.uniform(1, 3),
              random.random() * 6.28) for _ in range(170)]
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (10, 4, 26, 255))
        d = ImageDraw.Draw(img)
        cx, cy = W // 2, int(H * 0.42)
        for arm in range(3):
            for k in range(60):
                r = 30 + k * 9
                ang = arm * 2.094 + k * 0.16 + t * 0.9
                x = cx + r * math.cos(ang)
                y = cy + r * math.sin(ang) * 0.62
                a = max(0, 190 - k * 2)
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(190, 120, 255, a))
        for r, a in [(110, 120), (60, 220)]:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 230, 255, a))
        for sx, sy, ss, ph in stars:
            al = int(90 + 120 * math.sin(t * 2 + ph))
            d.ellipse([sx, sy, sx + ss, sy + ss], fill=(255, 255, 255, max(20, al)))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("galaxy ok")


def generate_aurora_night(duration=5.0, filename="18_aurora_night_sky.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    random.seed(18)
    stars = [(random.random() * W, random.random() * H * 0.8, random.uniform(1, 3)) for _ in range(120)]
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (2, 8, 18, 255))
        d = ImageDraw.Draw(img)
        for sx, sy, ss in stars:
            d.ellipse([sx, sy, sx + ss, sy + ss], fill=(255, 255, 255, 170))
        for band, (cr, cg, cb) in enumerate(((30, 255, 160), (80, 190, 255), (170, 120, 255))):
            pts = []
            for x in range(0, W + 24, 24):
                y = int(H * (0.22 + band * 0.09)
                        + 70 * math.sin(x / 190 + t * (1.4 + band * 0.4) + band * 2)
                        + 30 * math.sin(x / 77 - t * 2 + band))
                pts.append((x, y))
            for x, y in list(reversed(pts)):
                pts.append((x, y + 130 + band * 40))
            d.polygon(pts, fill=(cr, cg, cb, 44))
        base = int(H * 0.82)
        pts = [(0, H)] + [(x, base + int(24 * math.sin(x / 210))) for x in range(0, W + 20, 20)] + [(W, H)]
        d.polygon(pts, fill=(6, 14, 24, 255))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("aurora ok")


def generate_bronze_gears(duration=5.0, filename="19_bronze_gears_machine.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)

    def gear(d, cx, cy, r_out, r_in, teeth, ang, col):
        pts = []
        steps = teeth * 2
        for k in range(steps):
            r = r_out if k % 2 == 0 else r_out * 0.78
            a = ang + k * 6.283 / steps
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=col)
        d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(18, 10, 4, 255))

    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (20, 12, 6, 255))
        d = ImageDraw.Draw(img)
        gear(d, int(W * 0.32), int(H * 0.30), 250, 70, 12, t * 0.9, (200, 130, 50, 255))
        gear(d, int(W * 0.72), int(H * 0.52), 190, 54, 10, -t * 1.2, (170, 108, 44, 255))
        gear(d, int(W * 0.38), int(H * 0.74), 150, 42, 9, t * 1.6, (226, 160, 70, 255))
        for _ in range(24):
            x = random.randint(0, W)
            y = random.randint(0, H)
            d.ellipse([x, y, x + 2, y + 2], fill=(255, 200, 120, 60))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("gears ok")


def generate_white_reveal(duration=5.0, filename="20_white_light_reveal.mp4"):
    out = FOOTAGE_DIR / filename
    proc = _pipe(out)
    n = int(duration * FPS)
    for f in range(n):
        t = f / FPS
        img = Image.new("RGBA", (W, H), (8, 8, 12, 255))
        d = ImageDraw.Draw(img)
        cx, cy = W // 2, int(H * 0.42)
        for ang in range(0, 360, 12):
            rad = math.radians(ang) + t * 0.5
            r1 = 140 + 30 * math.sin(t * 3 + ang)
            r2 = r1 + 300 + 130 * math.sin(t * 1.6 + ang * 0.2)
            d.line([(cx + r1 * math.cos(rad), cy + r1 * math.sin(rad)),
                    (cx + r2 * math.cos(rad), cy + r2 * math.sin(rad))],
                   fill=(235, 240, 255, 46), width=4)
        for r, a in [(260, 40), (190, 70), (120, 130), (60, 250)]:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 248, 255, a))
        proc.stdin.write(np.array(img).tobytes())
    _finish(proc)
    print("reveal ok")


if __name__ == "__main__":
    FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)
    generate_ocean_waves()
    generate_desert_dunes()
    generate_gold_rain()
    generate_green_energy()
    generate_lava_embers()
    generate_city_nights()
    generate_red_alert()
    generate_galaxy_swirl()
    generate_aurora_night()
    generate_bronze_gears()
    generate_white_reveal()
    print("11 VAULT CLIPS DONE")
