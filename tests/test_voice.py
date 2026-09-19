"""اختبارات مكتبة الأصوات — أوفلاين بالكامل.

تغطي: تطبيع المoods، الاختيار من القائمة الفعلية، الدوران (تجنب آخر 5)،
الحتمية حسب الـ seed، والتسجيل.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xtrendaw import voice  # noqa: E402


class TestMood(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(voice.normalize_mood("crazy"), "crazy")
        self.assertEqual(voice.normalize_mood("مجنون"), "crazy")
        self.assertEqual(voice.normalize_mood("هادئ"), "calm")
        self.assertEqual(voice.normalize_mood("غامض"), "mysterious")
        self.assertEqual(voice.normalize_mood("جاد"), "serious")
        self.assertEqual(voice.normalize_mood("دافي"), "warm")
        self.assertEqual(voice.normalize_mood(None), "warm")
        self.assertEqual(voice.normalize_mood("??"), "warm")

    def test_pools_are_real_voices(self):
        valid = set(voice.load_ar_voices())
        for mood, pool in voice.MOOD_VOICES.items():
            for v in pool:
                self.assertIn(v, valid, f"صوت غير حقيقي في جدول {mood}: {v}")


class TestPick(unittest.TestCase):
    def test_returns_valid_voice(self):
        v = voice.pick_voice("crazy", seed="t1")
        self.assertIn(v, voice.load_ar_voices())

    def test_deterministic_per_seed(self):
        a = voice.pick_voice("warm", seed="topic-x")
        b = voice.pick_voice("warm", seed="topic-x")
        self.assertEqual(a, b)
        c = voice.pick_voice("warm", seed="topic-y")
        # احتمال التعادل exists (pool محدود) — لو اتحدا نعيد بمزاج تاني
        # لكن الحتمية نفسها هي اللي بنختبرها
        self.assertIn(c, voice.MOOD_VOICES["warm"])

    def test_avoid_recent(self):
        # لو كل أصوات الـ pool محظورة → يرجع من الـ pool كله (بلا فشل)
        pool = list(voice.MOOD_VOICES["calm"])
        v = voice.pick_voice("calm", seed="s", avoid=pool[: len(pool) - 1])
        self.assertEqual(v, pool[-1])
        # ولو كلهم محظورين → ما يفشلش
        v2 = voice.pick_voice("calm", seed="s", avoid=list(pool))
        self.assertIn(v2, pool)

    def test_mood_changes_pool(self):
        crazy = {voice.pick_voice("crazy", seed=f"i{i}", avoid=[]) for i in range(50)}
        calm = {voice.pick_voice("calm", seed=f"i{i}", avoid=[]) for i in range(50)}
        self.assertTrue(crazy <= set(voice.MOOD_VOICES["crazy"]))
        self.assertTrue(calm <= set(voice.MOOD_VOICES["calm"]))
        self.assertNotEqual(crazy, calm)


class TestRecentAndRegister(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._orig = voice.PRODUCTION_LOG_PATH
        voice.PRODUCTION_LOG_PATH = self.root / "production_log.json"

    def tearDown(self):
        voice.PRODUCTION_LOG_PATH = self._orig
        self.tmp.cleanup()

    def test_recent_voices(self):
        log = [{"topicId": "a", "voice": "ar-A"},
               {"topicId": "b", "voice": "ar-B"},
               {"topicId": "c", "voice": "ar-C"}]
        voice.PRODUCTION_LOG_PATH.write_text(json.dumps(log), encoding="utf-8")
        self.assertEqual(voice.recent_voices(), ["ar-C", "ar-B", "ar-A"])
        self.assertEqual(voice.recent_voices(2), ["ar-C", "ar-B"])

    def test_recent_empty_when_no_log(self):
        self.assertEqual(voice.recent_voices(), [])

    def test_register_usage(self):
        log = [{"topicId": "x", "title": "ت"},
               {"topicId": "y", "title": "ث"}]
        voice.PRODUCTION_LOG_PATH.write_text(json.dumps(log), encoding="utf-8")
        voice.register_usage("ar-SA-HamedNeural", "y")
        out = json.loads(voice.PRODUCTION_LOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(out[1]["voice"], "ar-SA-HamedNeural")
        self.assertNotIn("voice", out[0])
        # موضوع مش موجود → آخر مدخل
        voice.register_usage("ar-QA-MoazNeural", "nope")
        out = json.loads(voice.PRODUCTION_LOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(out[1]["voice"], "ar-QA-MoazNeural")


class TestRotationEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._orig = voice.PRODUCTION_LOG_PATH
        voice.PRODUCTION_LOG_PATH = self.root / "production_log.json"
        voice.PRODUCTION_LOG_PATH.write_text("[]", encoding="utf-8")

    def tearDown(self):
        voice.PRODUCTION_LOG_PATH = self._orig
        self.tmp.cleanup()

    def test_5_episodes_5_different_voices(self):
        """5 حلقات warm → ما ينفعش صوت يتكرر (pool فيه 5 أصوات)."""
        picked = []
        for i in range(5):
            v = voice.pick_voice("warm", seed=f"ep{i}")
            picked.append(v)
            log = json.loads(voice.PRODUCTION_LOG_PATH.read_text(encoding="utf-8"))
            log.append({"topicId": f"ep{i}", "voice": v})
            voice.PRODUCTION_LOG_PATH.write_text(json.dumps(log), encoding="utf-8")
        self.assertEqual(len(set(picked)), len(picked),
                         "صوت اتكرر خلال 5 حلقات: " + str(picked))


if __name__ == "__main__":
    unittest.main(verbosity=2)
