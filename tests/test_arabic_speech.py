"""اختبارات المطبّع العربي للنطق (2026-09-25).

الهدف: «نطق عربي سليم» — أي خطأ هنا = صوت غلط في فيديو منشور للعالم.
كل حالة هنا حصلت فعلًا في محتوى القناة (ﷺ · ﴿ ﴾ · فواتح السور · أرقام عربية).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xtrendaw.tts import normalize_for_speech  # noqa: E402


class TestSpeechNormalize(unittest.TestCase):
    def test_salawat_expanded(self):
        self.assertIn("صلى الله عليه وسلم",
                      normalize_for_speech("قال رسول الله ﷺ: اتقوا الله"))
        self.assertIn("جل جلاله", normalize_for_speech("تبارك الله ﷻ"))

    def test_ornate_brackets_and_emoji_removed(self):
        t = normalize_for_speech("﴿سُورَةُ المُلكِ﴾ 🤍🌊")
        self.assertNotIn("﴿", t)
        self.assertNotIn("﴾", t)
        self.assertNotIn("🤍", t)
        self.assertIn("سُورَةُ المُلكِ", t)

    def test_arabic_digits_to_latin(self):
        self.assertIn("52", normalize_for_speech("رواه البخاري رقم ٥٢"))
        self.assertIn("13", normalize_for_speech("الآية ١٣"))

    def test_dagger_alef_becomes_alef(self):
        # «الرَّحۡمَٰن» لازم تنطق «الرَّحمان» (ألف طويلة)، مش «الرحمَن»
        self.assertIn("الرَّحمَانِ", normalize_for_speech("الرَّحۡمَٰنِ"))

    def test_quran_waqf_marks_removed(self):
        t = normalize_for_speech("كَلَّا ۖ سَيَعۡلَمُونَ ۩ ۞")
        for ch in "ۖۗۘۚۛ۞۩":
            self.assertNotIn(ch, t)

    def test_muqattaat_expanded_as_whole_token(self):
        self.assertEqual("ألف لام ميم", normalize_for_speech("الم"))
        self.assertEqual("طا ها", normalize_for_speech("طه"))
        self.assertEqual("يا سين", normalize_for_speech("يسٓ"))
        self.assertEqual("صاد", normalize_for_speech("ص"))
        self.assertEqual("قاف", normalize_for_speech("ق"))
        self.assertEqual("نون", normalize_for_speech("نٓ"))

    def test_no_false_positive_inside_words(self):
        # بق حقيقي: «الر» جوه «الرحمن» اتوسّعت غلط → «ألف لام راَّحا ميمَانِ»
        self.assertEqual("الرَّحمَانِ", normalize_for_speech("الرَّحۡمَٰنِ"))
        self.assertEqual("الرحمن الرحيم", normalize_for_speech("الرحمن الرحيم"))
        self.assertEqual("والصلاة والسلام", normalize_for_speech("والصلاة والسلام"))

    def test_tatweel_and_variant_letters(self):
        self.assertEqual("كِتَابٌ كَبِير هُدَى", normalize_for_speech("كِتَابٌ کَبِير ھُدَى ـــ"))

    def test_spacing_clean(self):
        self.assertNotIn("  ", normalize_for_speech("مرحبا   بالعالم  "))
        self.assertTrue(normalize_for_speech("   ").strip() == "")


if __name__ == "__main__":
    unittest.main()
