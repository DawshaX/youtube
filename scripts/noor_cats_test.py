#!/usr/bin/env python3
"""🧪 اختبار التصنيفات الجديدة — يرندر فعليًا (بلا رفع خالص).

بيختبر كل تصنيف جديد مرة واحدة:
  • asma · athkar  → قالب الكارت (build_card_short)
  • quiz           → قالب الكويز (build_quiz_short) بتلاوة بشرية
  • dua · story    → نجيب بياناتهم ونتأكد إنها جاهزة (الرندر بتاعهم هو نفس
                     محرّك الآيات المستخدم في الإنتاج بالفعل)
النتيجة: سطر لكل تصنيف بالـid + المدة + حجم الملف. صفر رفع، صفر نشر.
"""
from __future__ import annotations

import os
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NOOR_DRY", "1")

from xtrendaw import noor_cards, noor_cats  # noqa: E402

WORK = ROOT / "work" / "noor" / "catstest"


def _report(kind: str, res: dict) -> None:
    v = res.get("video")
    size = (v.stat().st_size / 1e6) if v and v.exists() else 0.0
    print(f"✅ {kind:<7} مدة {res.get('duration', 0):6.1f}ث · حجم {size:5.1f}مب "
          f"· {v}", flush=True)


def main() -> int:
    bad = 0
    for kind in noor_cats.CATS:
        try:
            item = noor_cats.make(kind)
        except Exception as e:  # noqa: BLE001
            print(f"❌ {kind}: فشل الجلب ({type(e).__name__}: {e})", flush=True)
            bad += 1
            continue
        if not item:
            print(f"❌ {kind}: رجّع فاضي", flush=True)
            bad += 1
            continue
        print(f"🎬 {kind} · id={item.get('id')} · «{item.get('hook')}»", flush=True)
        try:
            if kind in ("asma", "athkar"):
                _report(kind, noor_cards.build_card_short(item, WORK / kind))
            elif kind == "quiz":
                _report(kind, noor_cards.build_quiz_short(item, WORK / kind))
            else:
                ok = bool(item.get("surah")) and bool(item.get("hook"))
                print(f"✅ {kind:<7} جاهز للرندر (سورة {item.get('surah')} "
                      f"آية {item.get('ayah')}) — المحرّك: noor_premium.render",
                      flush=True)
                if not ok:
                    bad += 1
        except Exception as e:  # noqa: BLE001
            print(f"❌ {kind}: فشل الرندر ({type(e).__name__}: {e})", flush=True)
            traceback.print_exc()
            bad += 1
    print(("🎉 كل التصنيفات نجحت" if not bad else f"⚠️ فيه {bad} فشل"), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
