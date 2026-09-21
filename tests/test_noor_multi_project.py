"""حرّاس ميزة «النشرة كل ساعة»: تناوب مشاريع جوجل والحصة المتضاعفة.

المبدأ: يوتيوب بيدي 10,000 وحدة/يوم **لكل مشروع جوجل** (الرفعة 1,600) يعني
6 رفعات لكل مشروع. لو صاحب القناة ضاف مشاريع إضافية، المصنع لازم:
  1) يكتشفهم من الأسماء المرقّمة (YOUTUBE_CLIENT_ID_2 … _8)
  2) يوسّع السقف اليومي = 6 × عدد المشاريع
  3) يوسّع مواعيد النشر (24 مشروع×6 = نشرة كل ساعة)
"""
import importlib
import unittest
from unittest import mock

from xtrendaw import settings


def _reload_with(env: dict):
    with mock.patch.dict("os.environ", env, clear=False):
        importlib.reload(settings)
        return settings


class TestMultiProject(unittest.TestCase):
    BASE = {"YOUTUBE_CLIENT_ID": "a", "YOUTUBE_CLIENT_SECRET": "b",
            "YOUTUBE_REFRESH_TOKEN": "c"}

    def tearDown(self) -> None:
        importlib.reload(settings)

    def test_single_project_is_the_default(self) -> None:
        s = _reload_with({**self.BASE, "YOUTUBE_CLIENT_ID_2": "",
                          "YOUTUBE_REFRESH_TOKEN_2": ""})
        self.assertGreaterEqual(len(s.YOUTUBE_ACCOUNTS), 1)
        self.assertEqual(s.YOUTUBE_DAILY_CAPACITY, 6 * len(s.YOUTUBE_ACCOUNTS))

    def test_extra_projects_are_detected_and_capacity_doubles(self) -> None:
        env = dict(self.BASE)
        for i in (2, 3, 4):
            env[f"YOUTUBE_CLIENT_ID_{i}"] = f"id{i}"
            env[f"YOUTUBE_CLIENT_SECRET_{i}"] = f"sec{i}"
            env[f"YOUTUBE_REFRESH_TOKEN_{i}"] = f"tok{i}"
        s = _reload_with(env)
        self.assertEqual(len(s.YOUTUBE_ACCOUNTS), 4)
        self.assertEqual(s.YOUTUBE_DAILY_CAPACITY, 24)     # نشرة كل ساعة
        self.assertEqual(s.DAILY_CAP, s.DAILY_CAP_BASE * 4)

    def test_partial_project_is_ignored(self) -> None:
        env = dict(self.BASE)
        env["YOUTUBE_CLIENT_ID_2"] = "id2"      # من غير سرّ ولا توكن
        s = _reload_with(env)
        self.assertEqual(len(s.YOUTUBE_ACCOUNTS), 1,
                         "مشروع ناقص ما يتحسبش — لازم المعرّف والسرّ والتوكن")

    def test_slots_expand_with_capacity(self) -> None:
        import scripts.noor_runner as R
        with mock.patch.object(settings, "YOUTUBE_DAILY_CAPACITY", 24):
            self.assertEqual(len(R._slots()), 24)          # كل ساعة
        with mock.patch.object(settings, "YOUTUBE_DAILY_CAPACITY", 12):
            self.assertEqual(len(R._slots()), 12)          # كل ساعتين
        with mock.patch.object(settings, "YOUTUBE_DAILY_CAPACITY", 6):
            self.assertEqual(R._slots(), [5, 9, 13, 16, 19, 22])


if __name__ == "__main__":
    unittest.main()
