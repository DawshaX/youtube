"""هوية واحدة في كل المخرجات — قاعدة المستودع (HANDOFF_BRIEF §7).

الدرس (2026-09-19): الفيديو المنشور طلع وفيه «XDAW NOVA» و«@XTreNDAW» جوه
الإطارات وفي الوصف، على قناة اسمها مختلف — يعني المخرج العام كان بيحمل
هوية مش بتاعتنا.
"""
from __future__ import annotations

import pathlib
import unittest

from xtrendaw import settings

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEGACY = ("XDAWNOVA", "XTreNDAW", "XDAW NOVA", "CosmicTube")
# استثناءات مقصودة: عناوين HTTP الداخلية (مش مخرجات للجمهور) والوثائق
ALLOWED_LINES = (
    "User-Agent",                       # هيدر HTTP داخلي
    "DawshaX/XTreNDAW",                 # اسم افتراضي للمستودع (مش مخرَج)
    "releases/download/",               # روابط أصول داخلية
    "callback.html",                    # مسار OAuth الداخلي
)

OUTPUT_FILES = ("din.py", "planner.py", "run_cycle.py", "brain.py",
                "requests.py", "scenes.py", "brand.py", "content.py",
                "bot.py", "publish/youtube.py", "publish/telegram.py")


class BrandTest(unittest.TestCase):
    def test_brand_defaults_to_the_channel_identity(self) -> None:
        self.assertTrue(settings.BRAND_NAME.strip(), "لازم يكون فيه اسم براند")
        self.assertTrue(settings.HANDLE.strip(), "لازم يكون فيه معرّف للخاتمة")

    def test_brand_is_configurable(self) -> None:
        import importlib
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"XT_BRAND": "قناة_تجربة"}):
            importlib.reload(settings)
            self.assertEqual(settings.BRAND_NAME, "قناة_تجربة")
        importlib.reload(settings)   # رجّع الافتراضي

    def test_no_legacy_brand_in_output_code(self) -> None:
        offenders = []
        for rel in OUTPUT_FILES:
            f = ROOT / "xtrendaw" / rel
            if not f.exists():
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if any(l in line for l in LEGACY) and \
                        not any(a in line for a in ALLOWED_LINES):
                    offenders.append(f"{rel}:{i}: {line.strip()[:90]}")
        self.assertFalse(offenders,
                         "أسماء قديمة ظاهرة في مخرجات الجمهور:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
