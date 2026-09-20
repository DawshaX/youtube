"""محرك التقليد: العين تشوف اللقطات → سكربت لحظة-بلحظة → رندر بنفس الترتيب.

شكوى صاحب القناة (2026-09-19): «الفيديو رجع لنشرة أخبار — عايز تقليد الفيديو
نفسه، بكل مشهد ولقطة». الاختبارات دي بتقفل الأبواب اللي كانت بتخلي الحلقة
نشرة: لافتات «الحقيقة الأولى»، استعلام واحد متكرر لكل المشاهد، وغياب اللقطات.
"""
import unittest

from xtrendaw import content


SHOTS_TOPIC = {
    "id": "eye-TEST123",
    "title_ar": "تحدي المارشميلو",
    "tags": "تحدي,مارشميلو",
    "shots": [
        {"t0": 0.0, "t1": 2.5, "dur": 2.5, "say_ar": "شوف إيدي… بترجف!",
         "say_en": "Look at my hand shaking!", "visual_query": "hand holding marshmallow",
         "sfx": "impact", "on_screen": "جرب كده"},
        {"t0": 2.5, "t1": 5.0, "dur": 2.5, "say_ar": "المارشميلو على النار بقى لون دهب",
         "say_en": "It turned golden", "visual_query": "marshmallow on fire closeup",
         "sfx": "", "on_screen": ""},
        {"t0": 5.0, "t1": 8.0, "dur": 3.0, "say_ar": "وطلعت مفاجأة!",
         "say_en": "Surprise!", "visual_query": "surprised kid face",
         "sfx": "pop", "on_screen": "مفاجأة"},
    ],
}


class ReplicationScriptTest(unittest.TestCase):
    def test_segments_follow_shots_in_order(self):
        segs = content.compose_script(SHOTS_TOPIC, "ar")
        said = [s["text"] for s in segs if s["seg"] != "cta" and s["seg"] != "outro"]
        self.assertEqual(said[0], SHOTS_TOPIC["shots"][0]["say_ar"])
        self.assertEqual(said[1], SHOTS_TOPIC["shots"][1]["say_ar"])
        self.assertEqual(said[2], SHOTS_TOPIC["shots"][2]["say_ar"])

    def test_no_news_bulletin_labels(self):
        segs = content.compose_script(SHOTS_TOPIC, "ar")
        joined = " ".join(s["text"] for s in segs)
        for banned in ("الحقيقة الأولى", "الحقيقة الثانية", "فاكت", "Fact 1"):
            self.assertNotIn(banned, joined)

    def test_each_segment_carries_its_own_visual_query(self):
        segs = content.compose_script(SHOTS_TOPIC, "ar")
        queries = [s.get("visual_query") for s in segs if s.get("visual_query")]
        self.assertEqual(queries, [sh["visual_query"] for sh in SHOTS_TOPIC["shots"]])
        self.assertEqual(len(set(queries)), len(queries))  # مش استعلام واحد مكرر

    def test_english_lines_match_shots(self):
        lines = content.english_lines(SHOTS_TOPIC)
        self.assertEqual(lines[0], SHOTS_TOPIC["shots"][0]["say_en"])

    def test_plain_topic_still_uses_old_template(self):
        segs = content.compose_script({"hook_ar": "تحذير", "facts_ar": ["أ", "ب"],
                                       "id": "x"}, "ar")
        self.assertEqual(segs[0]["text"], "تحذير")


class ShotBucketsTest(unittest.TestCase):
    """خط اللقطات من تقرير المشاهدة الحقيقي (مشاهد + تسميات + صوت)."""

    def _report(self):
        return {
            "durationSeconds": 9.0,
            "captions": [{"t": 0.5, "dur": 1.0, "text": "اول حاجة"},
                         {"t": 4.0, "dur": 1.0, "text": "تاني حاجة"}],
            "scenes": [{"start": 0, "end": 3, "desc": "ولد بيجري"},
                       {"start": 3, "end": 6, "desc": "بياكل مارشميلو"},
                       {"start": 6, "end": 9, "desc": "وشه مندهش"}],
            "audioRmsPerSec": [0.1, 0.2, 0.9, 0.1, 0.4, 0.3, 0.2, 0.8, 0.1],
        }

    def test_buckets_keep_real_timings_and_text(self):
        from xtrendaw.eye import _shot_buckets
        shots = _shot_buckets(self._report())
        self.assertGreaterEqual(len(shots), 3)
        self.assertAlmostEqual(shots[0]["t0"], 0.0, places=1)
        self.assertAlmostEqual(shots[-1]["t1"], 9.0, places=1)
        self.assertIn("اول حاجة", shots[0]["say"])
        self.assertEqual(shots[1]["desc"], "بياكل مارشميلو")

    def test_loud_moment_is_visible(self):
        from xtrendaw.eye import _shot_buckets
        shots = _shot_buckets(self._report())
        self.assertGreater(max(s["rms"] for s in shots), 0.5)


