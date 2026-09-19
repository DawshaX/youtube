import base64
import json
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
        payload = base64.b64encode(
            b"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t9999999999\tSID\tv1\n"
        ).decode()
        try:
            with mock.patch.dict(os.environ, {"YOUTUBE_COOKIES_B64": payload}, clear=False):
                header, path = eye._load_cookies()
            self.assertIsNotNone(path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertIn("SID=v1", header)
        finally:
            if eye._COOKIES_FILE:
                eye._COOKIES_FILE.unlink(missing_ok=True)
            eye._COOKIES_FILE = old


class CookieNormalizationTests(unittest.TestCase):
    """التشغيل الحقيقي 2026-09-19: السر كان base64 لسطر واحد بصيغة أزواج —
    والكود القديم كتبه زي ما هو، فـ yt-dlp رفضه ورجّع صفر كوكيز."""

    def _load(self, raw: str):
        """(header, path, نص الملف) — النص بيتقرأ قبل تنظيف الملف المؤقت."""
        old = eye._COOKIES_FILE
        eye._COOKIES_FILE = None
        try:
            with mock.patch.dict(os.environ, {"YOUTUBE_COOKIES_B64": raw}, clear=False):
                header, path = eye._load_cookies()
                text = path.read_text(encoding="utf-8") if path else ""
                return header, path, text
        finally:
            if eye._COOKIES_FILE:
                eye._COOKIES_FILE.unlink(missing_ok=True)
            eye._COOKIES_FILE = old

    def test_single_line_pairs_become_valid_netscape(self):
        raw = "SID=abc; HSID=def; VISITOR_INFO1_LIVE=ghi"
        header, path, text = self._load(raw)
        self.assertIsNotNone(path)
        self.assertTrue(text.startswith("# Netscape HTTP Cookie File"))
        self.assertEqual(len([l for l in text.splitlines() if l.count("\t") >= 6]), 6)
        self.assertIn("SID=abc", header)

    def test_base64_of_pairs_is_accepted_too(self):
        raw = base64.b64encode(b"SID=abc; HSID=def").decode()
        header, path, _ = self._load(raw)
        self.assertIsNotNone(path)
        self.assertIn("SID=abc", header)

    def test_json_export_is_accepted(self):
        raw = json.dumps([{"name": "SID", "value": "abc", "domain": ".youtube.com"}])
        header, path, _ = self._load(raw)
        self.assertIsNotNone(path)
        self.assertIn("SID=abc", header)

    def test_unreadable_secret_degrades_without_crashing(self):
        header, path, _ = self._load("!!!not-cookies!!!")
        self.assertEqual(header, "")
        self.assertIsNone(path)


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


class _Resp:
    def __init__(self, status, payload=None, text=""):
        self.status_code = status
        self._payload = payload or {}
        self.text = text
        self.ok = 200 <= status < 300

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code} {self.text[:60]}")


class _FakeHTTP:
    """محاكاة API حقيقي: موديل ميت بيرجّع 404 والموديل الشغال بيرجّع نص."""

    def __init__(self, live_models, dead_models, answer="تمام"):
        self.live, self.dead, self.answer = live_models, dead_models, answer
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        if url.endswith("/models"):
            return _Resp(200, {"data": [{"id": m} for m in self.live + self.dead]})
        return _Resp(404, {}, "unknown")

    def post(self, url, headers=None, json=None, timeout=None):
        model = (json or {}).get("model", "")
        self.calls.append(model)
        if model in self.dead:
            return _Resp(404, {"error": {"code": "model_not_found"}},
                         '{"error":"model_not_found"}')
        if model in self.live:
            return _Resp(200, {"choices": [{"message": {"content": self.answer}}]})
        if ":generateContent" in url:
            return _Resp(404, {}, "not found")
        return _Resp(404, {}, "not found")


class LLMChainTests(unittest.TestCase):
    """التشغيل 2026-09-19: llama-3.3-70b-versatile و gemini-2.0-flash بقوا 404
    والمفاتيح سليمة — فالسلامة لازم تكون في السلسلة نفسها، مش في الاسم."""

    def _patch(self, fake, env):
        return (mock.patch.object(eye, "_req", lambda: fake),
                mock.patch.dict(os.environ, env, clear=False))

    def test_dead_groq_model_falls_back_to_a_live_one(self):
        fake = _FakeHTTP(live_models=["openai/gpt-oss-120b"],
                         dead_models=["llama-3.3-70b-versatile"], answer="رد شغال")
        with mock.patch.object(eye, "_req", lambda: fake), \
             mock.patch.dict(eye.settings.LLM, {"base": "https://api.groq.com/openai/v1",
                                                "key": "k", "model": "llama-3.3-70b-versatile"}), \
             mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            out = eye._llm("قول تمام")
        self.assertEqual(out, "رد شغال")
        self.assertIn("llama-3.3-70b-versatile", fake.calls)
        self.assertIn("openai/gpt-oss-120b", fake.calls)
        self.assertLess(fake.calls.index("llama-3.3-70b-versatile"),
                        fake.calls.index("openai/gpt-oss-120b"))

    def test_gemini_fallback_uses_native_path_when_compat_fails(self):
        fake = _FakeHTTP(live_models=[], dead_models=["llama-3.3-70b-versatile"])
        native_calls = []

        class Fake2(_FakeHTTP):
            def post(self, url, headers=None, json=None, timeout=None):
                model = (json or {}).get("model", "")
                self.calls.append(model)
                if ":generateContent" in url:
                    native_calls.append(model)
                    return _Resp(200, {"candidates": [{"content": {"parts": [
                        {"text": "تمام"}]}}]})
                return _Resp(404, {}, "not found")

        fake2 = Fake2(live_models=[], dead_models=[])
        with mock.patch.object(eye, "_req", lambda: fake2), \
             mock.patch.dict(eye.settings.LLM, {"base": "https://api.groq.com/openai/v1",
                                                "key": "k", "model": "llama-3.3-70b-versatile"}), \
             mock.patch.dict(os.environ, {"GEMINI_API_KEY": "g"}, clear=False):
            out = eye._llm("قول تمام")
        self.assertEqual(out, "تمام")
        self.assertTrue(native_calls, "لازم المسار الأصلي لجوجل يكون اتجرّب")
        self.assertTrue(any("gemini" in c for c in fake2.calls))

    def test_everything_dead_fails_loudly_with_reason(self):
        fake = _FakeHTTP(live_models=[], dead_models=["openai/gpt-oss-120b"])
        with mock.patch.object(eye, "_req", lambda: fake), \
             mock.patch.dict(eye.settings.LLM, {"base": "https://api.groq.com/openai/v1",
                                                "key": "k", "model": "openai/gpt-oss-120b"}), \
             mock.patch.dict(os.environ, {"GEMINI_API_KEY": "g"}, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                eye._llm("قول تمام")
        self.assertIn("كل المزوّدين", str(ctx.exception))

    def test_probe_reports_the_working_provider(self):
        fake = _FakeHTTP(live_models=["openai/gpt-oss-120b"], dead_models=[])
        with mock.patch.object(eye, "_req", lambda: fake), \
             mock.patch.dict(eye.settings.LLM, {"base": "https://api.groq.com/openai/v1",
                                                "key": "k", "model": "openai/gpt-oss-120b"}), \
             mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            ok, detail = eye.llm_probe()
        self.assertTrue(ok)
        self.assertIn("openai/gpt-oss-120b", detail)
