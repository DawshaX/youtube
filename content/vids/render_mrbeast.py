import subprocess
from pathlib import Path

ROOT = Path("/home/user/youtube")
VISUALS = ROOT / "assets/visuals"
AUDIO = ROOT / "content/audio/mrbeast_final_mix.m4a"
ASS = ROOT / "content/vids/mrbeast_challenge.ass"
OUT = ROOT / "content/vids/mrbeast_challenge.mp4"
TMP_DIR = Path("/tmp/mrbeast_build")
TMP_DIR.mkdir(parents=True, exist_ok=True)

scenes = [
    {"img": VISUALS / "sc0_fire_hook.jpg", "dur": 7.5, "zoom": "in"},
    {"img": VISUALS / "sc1_cash_hands.jpg", "dur": 8.5, "zoom": "out"},
    {"img": VISUALS / "sc2_ice_blizzard.jpg", "dur": 10.5, "zoom": "in"},
    {"img": VISUALS / "sc3_countdown.jpg", "dur": 7.5, "zoom": "pan_r"},
    {"img": VISUALS / "sc4_winner_trophy.jpg", "dur": 7.12, "zoom": "in"},
]

clips = []
for i, sc in enumerate(scenes):
    clip_path = TMP_DIR / f"clip_{i}.mp4"
    frames = int(sc["dur"] * 30)
    cx = "iw/2-(iw/zoom/2)"
    cy = "ih/2-(ih/zoom/2)"
    
    if sc["zoom"] == "in":
        zp = f"z='1.0+0.12*on/{frames}':x='{cx}':y='{cy}'"
    elif sc["zoom"] == "out":
        zp = f"z='1.12-0.12*on/{frames}':x='{cx}':y='{cy}'"
    else:
        zp = f"z='1.08':x='(iw-iw/zoom)*(0.15+0.70*on/{frames})':y='{cy}'"

    cmd = [
        "/usr/local/bin/ffmpeg", "-y",
        "-loop", "1", "-i", str(sc["img"]),
        "-filter_complex",
        f"[0:v]scale=1620:2880,eq=contrast=1.14:saturation=1.28:brightness=0.02,vignette=PI/5,unsharp=5:5:0.5,"
        f"zoompan={zp}:d={frames}:s=1080x1920:fps=30,fade=t=in:st=0:d=0.25:color=black,fade=t=out:st={sc['dur']-0.20:.2f}:d=0.20:color=black[v]",
        "-map", "[v]",
        "-t", f"{sc['dur']:.2f}",
        "-r", "30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-an", str(clip_path)
    ]
    print(f"Rendering scene {i} ({sc['dur']}s)...")
    subprocess.run(cmd, check=True)
    clips.append(clip_path)

# Concat list
concat_txt = TMP_DIR / "concat.txt"
with open(concat_txt, "w") as f:
    for c in clips:
        f.write(f"file '{c.resolve().as_posix()}'\n")

base_video = TMP_DIR / "base_merged.mp4"
subprocess.run([
    "/usr/local/bin/ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", str(concat_txt),
    "-c", "copy", str(base_video)
], check=True)

# Final burn of subtitles and audio mix
print("Burning kinetic ASS subtitles and mixing high-energy audio...")
subprocess.run([
    "/usr/local/bin/ffmpeg", "-y",
    "-i", str(base_video),
    "-i", str(AUDIO),
    "-filter_complex",
    f"[0:v]ass={ASS.resolve().as_posix()}:fontsdir={ROOT}/assets/fonts[v]",
    "-map", "[v]", "-map", "1:a",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k",
    "-t", "41.12", "-movflags", "+faststart",
    str(OUT)
], check=True)

print(f"DONE! Video saved at: {OUT}")
