"""🎥 الفيديوهات الطويلة — حلقات مجمّعة (محرّك ساعات المشاهدة).

ليه؟ يوتيوب بيكافئ وقت المشاهدة، والفيديو الطويل بيفتح «شاهد التالي» واقتراحات.
الطرق:
  • سورة كاملة (موجودة أصلًا في noor_build.build_long_surah)
  • **حلقة قصص**: كذا قصة متتابعة (~٦–٩ دقايق) — دي الجديدة هنا.
كل مقطع بيترندر بمحرّك نور السينمائي وبعدين بيتجمعوا بسلاسة (concat).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import settings
from .tts import ffmpeg


def _dur(path: Path) -> float:
    r = subprocess.run([ffmpeg(), "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    import re
    m = re.findall(r"time=(\d+):(\d+):([\d.]+)", r.stderr or "")
    if not m:
        return 0.0
    h, mi, s = m[-1]
    return int(h) * 3600 + int(mi) * 60 + float(s)


def build_long_series(items: list[dict], workdir: Path,
                      max_items: int = 5) -> dict:
    """حلقة طويلة = كذا قصة/آية متتابعة بمحرّك نور السينمائي.

    items: عناصر فيها {kind, hook, surah, ayah, ayah_to, who, theme}
    """
    from . import noor_premium as np
    from .noor_pool import APPLY

    workdir.mkdir(parents=True, exist_ok=True)
    segs: list[Path] = []
    used = items[:max_items]
    for i, it in enumerate(used):
        sub = workdir / f"seg{i:02d}"
        title_piece = it.get("who") or it.get("theme") or ""
        outro = (f"خلّينا نكمل… {used[i + 1].get('who') or 'القصة اللي بعدها'} "
                 "بعد لحظة. لو عاجبك، تابعنا وشارك الفيديو."
                 if i < len(used) - 1 else
                 "لو القصص أفادتك، اشترك في القناة… في قصص جديدة كل يوم 🤍")
        res = np.render({"surah": it["surah"], "ayah": it["ayah"],
                         "ayah_to": it.get("ayah_to"),
                         "reciter": it.get("reciter", "husary"),
                         "hook": (it.get("hook") if i == 0 else
                                  f"قصة {title_piece} 🤍"),
                         "outro": outro,
                         "scenes": it.get("scenes"),
                         "brand": f"نور — {it.get('theme') or 'قصص القرآن'}"},
                        sub)
        segs.append(res["video"])
        print(f"[noor] 🎞️ مقطع {i + 1}/{len(used)} خلص ({title_piece})",
              flush=True)

    if not segs:
        raise RuntimeError("مفيش مقاطع للطويل")
    lst = workdir / "long.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs),
                   encoding="utf-8")
    out = workdir / "noor_long.mp4"
    r = subprocess.run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i",
                        str(lst), "-c", "copy", "-movflags", "+faststart",
                        str(out)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("جمع الطويل فشل: " + (r.stderr or "")[-300:])
    total = sum(_dur(s) for s in segs)
    cover = workdir / "cover.png"
    subprocess.run([ffmpeg(), "-y", "-ss", "3", "-i", str(out), "-frames:v", "1",
                    str(cover)], capture_output=True)
    return {"video": out, "cover": cover, "duration": total,
            "segments": len(segs)}
