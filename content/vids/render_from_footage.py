"""
Assemble the MrBeast Viral Video entirely from REAL MOTION FOOTAGE CLIPS.
Zero static slideshow — 100% fluid, dynamic, multi-layered video action.
"""

import subprocess
import os
import shutil

ROOT_DIR = "/home/user/youtube"
FOOTAGE_DIR = os.path.join(ROOT_DIR, "assets", "footage")
BUILD_DIR = "/tmp/footage_assembly"
AUDIO_MIX = os.path.join(ROOT_DIR, "content", "audio", "mrbeast_final_mix.m4a")
SUBTITLES = os.path.join(ROOT_DIR, "content", "vids", "mrbeast_challenge.ass")
FINAL_OUT = os.path.join(ROOT_DIR, "content", "vids", "mrbeast_challenge.mp4")

if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)
os.makedirs(BUILD_DIR, exist_ok=True)

# Scene shot breakdown (total = 41.12s):
shots = [
    {
        "id": "shot0_fire_hook",
        "footage": os.path.join(FOOTAGE_DIR, "01_fire_hook_motion.mp4"),
        "dur": 7.5,
        "desc": "Fire hook screaming action with heat wave and embers"
    },
    {
        "id": "shot1_cash_rain",
        "footage": os.path.join(FOOTAGE_DIR, "02_cash_rain_motion.mp4"),
        "dur": 6.0,
        "desc": "Cash mountain with 3D raining bills"
    },
    {
        "id": "shot2_cash_struggle",
        "footage": os.path.join(FOOTAGE_DIR, "06_cash_struggle_close.mp4"),
        "dur": 3.0,
        "desc": "Close-up hands trembling on cash with security laser"
    },
    {
        "id": "shot3_blizzard",
        "footage": os.path.join(FOOTAGE_DIR, "03_blizzard_freeze_motion.mp4"),
        "dur": 10.0,
        "desc": "Arctic blizzard with gale-force swirling snow"
    },
    {
        "id": "shot4_countdown",
        "footage": os.path.join(FOOTAGE_DIR, "04_countdown_hud_motion.mp4"),
        "dur": 7.5,
        "desc": "Digital countdown HUD with flashing red emergency siren"
    },
    {
        "id": "shot5_confetti",
        "footage": os.path.join(FOOTAGE_DIR, "05_confetti_winner_motion.mp4"),
        "dur": 7.12,
        "desc": "Confetti cannon explosion and victory trophy celebration"
    }
]

rendered_shots = []

for idx, shot in enumerate(shots):
    out_clip = os.path.join(BUILD_DIR, f"shot_{idx}.mp4")
    dur = shot["dur"]
    src = shot["footage"]
    print(f"Preparing shot {idx}: {shot['id']} ({dur}s) from {os.path.basename(src)}...")
    
    # Loop source if needed, scale to 1080x1920@30fps
    cmd = [
        "/usr/local/bin/ffmpeg", "-y",
        "-stream_loop", "3",
        "-i", src,
        "-t", f"{dur:.2f}",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        out_clip
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error preparing shot {idx}:", res.stderr)
        exit(1)
    rendered_shots.append(out_clip)

# Concat all shots
concat_list_file = os.path.join(BUILD_DIR, "concat_list.txt")
with open(concat_list_file, "w") as f:
    for c in rendered_shots:
        f.write(f"file '{c}'\n")

base_merged = os.path.join(BUILD_DIR, "footage_merged.mp4")
print("Concatenating all real motion shots...")
cmd_concat = [
    "/usr/local/bin/ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_list_file,
    "-c", "copy",
    base_merged
]
subprocess.run(cmd_concat, check=True)

# Burn ASS subtitles and mix audio
print("Burning kinetic subtitles and mastering final audio track...")
cmd_final = [
    "/usr/local/bin/ffmpeg", "-y",
    "-i", base_merged,
    "-i", AUDIO_MIX,
    "-vf", f"ass={SUBTITLES}:fontsdir={ROOT_DIR}/assets/fonts",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
    "-c:a", "aac", "-b:a", "192k",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    "-shortest",
    FINAL_OUT
]
subprocess.run(cmd_final, check=True)

print(f"SUCCESS! Rendered full motion viral video at: {FINAL_OUT}")
print(f"File size: {os.path.getsize(FINAL_OUT) / (1024*1024):.2f} MB")
