#!/usr/bin/env python3
"""صيانة يدوية: حذف حلقة من يوتيوب بمعرّفها — بأمان.

ليه ده موجود؟ (2026-09-19) حلقة «تحدي المارشميلو» طلعت مرتين بسبب بق
تكرار المواضيع. الحذف اليدوي محتاج أمر صريح، ومعاه حراسات:

  1) لازم المعرّف يكون في `state/published.json` (مفيش حذف لأي حاجة مش بتاعتنا).
  2) لازم `--yes` (يعني حذف مقصود، مش بالغلط).
  3) بيسجّل الحذف في `state/ledger.json` للمراجعة.

الاستخدام:  python scripts/video_delete.py --id gEcssSpLwD0 --yes
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _our_ids() -> set:
    try:
        pub = json.loads((ROOT / "state" / "published.json").read_text("utf-8"))
        return {str(x.get("id")) for x in pub if isinstance(x, dict)}
    except Exception:
        return set()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()

    if not a.yes:
        print("⛔ محتاج --yes (الحذف مقصود؟)")
        return 2
    if a.id not in _our_ids():
        print(f"⛔ {a.id} مش في سجل حلاقتنا — الحذف مرفوض")
        return 3

    from xtrendaw.publish import youtube as yt
    ok = yt.delete(a.id)
    print(("✓ اتحذف " if ok else "✗ الحذف فشل ") + a.id)
    try:
        led = ROOT / "state" / "ledger.json"
        rows = json.loads(led.read_text("utf-8")) if led.exists() else []
        rows.append({"at": time.strftime("%Y-%m-%d %H:%M"), "kind": "delete",
                     "id": a.id, "ok": bool(ok)})
        led.write_text(json.dumps(rows[-500:], ensure_ascii=False, indent=1),
                       encoding="utf-8")
    except Exception:
        pass
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
