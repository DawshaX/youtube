"""سياسة الحذف التلقائي — الدرس الحقيقي (2026-09-19).

الحارس القديم في run_cycle كان بينادي _yt.delete(vid) لما oEmbed يرجّع 403.
403 بتيجي كمان من rate-limit وحماية مؤقتة — يعني فيديوهات حقيقية اتمسحت من
القناة غلط. السياسة الجديدة: (1) مفتاح بيئة صريح، (2) تأكيد من الـAPI الرسمي.
"""
import os
import unittest
from unittest import mock

from xtrendaw.publish import youtube


class AutodeletePolicyTests(unittest.TestCase):
    def test_default_is_off(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(youtube.autodelete_enabled())
            self.assertFalse(youtube.should_autodelete("blocked"),
                             "الافتراضي لازم يكون: مفيش حذف — حتى لو الفحص قال blocked")

    def test_enabled_but_unconfirmed_verdict_never_deletes(self):
        with mock.patch.dict(os.environ, {"XT_ALLOW_YOUTUBE_AUTODELETE": "1"}, clear=True):
            for verdict in (None, "ok", "gone", "error"):
                self.assertFalse(youtube.should_autodelete(verdict),
                                 f"الحذف اتسمح بفحص غير مؤكد: {verdict}")

    def test_deletes_only_with_explicit_flag_and_official_confirmation(self):
        with mock.patch.dict(os.environ, {"XT_ALLOW_YOUTUBE_AUTODELETE": "1"}, clear=True):
            self.assertTrue(youtube.should_autodelete("blocked"))
        with mock.patch.dict(os.environ, {"XT_ALLOW_YOUTUBE_AUTODELETE": "0"}, clear=True):
            self.assertFalse(youtube.should_autodelete("blocked"))

    def test_oembed_403_alone_is_not_proof(self):
        with mock.patch.object(youtube, "requests") as fake:
            fake.get.return_value = mock.Mock(status_code=403)
            blocked, why = youtube.check_blocked("abc")
        self.assertTrue(blocked)
        self.assertEqual(why, "blocked")
        # لكن القرار النهائي لازم فحص رسمي + مفتاح → مايتحذفش
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(youtube.should_autodelete(why))


if __name__ == "__main__":
    unittest.main()
