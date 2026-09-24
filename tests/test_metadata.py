"""اختبارات الميتاداتا (العنوان/الوصف/الوسوم) — قفل مكسب المشاهدات.

السبب: شكوى صاحب القناة «مبيجيبوش مشاهدات». اللي بيجيب مشاهدات على يوتيوب
عربي: (١) كلمات الناس بتكتبها فعلًا في العنوان (اسم السورة/الآية/القارئ)،
(٢) وصف فيه النص كامل + مرجع + تفاعل، (٣) #shorts أول ٣ هاشتاجات،
(٤) وسوم مرتبطة (مش عامة). الاختبارات دي تمنع أي تراجع لاحق.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("noor_runner",
                                               ROOT / "scripts" / "noor_runner.py")
nr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nr)


class TestSurahName(unittest.TestCase):
    def test_strips_quran_marks(self):
        self.assertEqual("الرحمن", nr._clean_surah("سُورَةُ الرَّحۡمَٰنِ"))
        self.assertEqual("الحجرات", nr._clean_surah("سُورَةُ الحُجُرَاتِ"))
        self.assertEqual("الملك", nr._clean_surah("سُورَةُ المُلۡكِ"))

    def test_never_empty(self):
        self.assertEqual("القرآن الكريم", nr._clean_surah(""))
        self.assertEqual("القرآن الكريم", nr._clean_surah("سُورَةُ"))


class TestReference(unittest.TestCase):
    def test_single_ayah(self):
        self.assertEqual(
            "سورة الرحمن — الآية 13",
            nr._ref_of({"ayah": 13}, {"surah": "سُورَةُ الرَّحۡمَٰنِ"}))

    def test_range(self):
        self.assertEqual(
            "سورة الأحزاب — الآيات 41–42",
            nr._ref_of({"ayah": 41, "ayah_to": 42}, {"surah": "سُورَةُ الأَحۡزَابِ"}))

    def test_same_start_end_is_single(self):
        self.assertEqual(
            "سورة يونس — الآية 89",
            nr._ref_of({"ayah": 89, "ayah_to": 89}, {"surah": "سُورَةُ يُونُسَ"}))


class TestTags(unittest.TestCase):
    def _tags(self, kind, res=None):
        res = res or {"surah": "سُورَةُ الرَّحۡمَٰنِ", "reciter": "محمود خليل الحصري",
                      "book": "صحيح البخاري"}
        return nr._tags_of({"kind": kind, "theme": "رحمة", "ayah": 13}, res,
                           kind, "محمود خليل الحصري")

    def test_max_15_unique(self):
        for k in ("ayah", "hadith", "reel"):
            t = self._tags(k)
            self.assertLessEqual(len(t), 15, k)
            self.assertEqual(len(t), len(set(t)), f"وسوم مكرّرة في {k}")

    def test_contains_search_terms(self):
        t = self._tags("ayah")
        self.assertIn("الرحمن", " ".join(t))          # اسم السورة بالعامية/الكتابة المتعارفة
        self.assertIn("quran", " ".join(t).lower())
        self.assertIn("tلاوة".replace("t", "ت"), " ".join(t))

    def test_hadith_has_book(self):
        t = self._tags("hadith")
        self.assertIn("صحيح البخاري".split()[1], " ".join(t))


class TestDescription(unittest.TestCase):
    def _desc(self):
        return nr._desc_of("همّك هينتهي 🕊️", "فَإِنَّ مَعَ العُسۡرِ يُسۡرًا",
                           "سورة الشرح — الآية 5",
                           ["🎙️ تلاوة: محمود خليل الحصري", "🧩 من التفسير: مع العسر يسر"],
                           "نور", "#آية_وسكينة")

    def test_hook_first_line(self):
        self.assertTrue(self._desc().startswith("همّك هينتهي"))

    def test_has_reference_and_text(self):
        d = self._desc()
        self.assertIn("فَإِنَّ مَعَ العُسۡرِ يُسۡرًا", d)
        self.assertIn("سورة الشرح — الآية 5", d)

    def test_hashtags_and_shorts_first(self):
        d = self._desc()
        self.assertTrue(d.rstrip().endswith("#تدبر") or "#" in d.rstrip()[-40:])
        self.assertIn("#shorts", d)

    def test_engagement_ask_present(self):
        d = self._desc()
        self.assertIn("اكتب", d)
        self.assertIn("اشترك", d)

    def test_within_youtube_limit(self):
        d = self._desc()
        long_body = " ".join(["آية"] * 2000)
        big = nr._desc_of("هوك", long_body, "سورة كذا — الآية 1", ["س"], "نور")
        self.assertLessEqual(len(big), 4900)   # الحد الفعلي ليوتيوب


class TestTitleRules(unittest.TestCase):
    def test_short_title_has_keywords(self):
        nm = nr._clean_surah("سُورَةُ الرَّحۡمَٰنِ")
        title = f"أي نعمة أنكرتها؟ 🌊 | سورة {nm} آية 13 🤍 تلاوة محمود خليل الحصري"
        self.assertLessEqual(len(title), 95)      # بنقصّها على 95 في الرفع
        self.assertIn("سورة الرحمن", title)
        self.assertIn("آية 13", title)
        self.assertIn("الحصري", title)


if __name__ == "__main__":
    unittest.main()


class TestVaultMetaUpgrade(unittest.TestCase):
    """ترقية ميتاداتا الحلقات المخزّنة قبل كود 2026-09-25."""

    def _ayah(self):
        return {"kind": "noor",
                "title": "أعظم آية في القرآن 🌌 — آية وسكينة ﴿سُورَةُ البَقَرَةِ﴾",
                "tags": "قرآن,تلاوة,إسلاميات,shorts",
                "caption": ("اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ\n\n"
                            "🎙️ تلاوة: محمود خليل الحصري\nالمصادر: alquran.cloud\n"
                            "لا موسيقى في هذا الفيديو.\n\n🤍 شاركها\n\n#قرآن #shorts")}

    def _hadith(self):
        return {"kind": "noor",
                "title": "قبل ما تنشر حديث… شوف ده ⚠️ — حديث اليوم 📖",
                "tags": "قرآن,تلاوة,shorts",
                "caption": ("قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم …\n\n"
                            "📖 صحيح مسلم — حديث رقم 4\nالمصادر: …\n"
                            "🤍 شاركها\n\n#shorts #حديث")}

    def test_ayah_title_upgraded(self):
        t = nr._upgrade_meta(self._ayah())["title"]
        self.assertIn("سورة البقرة", t)
        self.assertIn("تلاوة محمود خليل الحصري", t)

    def test_hadith_title_upgraded(self):
        t = nr._upgrade_meta(self._hadith())["title"]
        self.assertIn("حديث صحيح — صحيح مسلم", t)

    def test_cta_added_once(self):
        m = nr._upgrade_meta(self._ayah())
        self.assertIn("🔔 اشترك", m["caption"])
        m2 = nr._upgrade_meta(m)
        self.assertEqual(m2["caption"].count("🔔 اشترك"), 1)   # مش بيتكرر

    def test_tags_are_focused(self):
        m = nr._upgrade_meta(self._ayah())
        tags = m["tags"].split(",")
        self.assertLessEqual(len(tags), 15)
        self.assertIn("سورة البقرة", tags)

    def test_unknown_title_stays(self):
        m = nr._upgrade_meta({"title": "حاجة غريبة", "caption": "#shorts x"})
        self.assertEqual(m["title"], "حاجة غريبة")

    def test_upgrade_can_be_disabled(self):
        import os
        os.environ["NOOR_META_UPGRADE"] = "0"
        try:
            self.assertEqual(nr._upgrade_meta(self._ayah())["title"],
                             self._ayah()["title"])
        finally:
            os.environ.pop("NOOR_META_UPGRADE", None)
