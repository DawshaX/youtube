#!/usr/bin/env python3
"""ألف سيناريو + فهرس فروع، والقديم ثابت، والمقفول مقفول."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from xtrendaw.noor_branches import branch_count, branch_at
from xtrendaw.noor_grid import SLOTS, TYPES, validate
from xtrendaw.noor_keeper import blocked, guard, next_ready, report
from xtrendaw.noor_thousand import cards, kinds, signatures
from xtrendaw.noor_variety import kinds as khair

validate()
assert len(TYPES) == 12 and len(SLOTS) == 15
ks = kinds()
assert len(ks) == 1000, len(ks)
assert len({k["id"] for k in ks}) == 1000
assert len({k["hook"] for k in ks}) == 1000
assert len({k["lines"][0] for k in ks}) == 1000
assert len(set(signatures())) == 1000
banned = ("﴿", "قال رسول", "يعالج", "خبر عاجل", "فتوى", "تفسير حلم")
blob = " ".join(k["hook"] + k["lines"][0] for k in ks)
for w in banned:
    assert w not in blob, w
assert len(khair()) >= 100
assert branch_count() >= 100_000
assert branch_at(0)["publishable"] is False
assert "fatwa" in blocked()
assert guard("fatwa") is False
assert guard("spirit") is True
nxt = next_ready(set())
assert nxt and nxt["id"].startswith("khair-")
rep = report(set())
assert rep["sanad_1000"] == 1000
assert rep["ready_total"] >= 1100
print(
    f"thousand ok {len(ks)} sanad branches {branch_count()} "
    f"years {rep['years_at_spirit_slot']} next {nxt['id']}"
)
