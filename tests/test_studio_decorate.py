"""🧩 اختبار طبقات الزينة في تمريرة واحدة.

ليه: الأفاتار + العلامة + الإطار كانوا ٣ تمريرات ffmpeg كاملة على الفيديو
كله. على حلقة ١٠ دقايق ده دقايق مهدورة من مهلة الدورة (٤٥ دقيقة) بلا أي
فرق في النتيجة. والأمان شرط: أي فشل ⇒ `None` والمصنع يرجّع للطريقة القديمة.
"""
import subprocess
import unittest
from pathlib import Path

from xtrendaw.noor_next import studio


class DecorateTests(unittest.TestCase):
    def test_nothing_to_do_returns_none(self):
        # مفيش طبقات ⇒ None (المصنع ما يستهلكش تمريرة فاضية)
        self.assertIsNone(studio.decorate(Path("/tmp/x.mp4"), Path("/tmp/y.mp4"),
                                          run=lambda cmd: None))

    def test_failure_returns_none_not_exception(self):
        gone = Path("/tmp/مافيش-كده.png")
        got = studio.decorate(Path("/tmp/x.mp4"), Path("/tmp/y.mp4"), badge=gone,
                              run=lambda cmd: None)
        # العلامة مش موجودة ⇒ مفيش طبقات ⇒ None، ومفيش استثناء طلع
        self.assertIsNone(got)

    def test_broken_run_returns_none(self):
        def boom(cmd):
            raise RuntimeError("ffmpeg مش موجود")
        got = studio.decorate(Path("/tmp/x.mp4"), Path("/tmp/y.mp4"),
                              badge=Path(__file__).resolve().parents[1] /
                              "assets" / "ornaments" / "frame.png",
                              run=boom)
        self.assertIsNone(got)          # الفشل بيسجّل وما بيكسرش


if __name__ == "__main__":
    unittest.main()
