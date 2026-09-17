"""اختبارات العين — أوفلاين بالكامل (بلا شبكة، بلا ffmpeg).

تغطي: تحليل tسميات json3، بناء الهاضم، طابور العين (سحب/أرشفة/نط
على المكرر)، تطبيع موضوع المصنع، وقراءة المدة.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xtrendaw import eye  # noqa: E402


SAMPLE_JSON3 = {
    "events": [
        {"tStartMs": 120, "dDurationMs": 780,
         "segs": [{"utf8": "شوف "}, {"utf8": "ده!"}]},
        {"tStartMs": 900, "dDurationMs": 0, "segs": []},          # فاصل → يتنطى
        {"tStartMs": 950, "dDurationMs": 1400,
         "segs": [{"utf8": "النتيجة "}, {"utf8": "\n"}]},
        {"tStartMs": 300, "dDurationMs": 500,
         "segs": [{"utf8": "تفصيلة متأخرة"}]},
    ]
}


class TestCaptions(unittest.TestCase):
    def test_parse_json3_sorted_and_clean(self):
        out = eye.parse_json3_captions(SAMPLE_JSON3)
        self.assertEqual(len(out), 3)
        # مرتب زمنيًا: التفصيلة المتأخرة (0.3s) قبل «النتيجة» (0.95s)
        self.assertEqual(out[0]["text"], "شوف ده!")
        self.assertEqual(out[0]["t"], 0.12)
        self.assertEqual(out[1]["text"], "تفصيلة متأخرة")
        self.assertEqual(out[2]["text"], "النتيجة")
        self.assertTrue(all(c["dur"] >= 0 for c in out))

    def test_parse_empty(self):
        self.assertEqual(eye.parse_json3_captions({}), [])
        self.assertEqual(eye.parse_json3_captions({"events": []}), [])


class TestDigest(unittest.TestCase):
    def _report(self):
        return {
            "durationSeconds": 24.0,
            "meta": {"title": "SPEED CHALLENGE", "channel": "X",
                     "region": "EG", "viewCount": 39000000,
                     "likeCount": 150000},
            "captions": [
                {"t": 0.1, "dur": 2.0, "text": "شوفين ده"},
                {"t": 12.0, "dur": 3.0, "text": "النتيجة خرافية"},
            ],
            "scenes": [
                {"start": 0.0, "end": 2.1, "colors": ["#112233", "#aabbcc"],
                 "brightness": 0.52, "motion": 0.01},
                {"start": 2.1, "end": 5.0, "colors": ["#ff0000"],
                 "brightness": 0.3, "motion": 0.12},
            ],
            "audioRmsPerSec": [-40.0, -25.0, -18.0],
        }

    def test_digest_contains_every_layer(self):
        d = eye.build_digest(self._report())
        self.assertIn("SPEED CHALLENGE", d)
        self.assertIn("39000000", d)
        self.assertIn("شوفين ده", d)
        self.assertIn("النتيجة خرافية", d)
        self.assertIn("#112233", d)
        self.assertIn("ساكن", d)      # motion 0.01 < 0.02
        self.assertIn("سريع", d)      # motion 0.12 > 0.08
        self.assertIn("أعلى طاقة عند ~2", d)

    def test_digest_no_captions_explicit(self):
        r = self._report()
        r["captions"] = []
        d = eye.build_digest(r)
        self.assertIn("مفيش مسار تسميات", d)


class TestQueue(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._orig_topics = eye.EYE_TOPICS_PATH
        self._orig_consumed = eye.EYE_CONSUMED_PATH
        eye.EYE_TOPICS_PATH = self.root / "eye_topics.json"
        eye.EYE_CONSUMED_PATH = self.root / "eye_consumed.json"

    def tearDown(self):
        eye.EYE_TOPICS_PATH = self._orig_topics
        eye.EYE_CONSUMED_PATH = self._orig_consumed
        self.tmp.cleanup()

    def _topic(self, n):
        return {
            "id": f"eye-test{n}",
            "title_ar": f"عنوان فريد تمامًا رقم {n} xyz",
            "hook_ar": f"خطاف {n}",
            "facts_ar": [f"حقيقة {n} أ", f"حقيقة {n} ب", f"حقيقة {n} ج"],
            "_eye": {"videoId": f"vid{n}"},
        }

    def test_save_then_consume(self):
        t1, t2 = self._topic(1), self._topic(2)
        eye.save_topic(t1)
        eye.save_topic(t2)
        got = eye.consume_queue(set())
        self.assertEqual(got["id"], "eye-test1")
        self.assertIn("_consumedAt", got)
        # الأول انسحب من الطابور وأرشف
        remaining = json.loads(eye.EYE_TOPICS_PATH.read_text())
        self.assertEqual([t["id"] for t in remaining], ["eye-test2"])
        consumed = json.loads(eye.EYE_CONSUMED_PATH.read_text())
        self.assertEqual([t["id"] for t in consumed], ["eye-test1"])
        # الثاني في النوبة التالية
        got2 = eye.consume_queue(set())
        self.assertEqual(got2["id"], "eye-test2")
        self.assertIsNone(eye.consume_queue(set()))

    def test_skip_seen_fingerprint(self):
        t1, t2 = self._topic(11), self._topic(12)
        eye.save_topic(t1)
        eye.save_topic(t2)
        seen = {eye.content.fingerprint(t1)}
        got = eye.consume_queue(seen)
        # الأول في «المشهود» → تنطى على التاني
        self.assertEqual(got["id"], "eye-test12")
        remaining = json.loads(eye.EYE_TOPICS_PATH.read_text())
        self.assertEqual([t["id"] for t in remaining], ["eye-test11"])

    def test_save_replaces_same_id(self):
        t1a, t1b = self._topic(21), self._topic(21)
        t1b["title_ar"] = "نسخة محدثة"
        eye.save_topic(t1a)
        eye.save_topic(t1b)
        q = json.loads(eye.EYE_TOPICS_PATH.read_text())
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]["title_ar"], "نسخة محدثة")


class TestFactoryTopic(unittest.TestCase):
    def test_to_factory_topic_complete(self):
        report = {
            "videoId": "abc123",
            "url": "https://youtu.be/abc123",
            "meta": {"title": "SPEED CHALLENGE", "channel": "Gadzhi",
                     "viewCount": 39000000},
        }
        dna = {"twist_or_payoff": "النتيجة آخر ثانية",
               "hook": {"technique": "shock"},
               "pacing": {"estimated_cuts_per_minute": 12},
               "retention_tricks": ["قطع كل ثانيتين"]}
        written = {
            "title_ar": "الكرة بترمي أسرع من أي حد في الدنيا!",
            "title_en": "Footballers throw discs faster than anyone!",
            "hook_ar": "تحذير: المشاهدة دي هتغير نظرتك للكرة!",
            "hook_en": "Warning: this changes how you see football!",
            "facts_ar": ["الفعل الأول", "الفعل التاني", "الفعل التالت"],
            "facts_en": ["one", "two", "three"],
            "takeaway_ar": {"aql": "عقل", "qalb": "قلب", "rouh": "روح"},
            "takeaway_en": {"aql": "mind", "qalb": "heart", "rouh": "soul"},
            "tags": "كرة,تحدي,ترند,دۅۄشے",
            "mood": "crazy",
            "visual_plan": [{"time": "0:00-0:03", "scene": "ستاد",
                             "style": "كاميرا سريعة", "colors": ["#0a3"]}],
        }
        t = eye.to_factory_topic(written, report, dna)
        self.assertEqual(t["id"], "eye-abc123")
        self.assertEqual(t["_kind"], "eye")
        self.assertEqual(t["_eye"]["videoId"], "abc123")
        self.assertEqual(len(t["facts_ar"]), 3)
        self.assertEqual(t["mood"], "crazy")
        # صالحة للمصنع: hook + facts + title
        self.assertTrue(t["hook_ar"] and t["facts_ar"] and t["title_ar"])

    def test_to_factory_topic_incomplete_raises(self):
        report = {"videoId": "x", "url": "u", "meta": {}}
        with self.assertRaises(RuntimeError):
            eye.to_factory_topic({"title_ar": "ع"}, report, {})


class TestDuration(unittest.TestCase):
    def test_iso_durations(self):
        self.assertEqual(eye._dur_secs("PT24S"), 24)
        self.assertEqual(eye._dur_secs("PT1M9S"), 69)
        self.assertEqual(eye._dur_secs("PT2M30S"), 150)
        self.assertEqual(eye._dur_secs("PT1H2M3S"), 3723)
        self.assertEqual(eye._dur_secs(""), 9999)
        self.assertEqual(eye._dur_secs(None), 9999)


class TestLLMAbsent(unittest.TestCase):
    def test_llm_call_fails_explicitly_without_key(self):
        from xtrendaw import settings
        orig = dict(settings.LLM)
        settings.LLM.update({"base": "", "key": ""})
        try:
            with self.assertRaises(RuntimeError):
                eye._llm("اختبار")
        finally:
            settings.LLM.clear()
            settings.LLM.update(orig)


if __name__ == "__main__":
    unittest.main(verbosity=2)
