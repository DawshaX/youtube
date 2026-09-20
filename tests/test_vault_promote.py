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


class VaultGuardTest(unittest.TestCase):
    """حراسة المخزون: مفيش حلقة بلا لقطات حية تتنشر.

    بق حقيقي (2026-09-20): حلقة تقليد IShowSpeed اتخزنت وهي كلها خلفيات
    مولّدة (صفر لقطة حية) وكانت هتتنشر أول ما الكوتة تفتح.
    """

    def test_pick_next_skips_zero_live(self):
        from xtrendaw import github_store as g
        entries = [
            {"name": "q100.mp4", "meta": {"live_clips": 0, "kind": "eye", "shots": 12}},
            {"name": "q200.mp4", "meta": {"live_clips": 4, "kind": "trend"}},
        ]
        self.assertEqual(g.pick_next(entries)["name"], "q200.mp4")

    def test_pick_next_prefers_replication(self):
        from xtrendaw import github_store as g
        entries = [
            {"name": "q100.mp4", "meta": {"live_clips": 3, "kind": "trend"}},
            {"name": "q300.mp4", "meta": {"live_clips": 6, "kind": "eye", "shots": 9}},
        ]
        self.assertEqual(g.pick_next(entries)["name"], "q300.mp4")

    def test_pick_next_unknown_meta_still_allowed(self):
        """حلقة قديمة بلا تسجيل ميديا (زي q1789834592) تتسمح عادي."""
        from xtrendaw import github_store as g
        entries = [{"name": "q100.mp4", "meta": {}},
                   {"name": "q050.mp4", "meta": {"credits": []}}]
        self.assertEqual(g.pick_next(entries)["name"], "q050.mp4")

    def test_pick_next_all_dead_returns_none(self):
        from xtrendaw import github_store as g
        self.assertIsNone(g.pick_next([{"name": "q1.mp4", "meta": {"live_clips": 0}}]))
        self.assertIsNone(g.pick_next([]))

    def test_dead_vault_assets_lists_only_zero_live(self):
        from xtrendaw import github_store as g
        dead = g.dead_vault_assets([
            {"name": "q1.mp4", "meta": {"live_clips": 0}},
            {"name": "q2.mp4", "meta": {"live_clips": 2}},
            {"name": "q3.mp4", "meta": {}},
        ])
        self.assertEqual([d["name"] for d in dead], ["q1.mp4"])

    def test_factory_records_live_clips_in_meta(self):
        import inspect
        from scripts import factory_loop
        src = inspect.getsource(factory_loop)
        self.assertIn('"live_clips": int(_ms.get("video") or 0)', src)

    def test_unverified_replication_is_skipped(self):
        """تقليد بشhots من غير إثبات لقطات حية = ما ينشرش (حماية إضافية)."""
        from xtrendaw import github_store as g
        entries = [
            {"name": "q100.mp4", "meta": {"kind": "eye", "shots": 12, "_eye": {}}},
            {"name": "q200.mp4", "meta": {"kind": "eye", "shots": 3, "live_clips": 7}},
        ]
        self.assertEqual(g.pick_next(entries)["name"], "q200.mp4")

    def test_old_episode_without_meta_field_still_ok(self):
        """حلقة قديمة (kind=eye بلا shots) مش تقليد ← تتسمح."""
        from xtrendaw import github_store as g
        e = [{"name": "q100.mp4", "meta": {"kind": "eye", "credits": []}}]
        self.assertEqual(g.pick_next(e)["name"], "q100.mp4")
