"""فلتر رخص الأصول الشبكية.

الدرس (2026-09-19): اللائحة كانت أضيق من الموثّق، فالمصنع كان بينزّل اللقطات
من بيكسلز/بيكساباي/ناسا ويرميها، ويرجع للمخزون الداخلي الثابت.
"""
from __future__ import annotations

import unittest

from xtrendaw import vault


class NetworkLicenseGateTest(unittest.TestCase):
    def test_stock_sources_documented_as_green_are_accepted(self) -> None:
        for lic in ("Pexels-License", "Pixabay-License", "NASA-Media-Usage",
                    "Public-Domain"):
            self.assertIn(lic, vault.ALLOWED_NETWORK_LICENSES,
                          f"{lic} موثّق 🟢 في docs/MEDIA_VAULT_SOURCES.md")
            self.assertIn(lic, vault.ALLOWED_LICENSES)

    def test_cc_licenses_still_accepted(self) -> None:
        for lic in ("CC0", "CC-BY-3.0", "CC-BY-4.0"):
            self.assertIn(lic, vault.ALLOWED_NETWORK_LICENSES)

    def test_owned_and_unknown_licenses_still_rejected(self) -> None:
        for lic in ("All-Rights-Reserved", "YouTube-Standard", "Getty",
                    "", "unknown", "Internal-Generated"):
            self.assertNotIn(lic, vault.ALLOWED_NETWORK_LICENSES,
                             f"{lic} مش رخصة شبكية مقبولة")

    def test_every_network_license_is_valid_for_rendering(self) -> None:
        # أي رخصة بتعدي فلتر الشبكة لازم تعدي بوابة الرندر كمان،
        # وإلا تبقى لقطة مقبولة وبعدين الرندر يموت عليها.
        extra = vault.ALLOWED_NETWORK_LICENSES - vault.ALLOWED_LICENSES
        self.assertFalse(extra, f"رخص بتعدي الشبكة وترفض في الرندر: {extra}")


if __name__ == "__main__":
    unittest.main()
