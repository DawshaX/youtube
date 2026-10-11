#!/usr/bin/env python3
"""نشر حلقة مكتبة زيادة. ما يلمسش جدول القرآن والحديث."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from xtrendaw.noor_next.cycle import publish_next  # noqa: E402


def main() -> int:
    rc = publish_next("short")
    print(f"[library] rc={rc}", flush=True)
    # 2 = الكوتة أو المسافة. مش فشل يوقف المصنع.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
