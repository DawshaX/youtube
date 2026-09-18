import base64
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from xtrendaw import doctor, eye, footage, vault


class DoctorSafetyTests(unittest.TestCase):
    def test_missing_secrets_fail_closed(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            report = doctor.run()
        self.assertEqual(set(report), set(doctor.REQUIRED))
        self.assertTrue(all(not item["ok"] for item in report.values()))

    def test_eye_cookie_file_is_0600_and_cleanup_registered(self):
        old = eye._COOKIES_FILE
        eye._COOKIES_FILE = None
        payload = base64.b64encode(b"# Netscape HTTP Cookie File\n").decode()
        try:
            with mock.patch.dict(os.environ, {"YOUTUBE_COOKIES_B64": payload}, clear=False):
                _, path = eye._load_cookies()
            self.assertIsNotNone(path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        finally:
            if eye._COOKIES_FILE:
                eye._COOKIES_FILE.unlink(missing_ok=True)
            eye._COOKIES_FILE = old


class WorldPolicyTests(unittest.TestCase):
    def test_network_is_on_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(footage.net_footage_enabled())

    def test_network_license_allowlist_is_strict(self):
        self.assertEqual(vault.ALLOWED_NETWORK_LICENSES,
                         {"CC0", "CC-BY-3.0", "CC-BY-4.0"})
        for forbidden in ("CC-BY-SA-4.0", "Public-Domain", "Pixabay-License",
                          "Pexels-License", "NASA-Media-Usage"):
            self.assertNotIn(forbidden, vault.ALLOWED_NETWORK_LICENSES)


if __name__ == "__main__":
    unittest.main()
