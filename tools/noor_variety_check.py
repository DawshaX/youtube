#!/usr/bin/env python3
"""يتأكد إن مكتبة الخير ≥ ١٠٠ وكل شكل مختلف، من غير ما نكسر جدول الـ١٢."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from xtrendaw.noor_grid import TYPES, SLOTS, validate
from xtrendaw.noor_variety import kinds, signatures

assert len(TYPES) == 12 and len(SLOTS) == 15
validate()
ks = kinds()
assert len(ks) >= 100, len(ks)
assert len({k["id"] for k in ks}) == len(ks)
assert len({k["hook"] for k in ks}) == len(ks)
sigs = signatures()
assert len(set(sigs)) == len(sigs), len(set(sigs))
for k in ks:
    assert "﴿" not in " ".join(k["lines"])
    assert k["kind"] == "spirit"
    assert len(k["scenes"]) >= 2
print(f"variety ok {len(ks)} kinds {len(set(sigs))} shapes")
