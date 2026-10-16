#!/usr/bin/env bash
# 🎬 جهّز أدوات الرندر المحلية (ffmpeg + ffprobe) — للساندبوكس بس.
#
# ليه الملف ده موجود؟
#   بيئة الشغل المحلية بتفقد الأدوات المثبّتة بين الجلسات (مجلدات .local
#   و.cache مستثناة من اللقطات). فبدل ما نشتغل بالإيد كل مرة، السكربت ده
#   بينزّل ffmpeg في **/tmp/bin** (بره المستودع، مش بيتلخم على git) وبيضيفه
#   للـPATH. وفي نفس الوقت بيعمل بديل مبسّط لـffprobe، لأن نسخة imageio
#   مش معاها ffprobe.
#
#   ⚠️ الملف ده **أداة تطوير محلية**. المصنع على GitHub Actions بيستخدم
#   ffmpeg الحقيقي من apt، ومش بيعتمد على أي حاجة هنا. صفر تأثير على الإنتاج.
#
# الاستخدام:  source tools/local_media_tools.sh
set -u

BIN=/tmp/bin
mkdir -p "$BIN"

if [ ! -x "$BIN/ffmpeg" ]; then
  echo "⏳ بننزّل ffmpeg…"
  python3 -m pip download --quiet --no-deps --dest /tmp/ffdl imageio-ffmpeg >/dev/null 2>&1 || true
  python3 - <<'PY'
import glob, shutil, zipfile, os
whl = glob.glob("/tmp/ffdl/*.whl")
if not whl:
    raise SystemExit("⚠️ مش قادر أنزّل imageio-ffmpeg")
z = zipfile.ZipFile(whl[0])
cand = [n for n in z.namelist()
        if n.startswith("imageio_ffmpeg/binaries/") and "linux" in n]
if not cand:
    raise SystemExit("⚠️ مش لاقي باينري ffmpeg في الحزمة")
z.extract(cand[0], "/tmp/_ffx")
src = f"/tmp/_ffx/{cand[0]}"
shutil.copy(src, "/tmp/bin/ffmpeg")
os.chmod("/tmp/bin/ffmpeg", 0o755)
shutil.rmtree("/tmp/_ffx", ignore_errors=True)
print("✅ ffmpeg جاهز")
PY
fi

# بديل ffprobe: imageio-ffmpeg معاه ffmpeg بس (مفيش ffprobe).
# المصنع بينادي ffprobe في ٣ أماكن (المدة/الأصوات/الفحص)، فبنوفّر بديل
# بيقرأ نفس المعلومات من مخرجات ffmpeg.
if [ ! -x "$BIN/ffprobe" ]; then
  cat > "$BIN/ffprobe" <<'PYEOF'
#!/usr/bin/env python3
"""بديل مبسّط لـffprobe للساندبوكس — imageio-ffmpeg معاه ffmpeg بس."""
import re, subprocess, sys

FFMPEG = "/tmp/bin/ffmpeg"


def probe(path):
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)],
                       capture_output=True, text=True)
    txt = r.stderr or ""
    out = {"format": {}, "streams": []}
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", txt)
    if m:
        h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        out["format"]["duration"] = f"{h * 3600 + mi * 60 + s:.6f}"
    m = re.search(r"bitrate:\s*(\d+)\s*kb/s", txt)
    if m:
        out["format"]["bit_rate"] = str(int(m.group(1)) * 1000)
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("Stream #"):
            continue
        st = {}
        kind = ("audio" if " Audio: " in line
                else ("video" if " Video: " in line else ""))
        st["codec_type"] = kind
        if kind == "video":
            m = re.search(r"(\d{2,5})x(\d{2,5})", line)
            if m:
                st["width"], st["height"] = m.group(1), m.group(2)
            m = re.search(r"(\d+(?:\.\d+)?)\s*fps", line)
            if m:
                st["r_frame_rate"] = m.group(1)
        if kind == "audio":
            m = re.search(r"(\d+)\s*Hz", line)
            if m:
                st["sample_rate"] = m.group(1)
            st["channels"] = "1" if "mono" in line else "2"
            m = re.search(r"Audio:\s*(\w+)", line)
            if m:
                st["codec_name"] = m.group(1)
        out["streams"].append(st)
    return out


def main():
    args = sys.argv[1:]
    show, sel, csv, path = "", "", False, ""
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-show_entries":
            show = args[i + 1]; i += 2; continue
        if a == "-select_streams":
            sel = args[i + 1]; i += 2; continue
        if a == "-of":
            csv = "csv" in args[i + 1]; i += 2; continue
        if a in ("-v", "-loglevel"):
            i += 2; continue
        if not a.startswith("-"):
            path = a
        i += 1
    if not path:
        return 1
    d = probe(path)
    streams = d["streams"]
    if sel.startswith("a"):
        streams = [s for s in streams if s.get("codec_type") == "audio"]
    if "format=duration" in show:
        print(d["format"].get("duration", "0")); return 0
    if "format=bit_rate" in show:
        print(d["format"].get("bit_rate", "0")); return 0
    keys = []
    m = re.search(r"stream=([\w,:]+)", show)
    if m:
        keys = m.group(1).split(",")
    for s in streams:
        vals = [s.get(k, "N/A") for k in keys] if keys else [s.get("codec_type", "N/A")]
        print(",".join(vals) if csv else "\n".join(vals))
    return 0


if __name__ == "__main__":
    sys.exit(main())
PYEOF
  chmod +x "$BIN/ffprobe"
fi

export PATH="$BIN:$PATH"
echo "🎬 أدوات الرندر جاهزة: $(command -v ffmpeg) · $(command -v ffprobe)"
