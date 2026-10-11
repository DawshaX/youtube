"""المسار الجديد يفضل إضافة: خط زمني هادي، وخزنة ما تقبلش ملف من غير ترخيص."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.noor_one import wanted_kind  # noqa: E402
from xtrendaw.noor_next.formats import REFUSED, pick_format  # noqa: E402
from xtrendaw.noor_next.montage import pick_feeling, pick_transition  # noqa: E402
from xtrendaw.noor_next.souls import face_allowed, pick_soul  # noqa: E402
from xtrendaw.noor_next.queries import queries_for  # noqa: E402
from xtrendaw.noor_next.studio import tts_pitch  # noqa: E402
from xtrendaw.noor_next.timeline import build, sacred_text  # noqa: E402
from xtrendaw.noor_next.vault import add_item, empty_index, match  # noqa: E402

SAMPLE = json.loads((ROOT / "data" / "noor_next" / "sample_kitchen.json").read_text(encoding="utf-8"))


class TimelineTests(unittest.TestCase):
    def test_kitchen_is_calm_and_unpublished(self):
        card = build(SAMPLE)
        self.assertEqual(card["palette"]["id"], "kitchen")
        self.assertIsNone(card["music"])
        self.assertFalse(card["faces"])
        self.assertFalse(card["publish"])
        self.assertGreaterEqual(len(card["shots"]), 3)
        self.assertTrue(all(s["zoom"] <= 0.08 for s in card["shots"]))
        self.assertTrue(all(s["visual"] == "card" for s in card["shots"]))

    def test_sacred_text_is_refused(self):
        self.assertTrue(sacred_text("قال رسول الله"))
        bad = dict(SAMPLE)
        bad["spoken"] = "قال رسول الله في الحديث."
        with self.assertRaises(ValueError):
            build(bad)


class DayCapTests(unittest.TestCase):
    def test_eight_shorts_and_four_longs(self):
        self.assertEqual(wanted_kind(0, 0), "short")
        self.assertEqual(wanted_kind(2, 0), "long")
        self.assertEqual(wanted_kind(8, 2), "long")
        self.assertEqual(wanted_kind(3, 4), "short")
        self.assertIsNone(wanted_kind(8, 4))


class MontageTests(unittest.TestCase):
    def test_two_episodes_can_differ(self):
        a = pick_transition("ser-kitchen-s01")
        b = pick_transition("ser-sky-s08")
        self.assertIn(a, ("fade", "fadeblack", "smoothleft", "smoothright", "dissolve"))
        self.assertIn(b, ("fade", "fadeblack", "smoothleft", "smoothright", "dissolve"))
        name, feel = pick_feeling({"id": "child-1", "series_title": "طفل بستر", "emotion": "", "field": ""})
        self.assertEqual(name, "طفل")
        self.assertFalse(feel.get("neon"))


class SoulTests(unittest.TestCase):
    def test_child_is_cartoon_and_faith_has_no_face(self):
        ward = pick_soul({"id": "child-1", "series_title": "طفل بستر", "emotion": "طفل"})
        self.assertEqual(ward["id"], "ward")
        self.assertFalse(ward.get("neon"))
        self.assertFalse(face_allowed({"series_title": "تذكير", "field": "خالق"}))
        self.assertIsNone(pick_soul({"id": "f", "series_title": "تذكير", "field": "خالق"}))
        seen = {pick_soul({"id": f"mix-{i}", "series_title": "مطبخ من غير خوف"})["id"] for i in range(40)}
        self.assertGreater(len(seen), 8)
        self.assertIn("malika", seen)
        self.assertIn("tina", seen)

    def test_format_is_ours_not_a_copied_video(self):
        name, spec = pick_format({"id": "ser-kitchen-s01", "series_title": "مطبخ من غير خوف"})
        self.assertIn(name, ("افتتاح وقطع", "قائمة", "حكاية", "قبل وبعد", "نيون هادي", "طين ثلاثي"))
        self.assertFalse(spec["copied_video"])
        self.assertIn("مش نسخ", spec["rights"])
        self.assertIn("coverr_api", REFUSED)
        self.assertIn("famous_video_file", REFUSED)


class VoiceTests(unittest.TestCase):
    def test_zero_pitch_gets_a_sign(self):
        self.assertEqual(tts_pitch("0Hz"), "+0Hz")
        self.assertEqual(tts_pitch("-2Hz"), "-2Hz")
        self.assertEqual(tts_pitch(""), "+0Hz")


class QueryTests(unittest.TestCase):
    def test_sentence_gets_its_own_shot(self):
        qs = queries_for("البصل بيدمع لأن بخاره يلمس العين.", "kitchen morning no people")
        self.assertIn("onion on wooden board no people", qs)
        self.assertTrue(all("no people" in q or "onion" in q for q in qs))


class VaultTests(unittest.TestCase):
    def test_license_is_required(self):
        index = empty_index()
        with self.assertRaises(ValueError):
            add_item(index, {"id": "x", "kind": "video", "source": "", "license": "", "commercial": True, "no_faces": True, "calm": True})

    def test_match_empty_is_card(self):
        self.assertIsNone(match(empty_index(), kind="video", palette="kitchen", query="board"))


if __name__ == "__main__":
    unittest.main()
