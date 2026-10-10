#!/usr/bin/env python3
"""الشجرة كاملة، والقديم ثابت، والمقفول ما يتألفش."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from xtrendaw.noor_grid import TYPES, SLOTS, validate
from xtrendaw.noor_tree import (
    FAMILIES, BRANCHES, add_branch, format_for, is_hold, named_present,
)
from xtrendaw.noor_variety import kinds

validate()
assert len(TYPES) == 12 and len(SLOTS) == 15
assert len(FAMILIES) == 9
ids = [b["id"] for b in BRANCHES]
assert len(ids) == len(set(ids))
live_engines = {b["engine"] for b in BRANCHES if b["status"] == "live"}
for t in TYPES:
    assert t["id"] in live_engines, t["id"]
missing = named_present([
    "قرآن كريم", "أحاديث", "أذكار", "أذكار الصباح والمساء", "أدعية",
    "قصص الأنبياء", "شاشة سوداء", "أخبار نافعة", "رقية شرعية", "ديني إسلامي",
    "ديني روحي",
])
assert not missing, missing
assert is_hold("fatwa") and is_hold("hulm") and is_hold("ruqyah") and is_hold("akhbar")
assert format_for({"kind": "quran"}) == "calm"
assert format_for({"kind": "ayah"}) == "calm"
assert format_for({"kind": "dua"}) == "calm"
assert format_for({"kind": "athkar"}) == "neon"
assert format_for({"kind": "asma"}) == "neon"
assert len(kinds()) >= 100
try:
    add_branch({"id": "quran", "ar": "نسخة", "family": "sacred", "status": "live"})
    raise SystemExit("replace was allowed")
except ValueError:
    pass
print(f"tree ok families {len(FAMILIES)} branches {len(BRANCHES)} khair {len(kinds())}")
