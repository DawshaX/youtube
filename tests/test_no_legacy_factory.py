"""حارس: المصنع القديم (JS) لازم يفضل ميّت — صفر رجعة.

أمر صاحب القناة (2026-09-19): «احذف كل المصنع القديم». الحارس ده بيمنع
إن حد (أو أي أداة) يرجّعه بالغلط، وبيمنع أي وركفلو ينشر من غير المصنع الجديد.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

LEGACY = [
    "server/autoPilot.js",
    "server/viralEngine.js",
    "server/youtubeService.js",
    "server/uploadVerification.js",
    "server/githubSync.js",
    "server/videoFactoryBridge.js",
    "scripts/run-autopilot.js",
    "scripts/produce-from-radar.js",
    "scripts/verify-uploads.js",
    "content/topics_daousha.json",
    ".github/workflows/cosmic-autopilot.yml",
    ".github/workflows/publish-watchdog.yml",
]


class LegacyFactoryGoneTest(unittest.TestCase):
    def test_legacy_files_removed(self):
        alive = [p for p in LEGACY if (ROOT / p).exists()]
        self.assertEqual(alive, [], f"المصنع القديم رجع: {alive}")

    def test_no_workflow_publishes_from_legacy(self):
        bad = []
        for w in (ROOT / ".github" / "workflows").glob("*.yml"):
            txt = w.read_text(encoding="utf-8")
            for needle in ("run-autopilot", "produce-from-radar",
                           "topics_daousha", "autoPilot.js"):
                if needle in txt:
                    bad.append(f"{w.name}: {needle}")
        self.assertEqual(bad, [], f"وركفلو بيستخدم المصنع القديم: {bad}")

    def test_only_factory_publish_can_publish(self):
        """وركفلو واحد بس فيه نشر حقيقي: factory-publish."""
        publishers = []
        for w in (ROOT / ".github" / "workflows").glob("*.yml"):
            txt = w.read_text(encoding="utf-8")
            if "factory_loop.py" in txt or "run_cycle" in txt:
                publishers.append(w.name)
        self.assertIn("factory-publish.yml", publishers)
        self.assertEqual(sorted(publishers), ["factory-publish.yml"])

    def test_status_server_is_read_only(self):
        src = (ROOT / "server" / "index.js").read_text(encoding="utf-8")
        for banned in ("/api/publish-factory", "/api/upload", "/api/autopilot"):
            self.assertNotIn(banned, src)
        self.assertIn("/api/factory/status", src)


if __name__ == "__main__":
    unittest.main()
