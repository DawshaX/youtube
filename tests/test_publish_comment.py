"""💬 اختبارات التعليق المثبّت — الحاجة اللي كانت «منتَج ورق» في المصنع.

الحقيقتان اللي بيحرسهم الاختبار:
  • الدالة **آمنة تمامًا**: بلا صلاحيات/بلا معرّف ⇒ False، ومفيش استثناء
    (يعني مستحيل تكسر النشر — وده شرط الاستوديو).
  • نصّ التعليق **متنوّع لكل حلقة** ومش قالب واحد ثابت.
"""
import unittest

from xtrendaw.pro.metadata import pinned_comment
from xtrendaw.publish import youtube as yt


class CommentTests(unittest.TestCase):
    def test_comment_is_safe_without_credentials(self):
        self.assertFalse(yt.comment("", "نص"))
        self.assertFalse(yt.comment("vid", ""))
        self.assertFalse(yt.comment("vid", "نص"))     # مفيش توكن في بيئة الاختبار

    def test_pinned_text_is_not_one_template(self):
        longs = {pinned_comment({"id": f"long-{i}", "kind": "long"})
                 for i in range(1, 12)}
        self.assertGreaterEqual(len(longs), 2, "التعليق لازم يتنوّع بين الحلقات")
        self.assertTrue(all(t.strip() for t in longs))

    def test_short_kinds_get_their_own_prompt(self):
        for kind in ("ayah", "hadith", "dua", "story", "life", "long_qissa"):
            txt = pinned_comment({"id": kind + "-1", "kind": kind})
            self.assertGreater(len(txt), 8, kind)
        self.assertNotEqual(pinned_comment({"id": "a", "kind": "ayah"}),
                            pinned_comment({"id": "a", "kind": "hadith"}))


if __name__ == "__main__":
    unittest.main()
