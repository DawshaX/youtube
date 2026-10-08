"""فحص جدول الـ١٢ نوع + مكتبة الأفكار + الاستوديو. بلا نشر."""
from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from xtrendaw import noor_grid, noor_signs  # noqa: E402


def main() -> int:
    fails = noor_grid.validate()
    print("أنواع:", len(noor_grid.TYPES), "| أيام:", len(noor_grid.WEEK))
    for wd in range(7):
        kinds = noor_grid.WEEK[wd]
        longs = [k for k, s in zip(kinds, noor_grid.SLOTS) if s["form"] == "long"]
        print(f"  {noor_grid.WEEKDAY_AR[wd]}: {noor_grid.DAY_THEME[wd]} | طويل: {', '.join(longs)}")
    # نافذة واحدة: خميس ١١:٢٠ القاهرة لازم يلقط الطويل ١١:٠٠ بس
    cairo = ZoneInfo("Africa/Cairo")
    sample = dt.datetime(2026, 10, 8, 11, 20, tzinfo=cairo)
    got = noor_grid.due(set(), sample)
    if len(got) != 1 or got[0]["form"] != "long" or got[0]["h"] != 11:
        fails.append(f"نافذة الخميس غلط: {got}")
    else:
        print("نافذة الاختبار:", got[0]["label"])
    # مراجع المعجزات/الحمد/النصر
    for kind in ("mujiza", "hamd", "nasr"):
        n = len(noor_signs.series(kind))
        print(f"  سلسلة {kind}: {n}")
        if n < 15:
            fails.append(f"{kind} قصير: {n}")
    # ٣ آيات حية من المصدر
    ua = {"User-Agent": "NoorFactory/1.0"}
    for s, a in ((21, 69), (14, 7), (94, 5)):
        url = f"https://api.alquran.cloud/v1/ayah/{s}:{a}/quran-uthmani"
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=25).read()
            text = json.loads(raw)["data"]["text"]
        except Exception as exc:  # noqa: BLE001
            fails.append(f"آية {s}:{a} {type(exc).__name__}")
            continue
        if not text or len(text) < 8:
            fails.append(f"آية {s}:{a} فاضية")
        else:
            print(f"  آية {s}:{a} «{text[:42]}»")
    lib = ROOT / "content" / "idea_library.json"
    if lib.exists():
        data = json.loads(lib.read_text(encoding="utf-8"))
        print(f"مكتبة الأفكار: بذور {data.get('seeds')} + بطاقات {data.get('leads')}")
        if int(data.get("leads") or 0) < 50:
            fails.append("مكتبة الأفكار صغيرة")
    else:
        fails.append("مكتبة الأفكار مش موجودة")
    today = noor_grid.cairo_now()
    print("القاهرة الآن:", today.strftime("%Y-%m-%d %H:%M"), noor_grid.WEEKDAY_AR[today.weekday()])
    print("الجاي:", noor_grid.next_slot(set(), today))
    due = noor_grid.due(set(), today)
    print("مستحق دلوقتي:", due[0]["label"] if due else "لا")
    if fails:
        print("❌")
        for f in fails:
            print(" ·", f)
        return 1
    print("🎉 الجدول والمكتبة تمام")
    return 0


if __name__ == "__main__":
    sys.exit(main())
