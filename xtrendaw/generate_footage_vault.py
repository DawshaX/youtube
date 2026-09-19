"""
Factory Stock Footage & B-Roll Vault Engine
Generates high-definition (1080x1920 @ 30fps) dynamic motion video clips
for viral challenge & science production (MrBeast & Kurzgesagt tier).
Includes dynamic on-demand generation for any query/theme.
"""

import os
import math
import random
import subprocess
import numpy as np
from PIL import Image, ImageDraw

FOOTAGE_DIR = "/home/user/youtube/assets/footage"
os.makedirs(FOOTAGE_DIR, exist_ok=True)

W, H, FPS = 1080, 1920, 30

def create_video_pipe(output_path, fps=30):
    cmd = [
        "/usr/local/bin/ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def generate_space_warp_clip(duration=5.0, filename="07_space_warp_cosmic.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    random.seed(505)
    stars = []
    for _ in range(250):
        stars.append({
            "angle": random.uniform(0, 2 * math.pi),
            "dist": random.uniform(20, W * 0.7),
            "speed": random.uniform(250, 750),
            "size": random.uniform(2, 6),
            "color": random.choice([(255, 255, 255), (180, 220, 255), (255, 180, 240), (100, 255, 220)])
        })

    for f in range(total_frames):
        t = f / FPS
        dt = 1.0 / FPS

        frame = Image.new("RGBA", (W, H), (6, 8, 20, 255))
        draw = ImageDraw.Draw(frame)

        # Center swirling nebula glow
        cx, cy = W // 2, H // 2
        nebula_rad = 320 + 40 * math.sin(t * 3)
        draw.ellipse([cx - nebula_rad, cy - nebula_rad, cx + nebula_rad, cy + nebula_rad],
                     fill=(80, 20, 140, 50))
        draw.ellipse([cx - nebula_rad*0.5, cy - nebula_rad*0.5, cx + nebula_rad*0.5, cy + nebula_rad*0.5],
                     fill=(30, 80, 200, 60))

        # Star streaks radiating outwards (hyperspace warp effect)
        for s in stars:
            s["dist"] += s["speed"] * dt
            if s["dist"] > W * 0.8:
                s["dist"] = random.uniform(10, 80)
                s["angle"] = random.uniform(0, 2 * math.pi)

            rad = s["angle"] + t * 0.2
            x2 = cx + s["dist"] * math.cos(rad)
            y2 = cy + s["dist"] * math.sin(rad)
            streak_len = min(60, s["dist"] * 0.15)
            x1 = cx + (s["dist"] - streak_len) * math.cos(rad)
            y1 = cy + (s["dist"] - streak_len) * math.sin(rad)

            col = s["color"] + (255,)
            draw.line([(x1, y1), (x2, y2)], fill=col, width=int(s["size"]))

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path}")
    return out_path


def generate_neon_cyber_clip(duration=5.0, filename="08_neon_cyber_grid.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    for f in range(total_frames):
        t = f / FPS
        frame = Image.new("RGBA", (W, H), (10, 10, 18, 255))
        draw = ImageDraw.Draw(frame)

        # 3D Synthwave perspective grid at bottom
        horizon_y = int(H * 0.55)
        draw.line([(0, horizon_y), (W, horizon_y)], fill=(255, 0, 128, 220), width=4)

        # Vertical vanishing perspective lines
        for vx in range(-W, 2 * W, 80):
            draw.line([(W // 2, horizon_y), (vx, H)], fill=(0, 255, 230, 140), width=2)

        # Horizontal scrolling grid lines
        grid_offset = (t * 200) % 60
        for gy in range(0, int(H - horizon_y), 50):
            cur_y = horizon_y + int(math.pow(gy / (H - horizon_y), 2) * (H - horizon_y)) + int(grid_offset)
            if horizon_y < cur_y < H:
                draw.line([(0, cur_y), (W, cur_y)], fill=(255, 0, 128, 120), width=2)

        # Pulsing Cyber Sun / HUD ring
        sun_y = int(horizon_y - 220)
        sun_r = 160 + 10 * math.sin(t * 6)
        draw.ellipse([W // 2 - sun_r, sun_y - sun_r, W // 2 + sun_r, sun_y + sun_r],
                     outline=(255, 200, 0, 240), width=6)
        for i in range(5):
            cut_y = sun_y + (i - 2) * 25
            draw.line([(W // 2 - sun_r, cut_y), (W // 2 + sun_r, cut_y)], fill=(10, 10, 18, 255), width=8)

        # Scanlines
        scan_y = int((t * 800) % H)
        draw.line([(0, scan_y), (W, scan_y)], fill=(0, 255, 230, 180), width=3)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path}")
    return out_path


def generate_lightning_storm_clip(duration=5.0, filename="09_lightning_storm_danger.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    for f in range(total_frames):
        t = f / FPS
        # Lightning strobe flashes at intervals
        flash = (int(t * 10) % 23 in (2, 3, 14, 15))
        bg_col = (180, 210, 255, 255) if flash else (12, 14, 25, 255)
        frame = Image.new("RGBA", (W, H), bg_col)
        draw = ImageDraw.Draw(frame)

        if flash:
            # Jagged lightning bolt
            lx = W // 2 + int(math.sin(t * 20) * 150)
            points = [(lx, 0)]
            cur_x, cur_y = lx, 0
            while cur_y < H * 0.85:
                cur_y += random.randint(40, 100)
                cur_x += random.randint(-60, 60)
                points.append((cur_x, cur_y))
            draw.line(points, fill=(255, 255, 255, 255), width=6)
            draw.line(points, fill=(160, 220, 255, 200), width=14)

        # Heavy rain streaks
        for rx in range(0, W, 25):
            ry = int((rx * 17 + t * 1400) % H)
            draw.line([(rx, ry), (rx - 15, ry + 40)], fill=(140, 180, 230, 140), width=2)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path}")
    return out_path


def generate_clip_on_demand(query, duration=5.0):
    """Dynamically route any query or topic to the most fitting cinema motion generator."""
    q = (query or "").lower().strip()
    clean_id = "".join(c for c in q if c.isalnum() or c in ("_", "-"))[:20] or "custom"
    filename = f"clip_{clean_id}_{int(duration)}s.mp4"
    out_path = os.path.join(FOOTAGE_DIR, filename)

    if os.path.exists(out_path):
        return filename

    if any(k in q for k in ["space", "star", "cosmic", "galaxy", "universe", "فضاء", "كون"]):
        generate_space_warp_clip(duration, filename)
    elif any(k in q for k in ["neon", "cyber", "tech", "grid", "matrix", "نيون", "تكنولوجيا"]):
        generate_neon_cyber_clip(duration, filename)
    elif any(k in q for k in ["storm", "lightning", "rain", "danger", "عاصفة", "برق", "رعد"]):
        generate_lightning_storm_clip(duration, filename)
    else:
        # Default high-impact cyber space motion
        generate_space_warp_clip(duration, filename)

    return filename


if __name__ == "__main__":
    generate_space_warp_clip()
    generate_neon_cyber_clip()
    generate_lightning_storm_clip()
    print("ALL 9 STOCK FOOTAGE CLIPS READY!")
