"""حرّاس تناوب الرفع بين مشاريع جوجل — بمحاكاة كاملة لردود يوتيوب.

السيناريوهات:
  1) مشروع أساسي حصته خلصت → الرفع ينقل للمشروع التالي تلقائيًا.
  2) كل المشاريع حصتها خلصت → يرجّع quota_exceeded (والمصنع يخزّن بدل ما يضيّع).
  3) مشروع واحد بس ورد 500 → يرجّع init_500 (مفيش تناوب غلط).
"""
import pathlib
import tempfile
import unittest
from unittest import mock

from xtrendaw.publish import youtube as yt


ACC1 = {"client_id": "i1", "client_secret": "s1", "refresh_token": "r1",
        "label": "الأساسي"}
ACC2 = {"client_id": "i2", "client_secret": "s2", "refresh_token": "r2",
        "label": "مشروع 2"}


class _Resp:
    def __init__(self, status, payload=None, location="https://up.example/x"):
        self.status_code = status
        self._p = payload or {}
        self.headers = {"Location": location}

    def json(self):
        return self._p

    @property
    def ok(self):
        return 200 <= self.status_code < 300


def _quota() -> _Resp:
    return _Resp(403, {"error": {"errors": [{"reason": "quotaExceeded"}]}})


def _ok() -> _Resp:
    return _Resp(200, {"id": "VID123"})


class RotationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp()) / "v.mp4"
        self.tmp.write_bytes(b"x" * 10)

    def _call(self, accounts, posts, puts):
        calls = {"n": 0}

        def post(*a, **k):
            i = calls["n"]
            calls["n"] += 1
            return posts[min(i, len(posts) - 1)]

        def put(*a, **k):
            return puts[0]

        with mock.patch.object(yt.settings, "has_youtube", lambda: True), \
             mock.patch.object(yt.settings, "YOUTUBE_ACCOUNTS", accounts), \
             mock.patch.object(yt, "_token", lambda *a, **k: "tok"), \
             mock.patch.object(yt.requests, "post", post), \
             mock.patch.object(yt.requests, "put", put):
            out = yt.publish(self.tmp, "عنوان", "وصف", ["وسم"])
        return out, calls["n"]

    def test_first_project_exhausted_moves_to_second(self) -> None:
        (url, err), n = self._call([ACC1, ACC2], [_quota(), _ok()], [_ok()])
        self.assertIsNone(err)
        self.assertIn("VID123", url)
        self.assertEqual(n, 2, "لازم يجرّب المشروع التاني بعد ما الأول حصته خلصت")

    def test_all_projects_exhausted_reports_quota(self) -> None:
        url, n = self._call([ACC1, ACC2], [_quota(), _quota()], [_ok()])
        self.assertIsNone(url[0])
        self.assertEqual(url[1], "quota_exceeded")
        self.assertEqual(n, 2)

    def test_single_project_server_error_has_no_fake_fallback(self) -> None:
        url, n = self._call([ACC1], [_Resp(500, {})], [_ok()])
        self.assertIsNone(url[0])
        self.assertEqual(url[1], "init_500")
        self.assertEqual(n, 1)


if __name__ == "__main__":
    unittest.main()
