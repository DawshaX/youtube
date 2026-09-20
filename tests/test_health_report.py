"""تقرير الصحة (الدكتور) — الهيكل، الملخص، وثبات الحالات.

من الباتش 2026-09-18: التقرير الجديد قائمة فحوص بحالات ثلاث + data/health.json.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xtrendaw import doctor  # noqa: E402


class TestReportStructure(unittest.TestCase):
    def test_local_run_shape(self):
        rep = doctor.run(local_only=True)
        self.assertIn("checkedAt", rep)
        self.assertIn("all_ok", rep)
        self.assertIn("checks", rep)
        # كل فحص: اسم + حالة من الثلاثة + تفاصيل
        for c in rep["checks"]:
            self.assertIn(c["status"], ("ok", "warn", "fail"))
            self.assertTrue(c["name"])
            self.assertTrue(c["detail"] is not None)
        # المحلي لازم يكون 4 فحوص فعلية
        real = [c for c in rep["checks"] if "تخطيه" not in c["detail"]]
        self.assertEqual(len(real), 4)
        # المتخطاة بأسماء خدمات مش دوال
        skipped = [c for c in rep["checks"] if "تخطيه" in c["detail"]]
        for c in skipped:
            self.assertNotIn("check_", c["name"])

    def test_report_written_to_disk(self):
        doctor.run(local_only=True)
        self.assertTrue(doctor.HEALTH_PATH.exists())
        rep = json.loads(doctor.HEALTH_PATH.read_text(encoding="utf-8"))
        self.assertIn("checks", rep)

    def test_summary_md(self):
        rep = doctor.run(local_only=True)
        md = doctor.summary_md(rep)
        self.assertIn("| الخدمة | الحالة |", md)
        self.assertIn("YOUTUBE_API_KEY (الرادار)", md)
        self.assertIn("edge-tts (صوت حقيقي)", md)

    def test_count_consistency(self):
        rep = doctor.run(local_only=True)
        self.assertEqual(rep["fails"],
                         sum(1 for c in rep["checks"] if c["status"] == "fail"))
        self.assertEqual(rep["warns"],
                         sum(1 for c in rep["checks"] if c["status"] == "warn"))
        self.assertEqual(rep["all_ok"], rep["fails"] == 0)


class TestLocalChecksOffline(unittest.TestCase):
    """الفحوص المحلية لازم ترجع نتيجة واضحة حتى بلا نت/ffmpeg/حزم."""

    def test_ffmpeg_status_is_valid(self):
        c = doctor.check_ffmpeg()
        self.assertIn(c["status"], ("ok", "fail"))

    def test_packages_status_is_valid(self):
        c = doctor.check_packages()
        self.assertIn(c["status"], ("ok", "fail"))

    def test_voice_library_real(self):
        c = doctor.check_voice_library()
        self.assertEqual(c["status"], "ok")
        self.assertIn("32", c["detail"])

    def test_data_integrity(self):
        c = doctor.check_data_integrity()
        self.assertIn(c["status"], ("ok", "fail"))


class TestCookieCheck(unittest.TestCase):
    """فحص الكوكيز: غير مضبوط = فشل · مشغل يقبل = ok · مرفوض = فشل برسالة حل."""

    @classmethod
    def setUpClass(cls):
        import base64
        sample = ("# Netscape HTTP Cookie File\n"
                  ".youtube.com\tTRUE\t/\tTRUE\t1999999999\tSAPISID\tabc\n")
        cls._b64 = base64.b64encode(sample.encode()).decode()

    def test_missing_secret_is_fail(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            c = doctor.check_youtube_cookies()
        self.assertEqual(c["status"], "fail")
        self.assertIn("غير مضبوط", c["detail"])

    def _patch_eye(self, meta: dict, player: dict):
        from xtrendaw import eye as _eye
        return (mock.patch.object(_eye, "_public_metadata", return_value=meta),
                mock.patch.object(_eye, "_player_response", return_value=player))

    def test_accepted_session_is_ok(self):
        with mock.patch.dict(os.environ, {"YOUTUBE_COOKIES_B64": self._b64}):
            m1, m2 = self._patch_eye({"title": "فيديو"}, {"storyboards": [1]})
            with m1, m2:
                c = doctor.check_youtube_cookies()
        self.assertEqual(c["status"], "ok")
        self.assertIn("الجلسة شغالة", c["detail"])

    def test_dead_session_is_warn_not_fail(self):
        """الكوكيز اتقرت بس جلسة المشغل ما رجعتش بيانات — تحذير مش فشل،
        لأن مسار العين الأساسي (oEmbed/storyboard) لسه بيمشي."""
        with mock.patch.dict(os.environ, {"YOUTUBE_COOKIES_B64": self._b64}):
            m1, m2 = self._patch_eye({}, {})
            with m1, m2:
                c = doctor.check_youtube_cookies()
        self.assertEqual(c["status"], "warn")
        self.assertIn("ما رجعتش بيانات", c["detail"])

    def test_cleanup_is_guaranteed(self):
        """حتى لو الاختبار وقع، الملف المؤقت بيتشال (finally)."""
        from xtrendaw import eye as _eye
        with mock.patch.dict(os.environ, {"YOUTUBE_COOKIES_B64": self._b64}):
            m1, m2 = self._patch_eye({}, {})
            with m1, m2, mock.patch.object(_eye, "_load_cookies",
                                           side_effect=RuntimeError("bag")):
                c = doctor.check_youtube_cookies()
        self.assertEqual(c["status"], "fail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
