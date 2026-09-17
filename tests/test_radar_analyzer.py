"""اختبار المحلل على بيانات تركيبية — بلا شبكة، بلا مفاتيح.

بيثبت إن `patterns.json` بيتحسب صح (السرعة، معدل الإعجاب، بنية العناوين)
وإن الرادار بيفشل صريحًا من غير مفتاح بدل ما يخترع بيانات.
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class TestAnalyzer(unittest.TestCase):
    def test_patterns_from_synthetic_snapshot(self):
        from xtrendaw import analyzer, settings  # noqa: F401
        now = dt.datetime.now(dt.timezone.utc)
        pub = (now - dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        snap = {
            "scannedAt": now.isoformat(timespec="seconds"),
            "regions": ["EG"],
            "videos": [
                {"videoId": "a" * 11, "region": "EG", "via": "mostPopular",
                 "title": "لن تصدق ماذا حدث! 3 حقائق 🤯", "channel": "X",
                 "publishedAt": pub, "categoryId": "22",
                 "duration": "PT1M", "viewCount": 1_000_000, "likeCount": 50_000},
                {"videoId": "b" * 11, "region": "EG", "via": "search:حقائق",
                 "title": "معلومة هادئة عن البحر", "channel": "Y",
                 "publishedAt": pub, "categoryId": "27",
                 "duration": "PT2M", "viewCount": 10_000, "likeCount": 100},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            snap_path = pathlib.Path(tmp) / "radar_snapshot.json"
            pat_path = pathlib.Path(tmp) / "patterns.json"
            snap_path.write_text(json.dumps(snap, ensure_ascii=False),
                                 encoding="utf-8")
            old_snap, old_pat = analyzer.SNAPSHOT_PATH, analyzer.PATTERNS_PATH
            analyzer.SNAPSHOT_PATH, analyzer.PATTERNS_PATH = snap_path, pat_path
            try:
                p = analyzer.analyze()
            finally:
                analyzer.SNAPSHOT_PATH, analyzer.PATTERNS_PATH = old_snap, old_pat

        self.assertEqual(p["videoCount"], 2)
        self.assertEqual(p["fastest"][0]["videoId"], "a" * 11)
        # 1M مشاهدة في 10 ساعات ≈ 100 ألف/ساعة
        self.assertAlmostEqual(p["fastest"][0]["velocityPerHour"], 100_000,
                               delta=5_000)
        self.assertEqual(p["fastest"][0]["likeRatePer1k"], 50.0)
        tp = p["titlePatterns"]
        self.assertEqual(tp["questionRate"], 0.0)
        self.assertEqual(tp["numberRate"], 0.5)
        self.assertEqual(tp["emojiRate"], 0.5)
        self.assertIn("22", p["categoryShare"])

    def test_radar_fails_loud_without_key(self):
        env = dict(os.environ)
        env.pop("YOUTUBE_API_KEY", None)
        env["PYTHONPATH"] = str(ROOT)
        r = subprocess.run([sys.executable, "-m", "xtrendaw.radar"],
                           env=env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 2)
        self.assertIn("YOUTUBE_API_KEY", r.stderr)

    def test_analyzer_fails_loud_without_snapshot(self):
        from xtrendaw import analyzer
        with tempfile.TemporaryDirectory() as tmp:
            old = analyzer.SNAPSHOT_PATH
            analyzer.SNAPSHOT_PATH = pathlib.Path(tmp) / "nope.json"
            try:
                with self.assertRaises(RuntimeError):
                    analyzer.analyze()
            finally:
                analyzer.SNAPSHOT_PATH = old


if __name__ == "__main__":
    unittest.main()
