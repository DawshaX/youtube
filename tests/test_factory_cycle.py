"""اختبارات دورة المصنع: حارس كوتة يوتيوب + سجل النشر المحفوظ على git.

الدرس اللي الملف ده بيحميه (2026-09-19): الدورة السحابية كانت بتنسى كل حاجة
لأن state/ كان مهمل من git — يعني احتمال نشر نفس الحلقة مرتين وفشل حصة.
"""
from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from xtrendaw import run_cycle, settings, state


class PublishedLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig_file = state.PUBLISHED_FILE
        self._orig_cap = settings.DAILY_CAP
        state.PUBLISHED_FILE = Path(self._tmp.name) / "published.json"

    def tearDown(self) -> None:
        state.PUBLISHED_FILE = self._orig_file
        settings.DAILY_CAP = self._orig_cap

    def test_empty_ledger_counts_zero(self) -> None:
        self.assertEqual(state.published_last_24h(), 0)
        self.assertFalse(run_cycle._quota_blocked())

    def test_counts_only_last_24h(self) -> None:
        now = time.time()
        state._wr(state.PUBLISHED_FILE, [
            {"id": "fresh1", "ts": now - 60},
            {"id": "fresh2", "ts": now - 3600},
            {"id": "old", "ts": now - 26 * 3600},
            "صف تالف مش قاموس",             # يتجاهل بلا انفجار
            {"id": "nots"},                # بلا طابع
            {"id": "badts", "ts": "نص"},   # طابع مش رقمي
        ])
        self.assertEqual(state.published_last_24h(), 2)

    def test_guard_blocks_at_cap(self) -> None:
        settings.DAILY_CAP = 6
        now = time.time()
        state._wr(state.PUBLISHED_FILE,
                  [{"id": f"v{i}", "ts": now - i} for i in range(5)])
        self.assertFalse(run_cycle._quota_blocked(), "أقل من السقف = يمشي")
        state.push_published({"id": "sixth", "ts": now})
        self.assertTrue(run_cycle._quota_blocked(), "السقف = يتوقف فورًا")

    def test_cap_zero_means_unlimited(self) -> None:
        settings.DAILY_CAP = 0
        state._wr(state.PUBLISHED_FILE,
                  [{"id": f"v{i}", "ts": time.time()} for i in range(50)])
        self.assertFalse(run_cycle._quota_blocked())

    def test_publish_log_keeps_newest_500(self) -> None:
        for i in range(510):
            state.push_published({"id": f"v{i}", "ts": time.time()})
        data = json.loads(state.PUBLISHED_FILE.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 500)
        self.assertEqual(data[-1]["id"], "v509")


class FactoryMemoryOnGitTest(unittest.TestCase):
    """الذاكرة لازم تبقى متتبعة في git — من غيرها الدورة السحابية بتبدأ فاضية."""

    def test_state_memory_is_not_ignored(self) -> None:
        import subprocess
        root = Path(__file__).resolve().parent.parent
        for name in ("produced.json", "ledger.json", "published.json",
                     "last_publish.json", "yt_recent.json",
                     "reciter_proven.json", "last_cycle.json"):
            rel = f"state/{name}"
            p = subprocess.run(["git", "check-ignore", "-q", rel], cwd=root)
            self.assertNotEqual(p.returncode, 0,
                                f"{rel} مهمل من git — الذاكرة هتضيع كل دورة")
        # والعكس: الكاش الوسيط يفضل مهمل
        p = subprocess.run(["git", "check-ignore", "-q", "state/din_cache"],
                           cwd=root)
        self.assertEqual(p.returncode, 0, "state/din_cache المفروض يفضل مهمل")


if __name__ == "__main__":
    unittest.main()
