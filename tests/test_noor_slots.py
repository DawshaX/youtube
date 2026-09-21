"""مواعيد النشر — الشبكة اليومية والاختيار التلقائي.

ليه ده مهم؟ (2026-09-21) المستخدم شاف 3 حلقات تنزل ورا بعضها في دقيقة واحدة
وبعدها مفيش حاجة ساعات — لأن `_next_slot` كانت ترجّع None لما ساعات اليوم
تخلص، و«None» في الرفع معناها «انشر حالًا». الاختبارات دي بتقفل الباب ده:

  1) الشبكة بتتوسّع صح حسب عدد مشاريع جوجل (6 = كل 4 ساعات · 24 = كل ساعة)
  2) `_next_slot` عمرها ما ترجّع None وهي فيه ساعة فاضية (اليوم أو بكرة)
  3) `_pick_at` بتدي نشر فوري بس لو القناة ساكتة 3 ساعات، غير كده موعد
"""
from __future__ import annotations

import time

from scripts import noor_runner as R
from xtrendaw import settings as _settings
from xtrendaw import state as _state


def _cap(monkeypatch, n: int):
    # الدوال بتستورد settings جوه، فبنعدّل على الموديول نفسه
    monkeypatch.setattr(_settings, "YOUTUBE_DAILY_CAPACITY", n, raising=False)


def test_grid_one_project_is_every_four_hours(monkeypatch):
    monkeypatch.delenv("NOOR_SLOTS", raising=False)
    _cap(monkeypatch, 6)
    grid = R._slots()
    assert grid == [3, 7, 11, 15, 19, 23]
    gaps = [b - a for a, b in zip(grid, grid[1:])]
    assert all(g == 4 for g in gaps), "المفروض نشرة كل 4 ساعات"


def test_grid_two_projects_every_two_hours(monkeypatch):
    monkeypatch.delenv("NOOR_SLOTS", raising=False)
    _cap(monkeypatch, 12)
    assert R._slots() == list(range(0, 24, 2))


def test_grid_four_projects_every_hour(monkeypatch):
    monkeypatch.delenv("NOOR_SLOTS", raising=False)
    _cap(monkeypatch, 24)
    assert R._slots() == list(range(24)), "24 رفعة = نشرة كل ساعة"


def test_next_slot_never_none_while_free_slot_exists(monkeypatch):
    monkeypatch.delenv("NOOR_SLOTS", raising=False)
    _cap(monkeypatch, 6)
    at = R._next_slot([])
    assert at, "لازم يرجّع موعد — مش None (اللي كان معناه انشر حالًا)"
    # لازم يكون ساعة على الشبكة وفي المستقبل (بفارق 12 دقيقة على الأقل)
    ts = time.mktime(time.strptime(at[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
    assert ts - time.time() >= 11 * 60
    assert int(at[11:13]) in R._slots()


def test_next_slot_skips_used_hours_and_rolls_to_tomorrow(monkeypatch):
    monkeypatch.delenv("NOOR_SLOTS", raising=False)
    _cap(monkeypatch, 6)
    today = time.strftime("%Y-%m-%d")
    tomorrow = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 86400))
    used = [f"{today}T{h:02d}" for h in R._slots()]
    at = R._next_slot(used)
    assert at, "بكرة لسه فيه ساعات فاضية"
    assert at.startswith(tomorrow), f"المفروض ينزلق لبكرة، طلع {at}"


def test_pick_at_is_instant_by_default(monkeypatch):
    """النشر فوري افتراضيًا — «كل ساعة حلقة تتنشر» بلا تأخير مجدول."""
    monkeypatch.delenv("NOOR_SCHEDULE", raising=False)
    monkeypatch.delenv("NOOR_SLOTS", raising=False)

    # القناة ساكتة أسبوع → برضه فوري
    monkeypatch.setattr(_state, "published_log",
                        lambda: [{"ts": time.time() - 7 * 86400}])
    assert R._pick_at({}) is None

    # ات نشرت قبل ثانية → برضه فوري (مفيش حجز مواعيد)
    monkeypatch.setattr(_state, "published_log",
                        lambda: [{"ts": time.time() - 1}])
    assert R._pick_at({}) is None


def test_pick_at_schedules_only_when_asked(monkeypatch):
    """لو اتطلب الجدولة صراحةً → موعد على الشبكة."""
    monkeypatch.setenv("NOOR_SCHEDULE", "1")
    monkeypatch.delenv("NOOR_SLOTS", raising=False)
    _cap(monkeypatch, 24)
    at = R._pick_at({})
    assert at and at.endswith("Z"), "لازم يرجع موعد مجدول"
    assert int(at[11:13]) in R._slots()


def test_pick_at_handles_empty_log(monkeypatch):
    monkeypatch.delenv("NOOR_SCHEDULE", raising=False)
    monkeypatch.setattr(_state, "published_log", lambda: [])
    assert R._pick_at({}) is None
