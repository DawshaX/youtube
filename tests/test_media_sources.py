"""اختبارات طبقات المصادر الجديدة — بلا شبكة.

بتثبت إن فلاتر التراخيص حاكمة فعلًا (اللي مش مسموح بيترفض)،
وإن خلط المؤثرات على الموسيقى بيشتغل، وإن الأسرار بأسمائها المختصرة
بتتقرا صح من البيئة.
"""
import pathlib
import subprocess
import sys
import unittest

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _tone_wav(path: pathlib.Path, seconds: float, freq: float = 440.0):
    import wave
    sr = 22050
    t = np.linspace(0, seconds, int(seconds * sr), endpoint=False)
    data = (0.3 * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


class TestLicenseGates(unittest.TestCase):
    def test_freesound_license_gate(self):
        from xtrendaw import sfx
        self.assertEqual(sfx.license_ok("Creative Commons 0"), ("CC0", False))
        self.assertEqual(sfx.license_ok("Attribution"), ("CC-BY-4.0", True))
        # التجاري غير مقبول عندنا — القناة قابلة للتربح
        self.assertIsNone(sfx.license_ok("Attribution NonCommercial"))
        self.assertIsNone(sfx.license_ok(""))
        self.assertIsNone(sfx.license_ok("All Rights Reserved"))

    def test_openverse_license_map(self):
        from xtrendaw import imagery
        self.assertIn("cc0", imagery._OPENVERSE_LIC)
        self.assertIn("by", imagery._OPENVERSE_LIC)
        self.assertIn("publicdomain", imagery._OPENVERSE_LIC)
        self.assertNotIn("by-nc", imagery._OPENVERSE_LIC)
        self.assertNotIn("by-nd", imagery._OPENVERSE_LIC)

    def test_openverse_and_commons_maps_are_allowed_by_vault(self):
        from xtrendaw import imagery, vault
        for lic, _ in imagery._OPENVERSE_LIC.values():
            self.assertIn(lic, vault.ALLOWED_LICENSES)
        for lic in ("CC0", "CC-BY-4.0", "CC-BY-3.0", "Public-Domain"):
            self.assertIn(lic, vault.ALLOWED_LICENSES)

    def test_secret_name_fallbacks(self):
        import os
        env = dict(os.environ)
        env.pop("PEXELS_API_KEY", None)
        env.pop("NASA_API_KEY", None)
        env.pop("OPENVERSE_API_KEY", None)
        env["PEXELS"] = "px-test"
        env["NASA"] = "nasa-test"
        env["OPENVERSE"] = "ov-test"
        env["PYTHONPATH"] = str(ROOT)
        code = ("import xtrendaw.settings as s; "
                "assert s.PEXELS_API_KEY == 'px-test'; "
                "assert s.NASA_API_KEY == 'nasa-test'; "
                "assert s.OPENVERSE_API_KEY == 'ov-test'; "
                "print('fallbacks ok')")
        r = subprocess.run([sys.executable, "-c", code], env=env,
                           capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fallbacks ok", r.stdout)


class TestSfxMixer(unittest.TestCase):
    def test_mix_events_produces_track(self):
        import tempfile
        from xtrendaw.produce import _mix_sfx_events
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            music = tmp / "music.wav"
            whoosh = tmp / "whoosh.wav"
            impact = tmp / "impact.wav"
            _tone_wav(music, 4.0, 220)
            _tone_wav(whoosh, 0.5, 880)
            _tone_wav(impact, 0.5, 110)
            out = _mix_sfx_events(music, [(0.2, whoosh), (2.0, impact)],
                                  4.0, tmp / "mixed.wav")
            self.assertIsNotNone(out)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 30_000)


if __name__ == "__main__":
    unittest.main()
