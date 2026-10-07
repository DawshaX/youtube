#!/usr/bin/env python3
"""🧪 اختبار المصنع الجديد — رندر فعلي بلا رفع (صفر نشر).

يغطي: التصنيفات الدينية (أسماء/أذكار/كويز) · الروحانيات العامة · المخطّط
الأبدي (جرد + عيّنة) · الطبقة العالمية (ترجمة + ترجمة آية معتمدة).
"""
from __future__ import annotations

import os
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NOOR_DRY", "1")
os.environ.setdefault("NOOR_PLAN", "1")

from xtrendaw import noor_cards, noor_cats  # noqa: E402

WORK = ROOT / "work" / "noor" / "catstest"


def _report(kind: str, res: dict) -> None:
    v = res.get("video")
    size = (v.stat().st_size / 1e6) if v and v.exists() else 0.0
    print(f"✅ {kind:<7} مدة {res.get('duration', 0):6.1f}ث · حجم {size:5.1f}مب", flush=True)


def main() -> int:
    bad = 0
    # ١) التصنيفات (أسماء الله · أذكار · كويز)
    for kind in ("asma", "athkar", "quiz"):
        try:
            item = noor_cats.make(kind)
            if not item:
                print(f"❌ {kind}: رجّع فاضي", flush=True); bad += 1; continue
            print(f"🎬 {kind} · id={item.get('id')} · «{item.get('hook')}»", flush=True)
            if kind == "quiz":
                _report(kind, noor_cards.build_quiz_short(item, WORK / kind))
            else:
                _report(kind, noor_cards.build_card_short(item, WORK / kind))
        except Exception as e:  # noqa: BLE001
            print(f"❌ {kind}: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc(); bad += 1

    # ٢) الروحانيات العامة 🌿
    try:
        from xtrendaw import noor_spirit
        it = noor_spirit.make("سكينة", 0)
        print(f"🎬 spirit · {it['id']} · «{it['hook']}»", flush=True)
        _report("spirit", noor_cards.build_card_short(it, WORK / "spirit"))
    except Exception as e:  # noqa: BLE001
        print(f"❌ spirit: {type(e).__name__}: {e}", flush=True); bad += 1

    # ٣) المخطّط الأبدي 🧠
    try:
        from xtrendaw import noor_plan
        st = noor_plan.stats()
        print(f"🧠 جرد المخزون: {st['kinds']} | المنجز: {st['done']}", flush=True)
        for i in range(5):
            it = noor_plan.next_item()
            if not it:
                print("⚠️ المخطّط رجّع فاضي", flush=True); bad += 1; break
            print(f"   ▸ دور {i+1}: {it.get('plan_kind')} → {it.get('kind')} "
                  f"{it.get('id')} (سورة {it.get('surah') or '-'})", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"❌ المخطّط: {type(e).__name__}: {e}", flush=True); bad += 1

    # ٤) الطبقة العالمية 🌍
    try:
        from xtrendaw import noor_global
        v = noor_global.verse_translation(13, 28, "en")
        t = noor_global.translate_text("آية تُريح القلب", "ur")
        print(f"🌍 ترجمة معتمدة (en): {v[:60]}", flush=True)
        print(f"🌍 ترجمة عنوان (ur): {t[:50]}", flush=True)
        if not v:
            bad += 1
    except Exception as e:  # noqa: BLE001
        print(f"🌍 الترجمة اتعذّرت (مش بتوقف النشر): {type(e).__name__}", flush=True)

    print(("🎉 المصنع الجديد كله نجح" if not bad else f"⚠️ فيه {bad} فشل"), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
