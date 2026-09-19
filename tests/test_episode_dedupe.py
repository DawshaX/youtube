"""منع تكرار الوسائط جوه الحلقة الواحدة (شكوى 2026-09-19).

«حاطط الـ4 صور القديمة والمخزنة ومفيش أي جديد» + نفس الصورة ظهرت 4 مرات
في حلقة واحدة. العلاج: سجل جوه-الحلقة + رفض إعادة استخدام أي أصل.
"""
import unittest
import unittest.mock
from pathlib import Path
from tempfile import TemporaryDirectory

from xtrendaw import state


class EpisodeRegistryTest(unittest.TestCase):
    def setUp(self):
        state.episode_clear("eye-test")

    def test_mark_and_seen(self):
        self.assertFalse(state.episode_seen("eye-test", "http://x/1.jpg"))
        state.episode_mark("eye-test", "http://x/1.jpg")
        self.assertTrue(state.episode_seen("eye-test", "http://x/1.jpg"))
        self.assertFalse(state.episode_seen("eye-other", "http://x/1.jpg"))

    def test_empty_keys_are_noop(self):
        state.episode_mark("", "x")
        state.episode_mark("ep", "")
        self.assertFalse(state.episode_seen("ep", "x"))

    def test_registry_does_not_leak_forever(self):
        for i in range(260):
            state.episode_mark(f"ep{i}", f"u{i}")
        self.assertLessEqual(len(state._EP_USED), 200)


class CommonsNoRepeatTest(unittest.TestCase):
    """fetch_real_visual لازم يرفض إعادة استخدام صورة مستخدمة قبل كده.

    ⚠️ درس 2026-09-19: اختبار بيكتب في `state/media_used.json` الحقيقي = كارثة
    (دخل في كوميت ومسح 48 سجل). فكل تست هنا بيعزل الملف في مجلد مؤقت.
    """

    def setUp(self):
        from xtrendaw import state as _s
        self._tmp = TemporaryDirectory()
        self._old = _s.MEDIA_FILE
        _s.MEDIA_FILE = Path(self._tmp.name) / "media_used.json"

    def tearDown(self):
        from xtrendaw import state as _s
        _s.MEDIA_FILE = self._old
        self._tmp.cleanup()

    def _iso(self):
        """اعزل مكتبة «المستخدم قبل كده» — وإلا التشغيل التاني بيفشل."""
        from xtrendaw import library
        return (unittest.mock.patch.object(library, "_used", lambda q: set()),
                unittest.mock.patch.object(library, "_mark_used",
                                           lambda q, u: None))

    def _fake_search(self, pages):
        class R:
            ok = True

            @staticmethod
            def json():
                return {"query": {"pages": {
                    str(i): p for i, p in enumerate(pages)}}}

        return unittest.mock.patch("requests.get", lambda *a, **k: R())

    def test_all_used_returns_false_instead_of_repeating(self):
        from xtrendaw import scenes
        pages = [{"title": "File:a.jpg",
                  "imageinfo": [{"mime": "image/jpeg", "width": 1200,
                                 "thumburl": "http://c/a.jpg"}]},
                 {"title": "File:b.jpg",
                  "imageinfo": [{"mime": "image/jpeg", "width": 1200,
                                 "thumburl": "http://c/b.jpg"}]}]
        used = {"http://c/a.jpg": {"source": "image:commons"},
                "http://c/b.jpg": {"source": "image:commons"}}
        with TemporaryDirectory() as d:
            out = Path(d) / "base.png"
            a, b = self._iso()
            with a, b, unittest.mock.patch.object(state, "media_used",
                                                  lambda: used), \
                 self._fake_search(pages):
                self.assertFalse(scenes.fetch_real_visual("q", out,
                                                          episode="eye-x"))
            # ونفس الحاجة للصور المستخدمة جوه نفس الحلقة
            a, b = self._iso()
            with a, b, unittest.mock.patch.object(state, "media_used",
                                                  lambda: {}), \
                 unittest.mock.patch.object(state, "episode_seen",
                                            lambda ep, u: True), \
                 self._fake_search(pages):
                self.assertFalse(scenes.fetch_real_visual("q", out,
                                                          episode="eye-x"))

    def test_fresh_candidate_is_accepted(self):
        from xtrendaw import scenes
        pages = [{"title": "File:fresh.jpg",
                  "imageinfo": [{"mime": "image/jpeg", "width": 1200,
                                 "thumburl": "http://c/fresh.jpg"}]}]
        img = _png_bytes()

        class Resp:
            ok = True
            content = img

            def json(self):
                return {"query": {"pages": {
                    "1": {"title": "File:fresh.jpg",
                          "imageinfo": [{"mime": "image/jpeg",
                                         "width": 1200,
                                         "thumburl": "http://c/fresh.jpg"}]}}}}

        def fake_get(url, *a, **k):
            return Resp()
        with TemporaryDirectory() as d:
            out = Path(d) / "base.png"
            a, b = self._iso()
            with a, b, unittest.mock.patch.object(state, "media_used",
                                                  lambda: {}), \
                 unittest.mock.patch("requests.get", fake_get):
                self.assertTrue(scenes.fetch_real_visual("q", out,
                                                         episode="eye-x"))
                self.assertTrue(out.exists())


