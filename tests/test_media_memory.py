"""ذاكرة الوسائط: أي لقطة اتستخدمت مرة ما تتكررش في حلقة تانية.

الدرس (2026-09-19): نفس الصور طلعت في 4 فيديوهات مختلفة، وصور التجربة الثابتة
كانت بتتكرر لأن مفيش ذاكرة بين الحلقات ومفيش بوابة تقفل المخزون القديم.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from xtrendaw import eye, footage, settings, state


class MediaMemoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig = state.MEDIA_FILE
        state.MEDIA_FILE = Path(self._tmp.name) / "media_used.json"

    def tearDown(self) -> None:
        state.MEDIA_FILE = self._orig

    def test_marking_prevents_reuse(self) -> None:
        self.assertFalse(state.media_seen("https://x/clip1.mp4"))
        state.mark_media_used("https://x/clip1.mp4", "pexels", "ep1")
        self.assertTrue(state.media_seen("https://x/clip1.mp4"))
        rec = state.media_used()["https://x/clip1.mp4"]
        self.assertEqual(rec["source"], "pexels")
        self.assertEqual(rec["episode"], "ep1")

    def test_empty_key_is_ignored(self) -> None:
        state.mark_media_used("", "pexels", "ep1")
        self.assertEqual(state.media_used(), {})

    def test_log_stays_bounded(self) -> None:
        for i in range(5100):
            state.mark_media_used(f"u{i}", "pixabay", f"ep{i}")
        self.assertLessEqual(len(state.media_used()), 5000)

    def test_static_vault_is_blocked_when_disabled(self) -> None:
        """صور التجربة ممنوعة في الإنتاج — المصنع يجيب ميديا جديدة."""
        with mock.patch.object(settings, "ALLOW_STATIC_VAULT", False):
            self.assertIsNone(
                footage.vault_clip("fact1", "أي نص", 2.0,
                                   Path(self._tmp.name), "seed:1"),
                "المخزون الثابت لازم يرجع None لما يكون مقفول")

    def test_used_static_clip_is_excluded_from_picking(self) -> None:
        present = footage.vault_available()
        if len(present) < 2:
            self.skipTest("مفيش خزنة محلية في النسخة دي")
        state.mark_media_used(f"vault:{present[0]}", "internal", "ep_prev")
        picked = footage.pick_vault_clip("fact1", "النص", "s:1")
        self.assertIsNotNone(picked)
        # ممكن يرجّع نفس اللقطة لو الخزنة كلها مستهلكة، لكن مش أول واحدة فاضية
        if len(present) > 1:
            self.assertNotEqual(picked, present[0])


class EyeQueueTest(unittest.TestCase):
    """طابور العين — مواضيع من مشاهدة فيديو مشهور كامل. لازم ينسحب ويتأرشف."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig_q = eye.EYE_TOPICS_PATH
        self._orig_c = eye.EYE_CONSUMED_PATH
        eye.EYE_TOPICS_PATH = Path(self._tmp.name) / "eye_topics.json"
        eye.EYE_CONSUMED_PATH = Path(self._tmp.name) / "eye_consumed.json"
        self.topic = {"id": "eye-TEST1", "title_ar": "عنوان", "hook_ar": "خطاف",
                      "facts_ar": ["١", "٢", "٣"], "tags": "وسم1,وسم2"}
        eye.EYE_TOPICS_PATH.write_text(
            json.dumps([self.topic], ensure_ascii=False), encoding="utf-8")
        eye.EYE_CONSUMED_PATH.write_text("[]", encoding="utf-8")

    def tearDown(self) -> None:
        eye.EYE_TOPICS_PATH = self._orig_q
        eye.EYE_CONSUMED_PATH = self._orig_c

    def test_consume_moves_topic_to_archive(self) -> None:
        taken = eye.consume_queue(seen=set())
        self.assertIsNotNone(taken, "لازم ينسحب موضوع من الطابور")
        self.assertEqual(taken["id"], "eye-TEST1")
        self.assertIn("_consumedAt", taken)
        left = json.loads(eye.EYE_TOPICS_PATH.read_text(encoding="utf-8"))
        arch = json.loads(eye.EYE_CONSUMED_PATH.read_text(encoding="utf-8"))
        self.assertEqual(left, [], "الطابور فضى")
        self.assertEqual(arch[0]["id"], "eye-TEST1", "اتأرشف للمراجعة")

    def test_empty_queue_returns_none(self) -> None:
        eye.consume_queue(seen=set())
        self.assertIsNone(eye.consume_queue(seen=set()))


if __name__ == "__main__":
    unittest.main()
