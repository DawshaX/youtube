"""
CosmicTube Stock Footage & B-Roll Vault Generator
Generates high-definition (1080x1920 @ 30fps) dynamic motion video clips
for viral challenge production (MrBeast tier).
"""

import os
import math
import random
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

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

# -------------------------------------------------------------
# 1. Fire Hook Motion Clip (Roaring fire, heat waves, floating embers)
# -------------------------------------------------------------
def generate_fire_clip(duration=5.0, filename="01_fire_hook_motion.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    # Base background: read sc0_fire_hook.jpg
    base_img = Image.open("/home/user/youtube/assets/visuals/sc0_fire_hook.jpg").convert("RGB").resize((W, H))
    base_arr = np.array(base_img, dtype=np.float32)

    # Particle embers
    random.seed(101)
    embers = []
    for _ in range(80):
        embers.append({
            "x": random.uniform(100, W - 100),
            "y": random.uniform(H * 0.3, H),
            "vy": random.uniform(250, 600),
            "vx": random.uniform(-60, 60),
            "radius": random.uniform(3, 10),
            "color": random.choice([(255, 100, 20), (255, 180, 40), (255, 230, 80), (255, 50, 10)]),
            "alpha": random.uniform(180, 255),
            "flicker": random.uniform(5, 15)
        })

    for f in range(total_frames):
        t = f / FPS
        dt = 1.0 / FPS

        # Dynamic heat-wave warp & camera shake
        shake_x = math.sin(t * 24) * 8 + math.cos(t * 37) * 4
        shake_y = math.cos(t * 28) * 8 + math.sin(t * 43) * 4
        zoom = 1.0 + 0.08 * (f / total_frames) # progressive zoom-in

        # Pulse brightness for fire glow
        glow_pulse = 1.0 + 0.15 * math.sin(t * 12) + 0.08 * math.cos(t * 19)
        cur_arr = np.clip(base_arr * glow_pulse, 0, 255).astype(np.uint8)
        frame_img = Image.fromarray(cur_arr).convert("RGBA")

        # Apply zoom & shake
        cw, ch = int(W / zoom), int(H / zoom)
        cx = int((W - cw)/2 + shake_x)
        cy = int((H - ch)/2 + shake_y)
        cx = max(0, min(W - cw, cx))
        cy = max(0, min(H - ch, cy))
        cropped = frame_img.crop((cx, cy, cx + cw, cy + ch)).resize((W, H), Image.BILINEAR)

        draw = ImageDraw.Draw(cropped)

        # Draw flame tongues at the bottom & sides
        flame_points = []
        for fx in range(0, W + 40, 40):
            fy = H - 80 - math.sin(fx * 0.03 + t * 14) * 120 - math.cos(fx * 0.08 - t * 20) * 60
            flame_points.append((fx, fy))
        flame_points.append((W, H))
        flame_points.append((0, H))
        draw.polygon(flame_points, fill=(255, 90, 10, 110))

        # Update & draw glowing embers
        for eb in embers:
            eb["y"] -= eb["vy"] * dt
            eb["x"] += (eb["vx"] + math.sin(t * 8 + eb["y"] * 0.01) * 80) * dt
            if eb["y"] < 0:
                eb["y"] = H + random.uniform(0, 100)
                eb["x"] = random.uniform(50, W - 50)

            r = eb["radius"] * (0.8 + 0.4 * math.sin(t * eb["flicker"]))
            alp = int(eb["alpha"] * (0.6 + 0.4 * math.cos(t * eb["flicker"])))
            col = eb["color"] + (alp,)
            draw.ellipse([eb["x"] - r, eb["y"] - r, eb["x"] + r, eb["y"] + r], fill=col)

        # Emergency red flash vignette every 1.5s
        if math.sin(t * math.pi * 1.5) > 0.7:
            draw.rectangle([0, 0, W, 40], fill=(255, 0, 0, 160))
            draw.rectangle([0, H - 40, W, H], fill=(255, 0, 0, 160))

        proc.stdin.write(cropped.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")


# -------------------------------------------------------------
# 2. Money Rain Motion Clip (3D falling tumbling cash bills)
# -------------------------------------------------------------
def generate_money_rain_clip(duration=6.0, filename="02_cash_rain_motion.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    base_img = Image.open("/home/user/youtube/assets/visuals/sc1_cash_hands.jpg").convert("RGB").resize((W, H))

    random.seed(202)
    bills = []
    for _ in range(65):
        bills.append({
            "x": random.uniform(30, W - 30),
            "y": random.uniform(-H, H),
            "vy": random.uniform(450, 950),
            "vx": random.uniform(-90, 90),
            "w": random.uniform(90, 160),
            "h": random.uniform(45, 80),
            "angle": random.uniform(0, 360),
            "v_angle": random.uniform(-200, 200),
            "flip": random.uniform(0, 360),
            "v_flip": random.uniform(150, 350),
            "z": random.uniform(0.6, 1.4)
        })

    for f in range(total_frames):
        t = f / FPS
        dt = 1.0 / FPS

        # Camera subtle pan & zoom
        zoom = 1.0 + 0.05 * math.sin(t * 1.5)
        cw, ch = int(W / zoom), int(H / zoom)
        pan_y = int(math.sin(t * 2) * 20)
        cropped_bg = base_img.crop((0, max(0, pan_y), cw, min(H, pan_y + ch))).resize((W, H), Image.BILINEAR).convert("RGBA")

        draw = ImageDraw.Draw(cropped_bg)

        # Draw green security laser scanning line
        laser_y = int((t * 500) % H)
        draw.line([(0, laser_y), (W, laser_y)], fill=(0, 255, 120, 220), width=4)
        draw.line([(0, laser_y - 2), (W, laser_y - 2)], fill=(180, 255, 200, 160), width=2)
        draw.line([(0, laser_y + 2), (W, laser_y + 2)], fill=(180, 255, 200, 160), width=2)

        # Draw bills sorted by z (depth)
        for b in sorted(bills, key=lambda x: x["z"]):
            b["y"] += b["vy"] * dt * b["z"]
            b["x"] += b["vx"] * dt + math.sin(t * 4 + b["angle"] * 0.02) * 50 * dt
            b["angle"] += b["v_angle"] * dt
            b["flip"] += b["v_flip"] * dt
            if b["y"] > H + 120:
                b["y"] = -random.uniform(50, 200)
                b["x"] = random.uniform(30, W - 30)

            scale_y = max(0.08, abs(math.cos(math.radians(b["flip"]))))
            bw = int(b["w"] * b["z"])
            bh = int(max(6, b["h"] * scale_y * b["z"]))

            bill_canvas = Image.new("RGBA", (int(bw * 1.4) + 10, int(bh * 1.4) + 10), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(bill_canvas)
            cx, cy = bill_canvas.width / 2, bill_canvas.height / 2

            # Green gradient cash border
            rect = [cx - bw/2, cy - bh/2, cx + bw/2, cy + bh/2]
            fill_col = (28, 115, 55, int(240 * min(1.0, b["z"])))
            bdraw.rectangle(rect, fill=fill_col, outline=(220, 255, 220, 255), width=2)

            # 100$ watermark
            if bh > 22 and bw > 60:
                bdraw.text((cx - 16, cy - 10), "$100", fill=(255, 255, 255, 240))
                bdraw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=(180, 240, 180, 200), width=1)

            rot = bill_canvas.rotate(b["angle"], resample=Image.BILINEAR, expand=True)
            cropped_bg.paste(rot, (int(b["x"] - rot.width/2), int(b["y"] - rot.height/2)), rot)

        proc.stdin.write(cropped_bg.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")


# -------------------------------------------------------------
# 3. Ice Blizzard Freeze Motion Clip (Swirling snow, ice gale, frost)
# -------------------------------------------------------------
def generate_blizzard_clip(duration=6.0, filename="03_blizzard_freeze_motion.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    base_img = Image.open("/home/user/youtube/assets/visuals/sc2_ice_blizzard.jpg").convert("RGB").resize((W, H))

    random.seed(303)
    snowflakes = []
    for _ in range(120):
        snowflakes.append({
            "x": random.uniform(0, W),
            "y": random.uniform(-100, H),
            "vx": random.uniform(-500, -150), # gale wind blowing left
            "vy": random.uniform(300, 700),
            "r": random.uniform(2, 8),
            "alpha": random.uniform(160, 255),
            "streak": random.uniform(8, 28)
        })

    for f in range(total_frames):
        t = f / FPS
        dt = 1.0 / FPS

        # Wind gusts & vibration
        wind_gust = math.sin(t * 15) * 12 + math.cos(t * 22) * 6
        zoom = 1.02 + 0.04 * math.sin(t * 3)

        cw, ch = int(W / zoom), int(H / zoom)
        cx = max(0, min(W - cw, int((W - cw)/2 + wind_gust)))
        cy = max(0, min(H - ch, int((H - ch)/2)))
        bg_frame = base_img.crop((cx, cy, cx + cw, cy + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")

        draw = ImageDraw.Draw(bg_frame)

        # Cold blue vignette tint
        vignette_alpha = int(40 + 20 * math.sin(t * 4))
        draw.rectangle([0, 0, W, H], fill=(0, 60, 140, vignette_alpha))

        # Swirling snowflakes with motion streaks
        for s in snowflakes:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            if s["x"] < -50 or s["y"] > H + 50:
                s["x"] = random.uniform(W * 0.5, W + 100)
                s["y"] = random.uniform(-50, H * 0.5)

            # Draw snow streak in direction of wind
            x1, y1 = s["x"], s["y"]
            x2 = x1 + s["streak"] * (s["vx"] / 400.0)
            y2 = y1 + s["streak"] * (s["vy"] / 400.0)
            col = (235, 245, 255, int(s["alpha"]))
            draw.line([(x1, y1), (x2, y2)], fill=col, width=int(s["r"]))
            draw.ellipse([x1 - s["r"]/2, y1 - s["r"]/2, x1 + s["r"]/2, y1 + s["r"]/2], fill=col)

        # Frost border on camera edges
        draw.rectangle([0, 0, W, 25], fill=(200, 230, 255, 90))
        draw.rectangle([0, H - 25, W, H], fill=(200, 230, 255, 90))
        draw.rectangle([0, 0, 25, H], fill=(200, 230, 255, 90))
        draw.rectangle([W - 25, 0, W, H], fill=(200, 230, 255, 90))

        proc.stdin.write(bg_frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")


# -------------------------------------------------------------
# 4. Countdown Alarm HUD Motion Clip (Running timer, siren beams, glitch)
# -------------------------------------------------------------
def generate_countdown_clip(duration=5.0, filename="04_countdown_hud_motion.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    base_img = Image.open("/home/user/youtube/assets/visuals/sc3_countdown.jpg").convert("RGB").resize((W, H))

    for f in range(total_frames):
        t = f / FPS
        # Timer counting down from 00:04:99 to 00:00:01
        remaining_secs = max(0.01, duration - t)
        mins = int(remaining_secs // 60)
        secs = int(remaining_secs % 60)
        millis = int((remaining_secs * 100) % 100)
        timer_text = f"{mins:02d}:{secs:02d}:{millis:02d}"

        # Emergency red strobe flash
        strobe = math.sin(t * 18) > 0.0
        bg_frame = base_img.copy().convert("RGBA")
        draw = ImageDraw.Draw(bg_frame)

        if strobe:
            draw.rectangle([0, 0, W, H], fill=(255, 20, 20, 60))

        # HUD Circular Radar Scanner in Center
        cx, cy = W // 2, int(H * 0.45)
        radar_radius = 240
        angle = (t * 360 * 1.5) % 360
        rad = math.radians(angle)
        lx = cx + radar_radius * math.cos(rad)
        ly = cy + radar_radius * math.sin(rad)
        draw.ellipse([cx - radar_radius, cy - radar_radius, cx + radar_radius, cy + radar_radius],
                     outline=(255, 50, 50, 180), width=4)
        draw.line([(cx, cy), (lx, ly)], fill=(255, 100, 100, 255), width=3)

        # Danger stripes at top and bottom
        stripe_offset = int((t * 150) % 80)
        for sx in range(-80, W + 80, 80):
            xpos = sx + stripe_offset
            draw.polygon([(xpos, 0), (xpos + 40, 0), (xpos + 20, 50), (xpos - 20, 50)], fill=(255, 200, 0, 180))
            draw.polygon([(xpos, H - 50), (xpos + 40, H - 50), (xpos + 20, H), (xpos - 20, H)], fill=(255, 200, 0, 180))

        # Digital Timer Display Box
        box_w, box_h = 600, 140
        bx1, by1 = (W - box_w)//2, cy + 300
        draw.rectangle([bx1, by1, bx1 + box_w, by1 + box_h], fill=(10, 10, 15, 230), outline=(255, 40, 40, 255), width=4)
        draw.text((bx1 + 75, by1 + 25), timer_text, fill=(255, 230, 50, 255), font=None)
        # Big text simulated by drawing outline
        draw.text((bx1 + 180, by1 + 85), "CRITICAL ELIMINATION", fill=(255, 80, 80, 240))

        # Horizontal glitch scanline
        glitch_y = int((t * 900) % H)
        draw.line([(0, glitch_y), (W, glitch_y)], fill=(255, 255, 255, 200), width=2)

        proc.stdin.write(bg_frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")


# -------------------------------------------------------------
# 5. Confetti Winner Motion Clip (3D slow-motion confetti explosion)
# -------------------------------------------------------------
def generate_confetti_clip(duration=5.0, filename="05_confetti_winner_motion.mp4"):
    out_path = os.path.join(FOOTAGE_DIR, filename)
    print(f"Generating {filename} ({duration}s)...")
    proc = create_video_pipe(out_path, FPS)
    total_frames = int(duration * FPS)

    base_img = Image.open("/home/user/youtube/assets/visuals/sc4_winner_trophy.jpg").convert("RGB").resize((W, H))

    random.seed(404)
    confetti_pieces = []
    colors = [
        (255, 215, 0), # gold
        (255, 40, 80),  # vibrant magenta
        (40, 220, 255), # bright cyan
        (255, 255, 255),# sparkling white
        (50, 255, 120), # emerald green
        (255, 140, 0)   # electric orange
    ]
    for _ in range(120):
        confetti_pieces.append({
            "x": random.uniform(50, W - 50),
            "y": random.uniform(-400, H * 0.8),
            "vy": random.uniform(280, 650),
            "vx": random.uniform(-100, 100),
            "w": random.uniform(20, 45),
            "h": random.uniform(10, 22),
            "color": random.choice(colors),
            "angle": random.uniform(0, 360),
            "v_angle": random.uniform(-300, 300),
            "flip": random.uniform(0, 360),
            "v_flip": random.uniform(180, 420)
        })

    for f in range(total_frames):
        t = f / FPS
        dt = 1.0 / FPS

        # Celebratory pulsating camera zoom
        zoom = 1.0 + 0.06 * math.sin(t * 3.5)
        cw, ch = int(W / zoom), int(H / zoom)
        cx = max(0, min(W - cw, int((W - cw)/2)))
        cy = max(0, min(H - ch, int((H - ch)/2)))
        frame = base_img.crop((cx, cy, cx + cw, cy + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")

        draw = ImageDraw.Draw(frame)

        # Golden shimmer light rays from top center
        ray_alpha = int(45 + 25 * math.sin(t * 6))
        for ra in range(-60, 61, 20):
            rad = math.radians(ra + 90)
            rx = W // 2 + 1200 * math.cos(rad)
            ry = 1200 * math.sin(rad)
            draw.line([(W // 2, 0), (rx, ry)], fill=(255, 230, 120, ray_alpha), width=18)

        # Draw 3D fluttering confetti
        for c in confetti_pieces:
            c["y"] += c["vy"] * dt
            c["x"] += c["vx"] * dt + math.sin(t * 5 + c["angle"] * 0.05) * 60 * dt
            c["angle"] += c["v_angle"] * dt
            c["flip"] += c["v_flip"] * dt
            if c["y"] > H + 50:
                c["y"] = -random.uniform(20, 150)
                c["x"] = random.uniform(50, W - 50)

            scale_y = max(0.1, abs(math.cos(math.radians(c["flip"]))))
            cw_cur = c["w"]
            ch_cur = max(4, c["h"] * scale_y)

            conf_canvas = Image.new("RGBA", (int(cw_cur * 1.5) + 6, int(ch_cur * 1.5) + 6), (0, 0, 0, 0))
            cdraw = ImageDraw.Draw(conf_canvas)
            ccx, ccy = conf_canvas.width / 2, conf_canvas.height / 2
            crect = [ccx - cw_cur/2, ccy - ch_cur/2, ccx + cw_cur/2, ccy + ch_cur/2]
            cdraw.rectangle(crect, fill=c["color"] + (240,))

            rot = conf_canvas.rotate(c["angle"], resample=Image.BILINEAR, expand=True)
            frame.paste(rot, (int(c["x"] - rot.width/2), int(c["y"] - rot.height/2)), rot)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    generate_fire_clip(5.0)
    generate_money_rain_clip(6.0)
    generate_blizzard_clip(6.0)
    generate_countdown_clip(5.0)
    generate_confetti_clip(5.0)
    print("ALL FOOTAGE VAULT CLIPS GENERATED SUCCESSFULLY!")
