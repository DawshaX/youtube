"""بوت التنظيم — يتابع الشجرة، يقدّم الجاهز، ويمنع المقفل.

مش مصنع جديد. ما يمسحش كارت، وما ينشرش ألف فيديو في يوم.
كل دورة يقدر يقول: إيه الجاهز، إيه المقفول، وإيه اللي دوره.
"""
from __future__ import annotations

from .noor_branches import branch_at, branch_count
from .noor_tree import BRANCHES, FAMILIES, is_hold
from .noor_variety import kinds as khair_kinds


def ready_cards() -> list[tuple[str, dict]]:
    from .noor_thousand import cards as sanad_cards
    from .noor_variety import cards as khair_cards
    return list(khair_cards()) + list(sanad_cards())


def next_ready(done: set[str] | None = None) -> dict | None:
    """أول سيناريو جاهز لسه ما اتنشرش. المقفل لا يمر."""
    done = done or set()
    for key, spec in ready_cards():
        if key in done:
            continue
        if is_hold(str(spec.get("kind") or "")) or is_hold(str(spec.get("plan_kind") or "")):
            continue
        return spec
    return None


def blocked() -> list[str]:
    return [b["id"] for b in BRANCHES if b.get("status") == "hold"]


def report(done: set[str] | None = None) -> dict:
    done = done or set()
    ready = ready_cards()
    left = [k for k, _ in ready if k not in done]
    per_day = 1  # خانة الروح في الجدول، مش الألف كلها
    return {
        "families": len(FAMILIES),
        "named_branches": len(BRANCHES),
        "addressable_branches": branch_count(),
        "sample_branch": branch_at(0)["ar"],
        "khair_108": len(khair_kinds()),
        "sanad_1000": len(ready) - len(khair_kinds()),
        "ready_total": len(ready),
        "ready_left": len(left),
        "years_at_spirit_slot": round(len(left) / 365, 2),
        "hold_closed": blocked(),
        "next_id": (next_ready(done) or {}).get("id"),
        "grid": "12 short + 3 long",
        "note": "الفهرس عنوان. الفيديو لا يطلع إلا من سيناريو جاهز. المقفل لا يتألف.",
    }


def guard(kind: str) -> bool:
    """True يعني مسموح يكمل. False يعني رف مقفول."""
    return not is_hold(kind)