class ProduceUsesShotQueryTest(unittest.TestCase):
    def test_produce_reads_visual_query_per_shot(self):
        import inspect
        from xtrendaw import produce
        src = inspect.getsource(produce.produce_episode)
        self.assertIn('item.get("visual_query")', src)
        # ولازم يكون فيه فرق واضح: التقليد = بلا لافتات
        self.assertIn("replication", src)


if __name__ == "__main__":
    unittest.main()


class StoryboardWatchTest(unittest.TestCase):
    """مسار المشاهدة بلا تنزيل: صور كل ثانية + كلام — ده اللي خلّى العين تشوف.

    الدرس (2026-09-20): yt-dlp اترفض من IP الخوادم («Sign in to confirm
    you're not a bot») فالعين كانت عمياء والمصنع بيرجع لنشرة أخبار.
    """

    VTT = """WEBVTT
Kind: captions
Language: ar

00:00:00.120 --> 00:00:02.400
اول حاجة بنشوفها

00:00:02.400 --> 00:00:05.000
<b>تاني حاجة</b> مهمة
"""

    def test_parse_vtt(self):
        from xtrendaw.eye import parse_vtt
        rows = parse_vtt(self.VTT)
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0]["t"], 0.12, places=2)
        self.assertEqual(rows[1]["text"], "تاني حاجة مهمة")   # الوسوم اتشالت
        self.assertGreater(rows[0]["dur"], 1.0)

    def test_storyboard_url_building(self):
        import inspect
        from xtrendaw import eye
        src = inspect.getsource(eye.storyboard_frames)
        self.assertIn("templateUrl", src)
        self.assertIn("storyboardWidth", src)

    def test_report_shape_matches_watch(self):
        """التقرير البديل لازم يطابق اللي المصنع مستنيه (مشاهد/مدة/ميتا)."""
        import inspect
        from xtrendaw import eye
        src = inspect.getsource(eye.watch_via_media)
        for key in ('"scenes"', '"durationSeconds"', '"meta"', '"captions"'):
            self.assertIn(key, src)
        self.assertIn('"desc"', src)   # وصف بصري لكل مشهد

    def test_watch_falls_back_to_media_path(self):
        import inspect
        from xtrendaw import eye
        src = inspect.getsource(eye.watch)
        self.assertIn("watch_via_media", src)


class RadarMetaShapeTest(unittest.TestCase):
    """شكل مسح الرادار بيتغير — العين لازم تصمد مع القائمة والقاموس.

    بق حقيقي (2026-09-20): `snap["videos"]` بقت قائمة → AttributeError →
    العين فشلت في التشغيل اليدوي بالكامل.
    """

    def _with_snapshot(self, payload):
        import json, tempfile, unittest.mock as mock
        from pathlib import Path
        from xtrendaw import eye
        tmp = Path(tempfile.mkdtemp()) / "snap.json"
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        with mock.patch.object(eye, "SNAPSHOT_PATH", tmp):
            return eye._radar_meta("ABC123")

    def test_list_shape(self):
        meta = self._with_snapshot({"videos": [
            {"videoId": "ABC123", "title": "ترند", "channel": "قناة",
             "viewCount": 5_000_000}]})
        self.assertEqual(meta.get("title"), "ترند")
        self.assertEqual(meta.get("viewCount"), 5_000_000)

    def test_dict_shape(self):
        meta = self._with_snapshot({"videos": {
            "ABC123": {"title": "تاني", "channel": "ق"}}})
        self.assertEqual(meta.get("title"), "تاني")

    def test_unknown_video_is_empty(self):
        self.assertEqual(self._with_snapshot({"videos": []}), {})
