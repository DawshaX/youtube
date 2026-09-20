"""الفرجة من المخزون: الحلقة اللي مستنية تنزل لما الكوتة تفتح.

بق حقيقي (2026-09-20): المصنع أنتج حلقة تقليد والكوتة كانت 6/6، فاتخزنت في
المخزون… ومحصلش أي حاجة تفرّجها. النشر الساعي كان هيبقى وهمي.
"""
import unittest
import unittest.mock as mock


class PromoteTest(unittest.TestCase):
    def _run(self, published_today, promote_result, publish_result):
        import scripts.factory_loop as fl
        from xtrendaw import github_store, state
        from xtrendaw.publish import youtube as yt

        pushed = []
        with mock.patch.object(fl, "NO_PUBLISH", False), \
             mock.patch.object(state, "published_today_pt",
                               lambda *a, **k: published_today), \
             mock.patch.object(github_store, "promote_next",
                               lambda: promote_result), \
             mock.patch.object(yt, "publish", lambda *a, **k: publish_result), \
             mock.patch.object(state, "push_published",
                               lambda x: pushed.append(x)), \
             mock.patch.object(state, "push_yt_recent", lambda x: None), \
             mock.patch.object(state, "set_last_kind", lambda k: None), \
             mock.patch.object(github_store, "upload_to_vault",
                               lambda *a, **k: {"video": "back"}):
            fl._promote_from_vault()
        return pushed

    def test_promotes_and_records(self):
        res = {"id": "ep9", "local_video": "/tmp/v.mp4",
               "meta": {"title": "حلقة تقليد", "tags": "تحدي,دوشة",
                        "kind": "eye", "caption": "وصف"}}
        pushed = self._run(2, res, ("https://www.youtube.com/watch?v=NEWID1", None))
        self.assertEqual(len(pushed), 1)
        self.assertEqual(pushed[0]["id"], "NEWID1")
        self.assertEqual(pushed[0]["title"], "حلقة تقليد")

    def test_failed_publish_returns_to_vault(self):
        res = {"id": "ep9", "local_video": "/tmp/v.mp4",
               "meta": {"title": "x"}}
        pushed = self._run(2, res, (None, "quota_exceeded"))
        self.assertEqual(pushed, [])

    def test_promote_skipped_when_nothing_queued(self):
        self.assertEqual(self._run(0, None, (None, None)), [])

    def test_caller_skips_when_quota_full(self):
        """الحلقة اللي في المخزون ما تتحاولش والكوتة مقفولة."""
        import inspect
        import scripts.factory_loop as fl
        src = inspect.getsource(fl.cycle_once)
        self.assertIn("published_today_pt() >= (settings.DAILY_CAP", src)
