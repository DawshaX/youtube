"""اختبارات مكتبة العالم — أوفلاين (mock للـ HTTP).

تغطي: البحث بالرمز والاسم، شكل المخرجات، والتدهور الصريح عند الفشل.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xtrendaw import world  # noqa: E402

_EG = [{
    "name": "Egypt",
    "names": {"common": {"en": "Egypt"}},
    "capital": ["Cairo"],
    "population": 111_111_000,
    "languages": {"ar": "Arabic", "en": "English"},
    "currencies": {"EGP": {"name": "Egyptian pound", "symbol": "£"}},
    "region": "Africa",
    "subregion": "Northern Africa",
    "area": 1_002_450,
    "timezones": ["UTC+01:00"],
}]


class FakeResp:
    def __init__(self, data, code=200):
        self._data, self.code = data, code

    def raise_for_status(self):
        if self.code != 200:
            raise RuntimeError("HTTPError 404")

    def json(self):
        return self._data


class FakeReq:
    """mock لـ requests: يرصد الـ URL ويرجع Egypt."""
    last_url = None

    @staticmethod
    def get(url, headers=None, timeout=None):
        FakeReq.last_url = url
        return FakeResp(_EG)


class TestCountryInfo(unittest.TestCase):
    def test_iso_code_uses_alpha(self):
        with patch.object(world, "_req", return_value=FakeReq):
            info = world.country_info("EG")
        self.assertIn("/alpha/EG", FakeReq.last_url)
        self.assertEqual(info["name"], "Egypt")
        self.assertEqual(info["capital"], "Cairo")
        self.assertEqual(info["population"], 111_111_000)
        self.assertIn("Arabic", info["languages"])
        self.assertIn("Egyptian pound", info["currency"])

    def test_name_uses_name_endpoint(self):
        with patch.object(world, "_req", return_value=FakeReq):
            info = world.country_info("Japan")
        self.assertIn("/name/Japan", FakeReq.last_url)
        self.assertTrue(info)

    def test_empty_query(self):
        self.assertEqual(world.country_info(""), {})
        self.assertEqual(world.country_info(None), {})
        self.assertEqual(world.country_info("  "), {})

    def test_network_failure_degrades_to_empty(self):
        def boom(*a, **k):
            raise RuntimeError("no net")
        with patch.object(world, "_req", return_value=_raiser):
            self.assertEqual(world.country_info("EG"), {})

    def test_unknown_country_degrades_to_empty(self):
        class NotFoundReq:
            @staticmethod
            def get(url, headers=None, timeout=None):
                return FakeResp(None, code=404)
        with patch.object(world, "_req", return_value=NotFoundReq):
            self.assertEqual(world.country_info("XX"), {})

    def test_profile_line(self):
        with patch.object(world, "_req", return_value=FakeReq):
            line = world.profile_line(world.country_info("EG"))
        self.assertIn("Egypt", line)
        self.assertIn("Cairo", line)
        self.assertIn("111,111,000", line)
        self.assertEqual(world.profile_line({}), "")


# helper: requests يرمي استثناء
class _raiser:
    @staticmethod
    def get(*a, **k):
        raise RuntimeError("no net")


class TestDigestWorldSection(unittest.TestCase):
    """العين: قسم «الفيديو في العالم» بيظهر فقط عند وجود منطقة + بيانات."""

    def _report(self, region):
        return {
            "videoId": "X", "durationSeconds": 30.0,
            "meta": {"title": "T", "channel": "C", "region": region,
                     "viewCount": 1000, "likeCount": 10},
            "captions": [{"t": 0, "dur": 2, "text": "أهلاً"}],
            "scenes": [], "audioRmsPerSec": [],
        }

    def test_region_adds_world_section(self):
        with patch.object(world, "_req", return_value=FakeReq):
            from xtrendaw import eye
            d = eye.build_digest(self._report("EG"))
        self.assertIn("الفيديو في العالم", d)
        self.assertIn("Egypt", d)

    def test_no_region_no_section(self):
        from xtrendaw import eye
        d = eye.build_digest(self._report(None))
        self.assertNotIn("الفيديو في العالم", d)

    def test_world_failure_no_section(self):
        class DownReq:
            @staticmethod
            def get(*a, **k):
                raise RuntimeError("no net")
        with patch.object(world, "_req", return_value=DownReq):
            from xtrendaw import eye
            d = eye.build_digest(self._report("EG"))
        self.assertNotIn("الفيديو في العالم", d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
