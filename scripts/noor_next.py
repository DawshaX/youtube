#!/usr/bin/env python3
"""مسار المصنع الجديد. ما ينشرش، وما يتوصلش بالحي."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xtrendaw.noor_next.render import render_episode  # noqa: E402
from xtrendaw.noor_next.timeline import build  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="مصنع المكتبة — رندر محلي، من غير نشر")
    p.add_argument("episode", type=Path, help="ملف حلقة JSON")
    p.add_argument("--out", type=Path, default=ROOT / "work" / "noor_next" / "proof.mp4")
    p.add_argument("--vault", type=Path, default=ROOT / "data" / "noor_next" / "vault.json")
    args = p.parse_args()
    episode = json.loads(args.episode.read_text(encoding="utf-8"))
    # بناء الخط قبل الرندر عشان الغلط يظهر قبل الصوت.
    build(episode)
    result = render_episode(episode, args.out, args.out.parent / "work", args.vault)
    print(json.dumps(result["gate"], ensure_ascii=False, indent=2))
    return 0 if result["gate"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
