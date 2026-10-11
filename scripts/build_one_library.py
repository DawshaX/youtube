#!/usr/bin/env python3
"""يضيف المحتوى القديم على مكتبة الأصناف الجديدة. مفيش حذف."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW = ROOT / "data" / "noor_next" / "episodes.jsonl"
DIN = ROOT / "content" / "din_stock.json"
STOCK = ROOT / "state" / "noor_cache" / "stock"
OUT = ROOT / "data" / "noor_next" / "one_library.jsonl"


def main() -> None:
    rows = []
    seen = set()

    def add(row: dict) -> None:
        if row["id"] in seen:
            return
        seen.add(row["id"])
        rows.append(row)

    if NEW.exists():
        for line in NEW.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ep = json.loads(line)
            ep["engine"] = "life"
            ep["origin"] = "مكتبة الأصناف الجديدة"
            add(ep)

    if DIN.exists():
        din = json.loads(DIN.read_text(encoding="utf-8"))
        for shelf, title in (
            ("duas", "دعاء من المصدر"),
            ("hadiths", "حديث من المصدر"),
            ("adhkar", "ذكر من المصدر"),
            ("info", "معلومة من المصدر"),
        ):
            for i, it in enumerate(din.get(shelf) or []):
                text = (it.get("text") or "").strip()
                src = (it.get("src") or "").strip()
                if not text:
                    continue
                add({
                    "id": f"old-{shelf}-{i:04d}",
                    "engine": "spoken",
                    "origin": "المخزون الديني القديم",
                    "series_id": f"old-{shelf}",
                    "series_title": title,
                    "kind": "short",
                    "field": title,
                    "hook": text.split("،")[0][:80],
                    "spoken": text,
                    "scene": "calm empty courtyard morning no people",
                    "benefit": src,
                    "source": src,
                    "factory": False,
                })

    windows = json.loads((STOCK / "windows.json").read_text(encoding="utf-8"))
    for w in windows:
        for plan, prefix, theme in (("quran", "q", "قرآن"), ("tafsir", "t", "تدبر")):
            add({
                "id": f"{prefix}-{int(w['surah']):03d}-{int(w['frm']):03d}",
                "engine": "source",
                "origin": "مصنع التلاوة",
                "series_id": f"old-{plan}",
                "series_title": theme,
                "kind": "ayah",
                "plan": plan,
                "theme": theme,
                "surah": w["surah"],
                "ayah": w["frm"],
                "ayah_to": w["to"],
                "hook": f"سورة {w.get('name') or w['surah']}",
                "source": "api.alquran.cloud",
                "factory": False,
            })

    for path in sorted(STOCK.glob("hadith_*_short.json")):
        col = path.name.replace("hadith_", "").replace("_short.json", "")
        items = json.loads(path.read_text(encoding="utf-8"))
        for h in items:
            n = int(h.get("n") or 0)
            if not n:
                continue
            add({
                "id": f"h-{col}-{n}",
                "engine": "source",
                "origin": "مصنع الحديث",
                "series_id": f"old-hadith-{col}",
                "series_title": f"حديث {col}",
                "kind": "hadith",
                "collection": col,
                "index": n,
                "theme": "حديث",
                "hook": f"حديث من {col}",
                "source": col,
                "factory": False,
            })

    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({
        "rows": len(rows),
        "life": sum(1 for r in rows if r.get("engine") == "life"),
        "spoken": sum(1 for r in rows if r.get("engine") == "spoken"),
        "source": sum(1 for r in rows if r.get("engine") == "source"),
        "path": str(OUT),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
