"""يتأكد إن الهوك من النص، والعناوين مش قالب، والشورت جوا حد يوتيوب."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from xtrendaw.noor_sense import (  # noqa: E402
    BUDGET, ROUTES, SHORT_MAX, SHORT_MIN, awaken, hook_from_text, is_generic,
    long_title, quotes_verse, speech_room, title_of, without_verse,
)


def main() -> int:
    errs = []
    fire = "قلنا يا نار كوني بردا وسلاما على ابراهيم"
    hook = hook_from_text(fire, surah="الأنبياء", who="إبراهيم", kind="mujiza")
    if "إبراهيم" not in hook:
        errs.append("هوك المعجزة ما سمّاش صاحب القصة: " + hook)
    if quotes_verse(hook, fire):
        errs.append("الهوك بيقتبس الآية: " + hook)
    quran_hook = hook_from_text(fire, surah="الأنبياء", kind="quran")
    if quotes_verse(quran_hook, fire):
        errs.append("هوك التلاوة بينطق الآية: " + quran_hook)
    if not is_generic("آية تُريح القلب 🤍"):
        errs.append("الشعار العام ما اتعرفش")
    if is_generic("رؤيا يوسف… بداية الحكاية 🌙"):
        errs.append("هوك القصة المكتوب اتعامل كشعار")
    kept = awaken({"kind": "story", "plan_kind": "qissa", "who": "يوسف",
                   "hook": "رؤيا يوسف… بداية الحكاية 🌙",
                   "scenes": ["desert night", "well stone"]})
    if kept["hook"] != "رؤيا يوسف… بداية الحكاية 🌙":
        errs.append("مسح هوك مكتوب: " + kept["hook"])
    generic = awaken({"kind": "story", "plan_kind": "qissa", "who": "موسى",
                      "hook": "قصة من القرآن 🤍"})
    if "موسى" not in generic["hook"]:
        errs.append("القصة العامة ما اتسمتش: " + generic["hook"])
    if len(generic.get("scenes") or []) < 2:
        errs.append("مشاهد القصة أقل من لقطتين")
    quiz = hook_from_text("إنا أنزلناه في ليلة القدر", kind="quiz")
    if quotes_verse(quiz, "إنا أنزلناه في ليلة القدر"):
        errs.append("الكويز بينطق الآية قبل التلاوة: " + quiz)
    if "من أي سورة" not in quiz:
        errs.append("الكويز ما سألش: " + quiz)
    if BUDGET["quiz"] > 60 or BUDGET["qissa"] < 150:
        errs.append("ميزانية الأنواع مش ماشية مع طبيعة الفيديو")
    verse = "قلنا يا نار كوني بردا وسلاما على ابراهيم"
    taf = "قلنا يا نار كوني بردا أي صيري بردا وسلاما فلا تؤذيه"
    cleaned = without_verse(taf, verse)
    if quotes_verse(cleaned, verse):
        errs.append("الشرح لسه بيقتبس الآية: " + cleaned)
    if "تؤذيه" not in cleaned and "صيري" not in cleaned:
        errs.append("الشرح ضيّع المعنى: " + cleaned)
    lt = long_title("qissa", "يوسف · يعقوب · موسى")
    if "تلاوة" in lt or "يوسف" not in lt:
        errs.append("عنوان الطويل لسه قالب: " + lt)
    if "تلاوة" not in long_title("quran", "الرحمن"):
        errs.append("سورة كاملة لازم تقول إنها تلاوة")
    t = title_of(kind="hadith", hook="إنما الأعمال بالنيات", ref="البخاري")
    if "تلاوة" in t or "البخاري" not in t:
        errs.append("عنوان الحديث غلط: " + t)
    if speech_room(40) < 100 or speech_room(170) > 10:
        errs.append("ميزانية الشرح مش ماشية مع حد الشورت")
    if not (SHORT_MIN == 8 and SHORT_MAX == 175):
        errs.append("حد الشورت مش 8–175")
    need = {"quran", "tafsir", "hadith", "qissa", "asma", "athkar", "dua",
            "quiz", "spirit", "mujiza", "hamd", "nasr", "salah", "hijri",
            "qfacts", "proverb"}
    missing = need - set(ROUTES)
    if missing:
        errs.append("أنواع بلا طريق: " + ",".join(sorted(missing)))
    if errs:
        print("FAIL")
        for e in errs:
            print(" -", e)
        return 1
    print("sense ok", len(ROUTES), "routes", "short", SHORT_MIN, SHORT_MAX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