def _png_bytes():
    from io import BytesIO
    from PIL import Image
    import random
    img = Image.new("RGB", (1100, 1600))
    px = img.load()
    for y in range(0, 1600, 7):
        for x in range(0, 1100, 7):
            px[x, y] = (random.randint(0, 200), random.randint(0, 200),
                        random.randint(0, 200))
    b = BytesIO()
    img.save(b, "JPEG")
    return b.getvalue()


if __name__ == "__main__":
    unittest.main()


class MediaFileIsolationTest(unittest.TestCase):
    """حارس: الاختبارات ما تكتبش في ملف ذاكرة الميديا الحقيقي.

    الدرس: اختبار دخل كوميت بـ`state/media_used.json` فيه سجل واحد بس
    (48 → 1) — يعني الذاكرة رجعت لورا واللقطات بقت تتكرر.
    """

    def test_paths_are_patchable_and_default_is_repo_state(self):
        from xtrendaw import state
        self.assertTrue(str(state.MEDIA_FILE).endswith("media_used.json"))
        self.assertIn("state", str(state.MEDIA_FILE))

    def test_mark_media_used_writes_to_patched_file(self):
        from xtrendaw import state
        with TemporaryDirectory() as d:
            tmp = Path(d) / "m.json"
            old = state.MEDIA_FILE
            try:
                state.MEDIA_FILE = tmp
                state.mark_media_used("http://x/1", "video:pixabay", "ep1")
                self.assertIn("http://x/1", state.media_used())
                self.assertTrue(state.media_seen("http://x/1"))
            finally:
                state.MEDIA_FILE = old


class ProducedTopicGuardTest(unittest.TestCase):
    """حلقة المارشميلو طلعت مرتين — الحارس: المعرّف مش العنوان."""

    def test_produced_ids_reads_repo_state(self):
        from xtrendaw import state
        ids = state.produced_ids()
        self.assertIsInstance(ids, set)
        self.assertIn("eye-JPbWXvyaCcw", ids)   # اتعملت فعلًا على القناة

    def test_brain_rejects_already_produced_id(self):
        from xtrendaw import brain
        cand = {"id": "eye-JPbWXvyaCcw", "title_ar": "عنوان جديد خالص",
                "angle": "ترند", "facts_ar": ["حقيقة"]}
        self.assertFalse(brain._candidate_is_fresh(cand))

    def test_brain_accepts_new_id(self):
        from xtrendaw import brain
        cand = {"id": "eye-جديد-123", "title_ar": "موضوع جديد",
                "angle": "ترند", "facts_ar": ["حقيقة"]}
        self.assertTrue(brain._candidate_is_fresh(cand))
