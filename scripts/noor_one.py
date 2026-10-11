#!/usr/bin/env python3
"""ينشر الحلقة الجاية من المكتبة الواحدة. القديم والجديد في نفس الطابور."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LIB = ROOT / "data" / "noor_next" / "one_library.jsonl"
LEDGER = ROOT / "state" / "noor_library.json"


def _load() -> dict:
    if not LEDGER.exists():
        return {"served": []}
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _rows() -> list[dict]:
    if not LIB.exists():
        return []
    return [json.loads(l) for l in LIB.read_text(encoding="utf-8").splitlines() if l.strip()]


def next_item() -> dict | None:
    st = _load()
    done = set(st.get("served") or [])
    last = str(st.get("last_series") or "")
    fresh = [r for r in _rows() if r.get("id") not in done and r.get("series_id") != last]
    pool = fresh or [r for r in _rows() if r.get("id") not in done]
    if not pool:
        return None
    # لفّ بين العائلات عشان القديم والجديد يطلعوا، ومش نوع واحد ياكل الطابور.
    families: dict[str, list[dict]] = {}
    for row in pool:
        families.setdefault(str(row.get("series_id") or row.get("engine") or "عام"), []).append(row)
    turn = int(st.get("turn") or 0) % max(1, len(families))
    key = list(families)[turn]
    st["turn"] = turn + 1
    _save(st)
    return families[key][0]


def _mark(row: dict, url: str = "", err: str = "") -> None:
    st = _load()
    st["served"] = list(dict.fromkeys([*(st.get("served") or []), row["id"]]))
    st["last_series"] = row.get("series_id") or ""
    st.setdefault("done", []).append({"id": row["id"], "url": url, "err": err})
    _save(st)


def _runner():
    import importlib.util
    name = "noor_runner_live"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "noor_runner.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _publish_life(row: dict) -> int:
    from xtrendaw.noor_next.produce import render
    runner = _runner()
    work = runner.WORK / f"one_{row['id']}"
    made = render(row, work)
    if not made:
        _mark(row, err="no_footage")
        return 1
    title = f"{made['lines'][0][:70]} | {row.get('series_title') or 'نور'}"
    src = row.get("source") or ""
    credits = "\n".join(made["credits"]) or "لقطات مرخّصة."
    desc = f"{row.get('spoken') or ''}\n\n{src}\n\n{credits}"
    url, err = runner._publish(made["video"], None, title[:95], desc, ["نور", row.get("series_title") or "خير"], synthetic=True)
    if err in ("quota_guard", "too_soon"):
        return 2
    _mark(row, url or "", err or "")
    print(f"[one] life {row['id']} {url or err}", flush=True)
    return 0 if url or runner.DRY else 1


def _publish_source(row: dict) -> int:
    os.environ["NOOR_ITEM_JSON"] = json.dumps(row, ensure_ascii=False)
    os.environ["NOOR_PLAN"] = "0"
    runner = _runner()
    rc = runner.short_once()
    _mark(row, err="" if rc == 0 else "source_failed")
    print(f"[one] source {row['id']} rc={rc}", flush=True)
    return 0 if rc == 0 else 1


def main() -> int:
    if not LIB.exists():
        print("[one] المكتبة الواحدة مش موجودة", flush=True)
        return 1
    for _ in range(3):
        row = next_item()
        if not row:
            print("[one] الطابور خلص", flush=True)
            return 1
        engine = row.get("engine")
        rc = _publish_source(row) if engine == "source" else _publish_life(row)
        if rc == 2:
            return 0
        if rc == 0:
            return 0
    # ساعة ما تفضاش: المسار القديم يكمّل لو المكتبة وقعت ثلاث مرات.
    runner = _runner()
    print("[one] ثلاث محاولات وقعت — المسار القديم يكمل الساعة", flush=True)
    return runner.short_once()


if __name__ == "__main__":
    raise SystemExit(main())
