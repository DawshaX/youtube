"""اختبارات عدّاد كوتة يوتيوب (يوم PT) + تمييز quotaExceeded.

الدرس (2026-09-19): كنا بنعدّ 24 ساعة متحركة فالحارس قفل النشر وإحنا
لسه عندنا حصة فعلية النهاردة — ويوتيوب بيرجّع الحصة 12 بالليل PT.
"""
import pathlib
import tempfile
import time
import unittest
import unittest.mock
from datetime import datetime, timezone

from xtrendaw import state


def _ts_utc(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc).timestamp()


class QuotaDayTest(unittest.TestCase):
    def test_pt_day_start_is_07_utc_in_summer(self):
        start = state._pt_day_start(_ts_utc(2026, 9, 19, 18, 0))  # صيف: PT=UTC-7
        got = datetime.fromtimestamp(start, timezone.utc)
        self.assertEqual((got.day, got.hour, got.minute), (19, 7, 0))

    def test_yesterday_pt_not_counted_today(self):
        now = _ts_utc(2026, 9, 19, 18, 0)
        old = _ts_utc(2026, 9, 19, 5, 0)      # 22:00 PT امبارح
        fresh = _ts_utc(2026, 9, 19, 9, 5)    # 02:05 PT النهاردة
        log = [{"ts": old}, {"ts": fresh}]
        with unittest.mock.patch.object(state, "published_log", lambda: log):
            self.assertEqual(state.published_today_pt(now), 1)
            self.assertEqual(state.published_last_24h(now), 2)

    def test_new_pt_day_frees_quota(self):
        """الحالة اللي قفلت النشر: 6 رفعات في آخر 24س، بس يوم PT جديد."""
        now = _ts_utc(2026, 9, 19, 18, 0)
        log = [{"ts": _ts_utc(2026, 9, 19, t, 0)} for t in (4, 5)]
        with unittest.mock.patch.object(state, "published_log", lambda: log):
            self.assertEqual(state.published_today_pt(now), 0)
            self.assertEqual(state.published_last_24h(now), 2)

    def test_broken_records_ignored(self):
        now = time.time()
        log = [{"ts": str(now)}, {"ts": None}, {"ts": "خربان"}, {}]
        with unittest.mock.patch.object(state, "published_log", lambda: log):
            self.assertEqual(state.published_today_pt(now), 1)


class UploaderQuotaTest(unittest.TestCase):
    def _publish(self, status, payload, ok=False):
        from xtrendaw.publish import youtube as yt

        class R:
            def __init__(s):
                s.status_code, s.headers, s.ok = status, {}, ok

            def json(s):
                return payload

        tmp = pathlib.Path(tempfile.mkdtemp()) / "v.mp4"
        tmp.write_bytes(b"x")
        with unittest.mock.patch.object(yt.settings, "has_youtube", lambda: True), \
             unittest.mock.patch.object(yt, "_token", lambda *a, **k: "tok"), \
             unittest.mock.patch.object(yt.requests, "post", lambda *a, **k: R()):
            return yt.publish(tmp, "عنوان", "وصف", ["وسم"])

    def test_quota_403_is_named(self):
        url, err = self._publish(403, {"error": {"errors": [{"reason": "quotaExceeded"}]}})
        self.assertIsNone(url)
        self.assertEqual(err, "quota_exceeded")

    def test_auth_403_is_not_called_quota(self):
        url, err = self._publish(403, {"error": {"errors": [{"reason": "forbidden"}]}})
        self.assertEqual(err, "auth_403")

    def test_other_error_keeps_status_code(self):
        url, err = self._publish(500, {})
        self.assertEqual(err, "init_500")


if __name__ == "__main__":
    unittest.main()
