"""⏱️ اختبارات فهرس الجلسة (chapters) — الفيديو الطويل.

بيحرس قواعد يوتيوب الصريحة + قاعدة الأمانة (مفيش فصل ملفّق):
  • أول فصل 00:00 دايمًا
  • ٣ فصول على الأقل، وكل فصل مباعد عن اللي قبله
  • الوقت بيتحسب من **المدة المقيسة الحقيقية** مش من تخمين
  • لو الإشارات ناقصة ⇒ مفيش فهرس خالص (مش فهرس غلط)
"""
import unittest

from xtrendaw.noor_next.chapters import chapter_lines, block


class ChapterTests(unittest.TestCase):
    def test_real_session_ten_minutes(self):
        hint = [{"at_word": 0, "label": "البداية"},
                {"at_word": 150, "label": "المال"},
                {"at_word": 320, "label": "الرزق"},
                {"at_word": 500, "label": "التجربة"},
                {"at_word": 700, "label": "البناء"},
                {"at_word": 900, "label": "التدوير"}]
        got = chapter_lines(hint, 1180, 630)
        self.assertTrue(got)
        self.assertTrue(got[0].startswith("00:00"), got)
        self.assertGreaterEqual(len(got), 3)
        self.assertTrue(all(":" in line for line in got))
        # الترتيب تصاعدي (شرط يوتيوب لعرض الفصول)
        stamps = [int(l.split(" ")[0].split(":")[0]) * 60 + int(l.split(" ")[0].split(":")[1])
                  for l in got]
        self.assertEqual(stamps, sorted(stamps))
        self.assertGreaterEqual(stamps[-1], 10)          # مش كله في أول ثانية

    def test_no_fake_chapters(self):
        # إشارات واحدة ⇒ مفيش فهرس (أحسن من فهرس كاذب)
        self.assertEqual(chapter_lines([{"at_word": 5, "label": "x"}], 1180, 630), [])
        # مفيش مدة أو مفيش كلام ⇒ مفيش فهرس
        self.assertEqual(chapter_lines([{"at_word": 5, "label": "x"}], 0, 630), [])
        self.assertEqual(chapter_lines([{"at_word": 5, "label": "x"}], 1180, 0), [])
        self.assertEqual(chapter_lines(None, 1180, 630), [])

    def test_short_long_gets_no_chapters(self):
        # جلسة ٣ دقايق (١٨٠ث) والفصول كلها في آخر ١٠ ثواني ⇒ مرفوضة
        hint = [{"at_word": 300, "label": "أ"}, {"at_word": 320, "label": "ب"},
                {"at_word": 340, "label": "ج"}]
        self.assertEqual(chapter_lines(hint, 350, 180), [])

    def test_duration_scales_time(self):
        # نفس الكلمات بمدة أكبر ⇒ نفس التوقيت النسبي (الوقت من المدة مش من سرعة مقدّرة)
        hint = [{"at_word": 300, "label": "أ"}, {"at_word": 600, "label": "ب"}]
        a = chapter_lines(hint, 1200, 600)
        b = chapter_lines(hint, 1200, 1200)
        self.assertEqual([x.split(" ")[0] for x in a], ["00:00", "02:30", "05:00"])
        self.assertEqual([x.split(" ")[0] for x in b], ["00:00", "05:00", "10:00"])

    def test_block_wraps_for_description(self):
        hint = [{"at_word": 300, "label": "المال"}, {"at_word": 600, "label": "الرزق"}]
        txt = block(hint, 1200, 600)
        self.assertIn("فهرس", txt)
        self.assertIn("00:00", txt)
        self.assertEqual(block(None, 1200, 600), "")


if __name__ == "__main__":
    unittest.main()
