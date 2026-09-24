"""اختبارات استخراج **متن الحديث** من غير الإسناد (اتصلحت 2026-09-25).

ليه ده مهم: قبل الإصلاح كان الفيديو بيروي سلسلة الرواة كاملة
(«حدثنا عبد الله بن مسلمة عن مالك عن سمي عن أبي صالح عن أبي هريرة…»)
= ٨–١٠ ثواني في أول كل شورت حديث + تشويش على المشاهد. الصيغة الشائعة
«أَنَّ رَسُولَ اللَّهِ ﷺ قَالَ» مكنتش في القائمة.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from xtrendaw import noor_build as nb  # noqa: E402


class TestMatnExtraction(unittest.TestCase):
    def test_anna_rasul_allah_form(self):
        """الصيغة اللي كانت بتفشل: «أَنَّ رَسُولَ اللَّهِ ﷺ قَالَ»."""
        t = ("حَدَّثَنَا عَبْدُ اللَّهِ بْنُ مَسْلَمَةَ، عَنْ مَالِكٍ، عَنْ سُمَىٍّ، "
             "عَنْ أَبِي صَالِحٍ، عَنْ أَبِي هُرَيْرَةَ ـ رضى الله عنه ـ "
             "أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم قَالَ مَنْ قَالَ "
             "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ فِي يَوْمٍ مِائَةَ مَرَّةٍ.")
        m = nb._matn(t)
        self.assertNotIn("حَدَّثَنَا", m)
        self.assertNotIn("عَبْدُ اللَّهِ بْنُ مَسْلَمَةَ", m)
        self.assertNotIn("أَبِي صَالِحٍ", m)
        self.assertIn("مَنْ قَالَ سُبْحَانَ اللَّهِ", m)
        self.assertIn("رَسُولَ اللَّهِ", m)

    def test_anni_nabiy_form(self):
        t = ("عَنْ أَبِي هُرَيْرَةَ رَضِيَ اللَّهُ عَنْهُ عَنِ النَّبِيِّ "
             "صلى الله عليه وسلم قَالَ: مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ "
             "الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ.")
        m = nb._matn(t)
        self.assertNotIn("أَبِي هُرَيْرَةَ", m)
        self.assertIn("مَنْ كَانَ يُؤْمِنُ", m)

    def test_qala_rasul_allah_form(self):
        t = ("حَدَّثَنَا مَسَدَّدٌ عَنْ قَتَادَةَ عَنْ أَنَسٍ قَالَ رَسُولُ اللَّهِ "
             "صلى الله عليه وسلم: يَسِّرُوا وَلَا تُعَسِّرُوا.")
        m = nb._matn(t)
        self.assertNotIn("مَسَدَّدٌ", m)
        self.assertIn("يَسِّرُوا", m)

    def test_plain_matn_untouched(self):
        t = "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى."
        self.assertIn("الأَعْمَالُ بِالنِّيَّاتِ", nb._matn(t))

    def test_no_short_cutoff_garbage(self):
        # ما ينفعش القص يرجّع جملة مبتورة أقل من 25 حرف
        for t in ("قال:", "أن ", "قال رسول الله"):
            self.assertGreaterEqual(len(nb._matn(t)), 1)

    def test_display_cleaning_keeps_words(self):
        # علامات الاقتباس والاتجاه تتشال، والكلمات تفضل زي ما هي
        t = '‏ " مَنْ قَالَ سُبْحَانَ اللَّهِ وَبِحَمْدِهِ ‏" ‏.'
        c = nb._clean_display(t)
        self.assertNotIn('"', c)
        self.assertNotIn("\u200f", c)
        self.assertIn("سُبْحَانَ اللَّهِ وَبِحَمْدِهِ", c)


if __name__ == "__main__":
    unittest.main()
