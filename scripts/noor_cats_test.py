#!/usr/bin/env python3
"""🧪 اختبار المصنع — تصنيفات + تنويع + مخطّط + عالمي (رندر فعلي، صفر نشر)."""
from __future__ import annotations

import os
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NOOR_DRY", "1")
os.environ.setdefault("NOOR_PLAN", "1")

from xtrendaw import noor_cards  # noqa: E402

WORK = ROOT / "work" / "noor" / "catstest"


def _report(kind: str, res: dict) -> None:
    v = res.get("video")
    size = (v.stat().st_size / 1e6) if v and v.exists() else 0.0
    print(f"✅ {kind:<9} مدة {res.get('duration', 0):6.1f}ث · حجم {size:5.1f}مب",
          flush=True)


def main() -> int:
    bad = 0

    # ١) التصنيفات الدينية
    for kind in ("asma", "athkar", "quiz"):
        try:
            from xtrendaw import noor_cats
            item = noor_cats.make(kind)
            if not item:
                print(f"❌ {kind}: فاضي", flush=True); bad += 1; continue
            print(f"🎬 {kind} · {item.get('id')} · «{item.get('hook')}»", flush=True)
            _report(kind, noor_cards.build_quiz_short(item, WORK / kind)
                    if kind == "quiz" else
                    noor_cards.build_card_short(item, WORK / kind))
        except Exception as e:  # noqa: BLE001
            print(f"❌ {kind}: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc(); bad += 1

    # ٢) 🆕 التصنيفات الأربعة الجديدة (كروت: مواقيت · هجري · معلومات · أمثال)
    try:
        from xtrendaw import noor_more
        for kind in ("salah", "hijri", "qfacts", "proverb"):
            item = noor_more.make(kind)
            if not item:
                print(f"❌ {kind}: فاضي", flush=True); bad += 1; continue
            print(f"🎬 {kind} · {item.get('id')} · «{item.get('hook')}»", flush=True)
            print(f"     سطر: {str((item.get('lines') or [''])[0])[:70]}", flush=True)
            _report(kind, noor_cards.build_card_short(item, WORK / kind))
    except Exception as e:  # noqa: BLE001
        print(f"❌ الجديد: {type(e).__name__}: {e}", flush=True); bad += 1

    # ٣) الروحانيات 🌿
    try:
        from xtrendaw import noor_spirit
        it = noor_spirit.make("أمل", 0)
        print(f"🎬 spirit · {it['id']} · «{it['hook']}»", flush=True)
        _report("spirit", noor_cards.build_card_short(it, WORK / "spirit"))
    except Exception as e:  # noqa: BLE001
        print(f"❌ spirit: {type(e).__name__}", flush=True); bad += 1

    # ٤) 🎙️ تنويع الأصوات
    try:
        from xtrendaw import noor_voice
        for k in ("spirit", "quran", "asma", "quiz"):
            print(f"🎙️ صوت {k:<7} → {noor_voice.pick(k, 0)}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"❌ الأصوات: {type(e).__name__}", flush=True); bad += 1

    # ٥) 🧠 المخطّط: الجرد + أنواع جديدة + ترقيم السلسلة
    try:
        from xtrendaw import noor_plan
        st = noor_plan.stats()
        print(f"🧠 الجرد: {st['kinds']} | المنجز: {st['done']}", flush=True)
        for kind in ("salah", "hijri", "qfacts", "proverb", "qissa", "athkar"):
            try:
                s = noor_plan.series(kind)
                print(f"   ▸ مخزون {kind:<8}: {len(s)} عنصر", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"   ⚠️ {kind}: {type(e).__name__}", flush=True)
        for i in range(6):
            it = noor_plan.next_item()
            if not it:
                break
            print(f"   ▸ دور {i+1}: {it.get('plan_kind')} → {it.get('kind')} "
                  f"{str(it.get('id'))[:26]} | سلسلة: {str(it.get('series') or '-')[:32]}",
                  flush=True)
        # سلسلة قرآنية فيها ترقيم
        q = noor_plan.series("quran")
        print(f"   ▸ عيّنة سلسلة: {q[0][1].get('series')} | {q[300][1].get('series')}",
              flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"❌ المخطّط: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc(); bad += 1

    # ٦) 📚 مجموعة حديث جديدة (إثبات إن الـ٨ مجموعات شغالة)
    try:
        from xtrendaw import noor_plan
        h = noor_plan.hadith_stock("abudawud", limit=50)
        print(f"📚 سنن أبي داود: {len(h)} حديث قصير جاهز (عيّنة)", flush=True)
        if not h:
            bad += 1
    except Exception as e:  # noqa: BLE001
        print(f"📚 الحديث الجديد اتعذّر: {type(e).__name__}: {str(e)[:80]}",
              flush=True); bad += 1

    # ٧) 🌍 الترجمة العالمية
    try:
        from xtrendaw import noor_global
        v = noor_global.verse_translation(2, 153, "en")
        print(f"🌍 ترجمة معتمدة: {v[:60]}", flush=True)
        if not v:
            bad += 1
    except Exception as e:  # noqa: BLE001
        print(f"🌍 الترجمة اتعذّرت (مش بتوقف النشر): {type(e).__name__}", flush=True)

    print(("🎉 المصنع كله نجح" if not bad else f"⚠️ فيه {bad} فشل"), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
