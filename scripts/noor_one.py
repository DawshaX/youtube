#!/usr/bin/env python3
"""ينشر الحلقة الجاية من المكتبة الواحدة. القديم والجديد في نفس الطابور."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SHORT_CAP = int(os.environ.get("NOOR_SHORTS_PER_DAY", "8"))
LONG_CAP = int(os.environ.get("NOOR_LONGS_PER_DAY", "4"))
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


def _day() -> str:
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
    except Exception:
        tz = dt.timezone(dt.timedelta(hours=-7))
    return dt.datetime.now(tz).date().isoformat()


def _counts() -> tuple[int, int]:
    bag = _load().get("day") or {}
    if bag.get("date") != _day():
        return 0, 0
    return int(bag.get("short") or 0), int(bag.get("long") or 0)


def _bump(kind: str) -> None:
    st = _load()
    day = _day()
    bag = st.get("day") or {}
    if bag.get("date") != day:
        bag = {"date": day, "short": 0, "long": 0}
    key = "long" if kind == "long" else "short"
    bag[key] = int(bag.get(key) or 0) + 1
    st["day"] = bag
    _save(st)


def wanted_kind(shorts: int | None = None, longs: int | None = None) -> str | None:
    if shorts is None or longs is None:
        shorts, longs = _counts()
    if shorts >= SHORT_CAP and longs >= LONG_CAP:
        return None
    if longs >= LONG_CAP:
        return "short"
    if shorts >= SHORT_CAP:
        return "long"
    return "long" if (shorts + longs) % 3 == 2 else "short"


def next_item(kind: str | None = None) -> dict | None:
    st = _load()
    done = set(st.get("served") or [])
    last = str(st.get("last_series") or "")
    def ok(row: dict) -> bool:
        if row.get("id") in done or row.get("engine") == "source":
            return False
        is_long = row.get("kind") == "long"
        if kind == "long":
            return is_long
        if kind == "short":
            return not is_long
        return True
    fresh = [r for r in _rows() if ok(r) and r.get("series_id") != last]
    pool = fresh or [r for r in _rows() if ok(r)]
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
    st.setdefault("done", []).append({"id": row["id"], "url": url, "err": err, "kind": row.get("kind")})
    _save(st)
    if url:
        _bump(str(row.get("kind") or "short"))


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
    who = made.get("soul")
    host = f"الشخصية: {who}، أصلية للمصنع.\n" if who else ""
    craft = f"أسلوب اللقطات: {made.get('format')} — صناعة المصنع، مش نسخ لفيديو.\n" if made.get("format") else ""
    desc = f"{host}{craft}{row.get('spoken') or ''}\n\n{src}\n\n{credits}"
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


def _unserved(kind: str, engine: str = "life") -> list[dict]:
    done = set(_load().get("served") or [])
    rows = []
    for row in _rows():
        if row.get("id") in done or row.get("engine") != engine or row.get("kind") != kind:
            continue
        rows.append(row)
    return rows


def _diverse(rows: list[dict], count: int) -> list[dict]:
    out = []
    seen = set()
    for row in rows:
        series = row.get("series_id") or row.get("id")
        if series in seen:
            continue
        seen.add(series)
        out.append(row)
        if len(out) == count:
            break
    return out


def opening() -> int:
    """شورتان وفيديو طويل من المكتبة، وبعدها الساعة ترجع عادي."""
    batch = _diverse(_unserved("short"), 2) + _diverse(_unserved("long"), 1)
    if len(batch) < 3:
        print("[one] الافتتاح ناقص شورت أو طويل", flush=True)
        return 1
    published = 0
    for row in batch:
        rc = _publish_life(row)
        if rc == 2:
            print(f"[one] الافتتاح وقف بعد {published} — الحصة أو الوقت", flush=True)
            return 0 if published else 0
        if rc == 0:
            published += 1
            print(f"[one] افتتاح {row.get('kind')} {row.get('id')}", flush=True)
    print(f"[one] الافتتاح نشر {published}", flush=True)
    return 0 if published else 1


def _one_live(kind: str, tries: int = 4) -> int:
    for _ in range(tries):
        row = next_item(kind)
        if not row:
            print(f"[one] مفيش {kind} جديد", flush=True)
            return 1
        try:
            rc = _publish_life(row)
        except Exception as exc:
            print(f"[one] الرندر وقع على {row.get('id')}: {type(exc).__name__}: {exc}", flush=True)
            _mark(row, err=type(exc).__name__)
            continue
        if rc == 0:
            print(f"[one] نزل {kind} {row.get('id')}", flush=True)
            return 0
        if rc == 2:
            return 2
        print(f"[one] {row.get('id')} ما نزلش، هنجرب غيره", flush=True)
    return 1


def first() -> int:
    """أول ريل وأول طويل من المصنع الجديد، وبعدها الساعة تكمل بنفس الشكل."""
    published = 0
    for kind in ("short", "long"):
        rc = _one_live(kind)
        if rc == 0:
            published += 1
        elif rc == 2:
            print(f"[one] وقفنا بعد {published}. الحصة أو الوقت.", flush=True)
            return 0 if published else 2
    print(f"[one] أول دفعة نشرت {published} من 2", flush=True)
    return 0 if published == 2 else 1


def main() -> int:
    if os.environ.get("NOOR_FIRST") == "1":
        return first()
    if not LIB.exists():
        print("[one] المكتبة الواحدة مش موجودة", flush=True)
        return 1
    kind = wanted_kind()
    shorts, longs = _counts()
    if kind is None:
        print(f"[one] سقف اليوم خلص: {shorts} شورت و{longs} طويل", flush=True)
        return 0
    print(f"[one] اليوم {shorts}/{SHORT_CAP} شورت و{longs}/{LONG_CAP} طويل — الجاية {kind}", flush=True)
    for _ in range(3):
        row = next_item(kind)
        if not row:
            print("[one] الطابور خلص", flush=True)
            return 1
        engine = row.get("engine")
        try:
            rc = _publish_source(row) if engine == "source" else _publish_life(row)
        except Exception as exc:
            print(f"[one] الرندر وقع على {row.get('id')}: {type(exc).__name__}: {exc}", flush=True)
            _mark(row, err=type(exc).__name__)
            continue
        if rc == 2:
            return 0
        if rc == 0:
            return 0
    print("[one] ثلاث محاولات وقعت — الساعة دي من غير نشر قديم", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
