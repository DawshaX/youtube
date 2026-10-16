"""📝 محرّك الميتاداتا الاحترافي — العنوان والوصف والوسوم.

المبادئ (مبنية على تحليل حقيقي لأنماط يوتيوب 2025–2026):

    **العنوان**
      · أول ٤٥ حرف أهم حاجة — الباقي بيتقص في الموبايل.
      · **الفائدة/الإحساس قبل الاسم** — «هينتهي همّك» أقوى من «سورة الشرح».
      · الكلمة المفتاحية (اسم السورة/الموضوع) لازم تكون موجودة — للبحث.
      · إيموجي واحد أو اتنين مش أكتر — الأكتر = إشارة «بوت».
      · رقم محدد بيرفع النقر («٣» · «آية ١٣» · «في ٦٠ ثانية»).

    **الوصف**
      · أول ١٥٠ حرف بيظهروا في نتايج البحث — لازم يحملوا الفايدة والكلمة.
      · النص الكامل بعد كده (يوتيوب بيقراه للفهرسة + العمق).
      · الإسناد والمصادر (مصداقية + شرط الترخيص).
      · دعوة تفاعل واحدة واضحة، مش ٣.
      · هاشتاجات في الآخر، ٣-٥ بس، أول واحد #shorts.

    **الوسوم**
      · مش بتأثر في الترتيب تقريبًا، لكن بتساعد في الفهم. 12-15 وسم كفاية.
      · مزيج: عام + محدد + قارئ + إنجليزي.
"""
from __future__ import annotations

import os
import re
from typing import Iterable

BRAND = os.environ.get("NOOR_CHANNEL_NAME") or "روح الله"

# إيموجي معتمدة بالمعنى (مش عشوائية)
EMOJI = {
    "قلب": "🤍", "نور": "✨", "هدوء": "🕊️", "دعاء": "🤲", "علم": "🧠",
    "خير": "🌿", "فرج": "🌤️", "قصة": "📖", "حديث": "📜", "قرآن": "🕌",
    "أمل": "🌱", "وقت": "⏳", "قوة": "💪", "ذكر": "📿", "سكينة": "☁️",
}

# ─────────────────────────────────────────────────────────────────────
# العنوانات — كل قالب اتصمّم لحاجة، و{kw} بتتحطّ عليها الكلمة المفتاحية
# ─────────────────────────────────────────────────────────────────────
TITLE_PATTERNS = {
    "ayah": (
        "{hook} | سورة {kw} {num}",
        "{hook} 🤍 سورة {kw} — {num} | تلاوة {rec}",
        "{hook} | {kw} {num} 🤍",
        "{num} من سورة {kw}… {hook}",
    ),
    "hadith": (
        "{hook} 📜 حديث صحيح — {kw}",
        "{hook} | من {kw} 🤍",
        "قال النبي ﷺ… {hook} | {kw}",
    ),
    "dua": (
        "{hook} 🤲 دعاء من القرآن | {kw}",
        "{hook} | دعاء {kw} 🤲",
        "علّم قلبك يدعي: {hook} 🤲 {kw}",
    ),
    "story": (
        "{hook} 📖 | قصة {kw}",
        "{hook}… قصة {kw} كاملة 📖",
        "قصة {kw}: {hook} 📖",
    ),
    "quiz": (
        "{hook} 🤔 | اختبر معرفتك",
        "{hook}… تعرف الإجابة؟ 🧠",
        "سؤال وسؤال: {hook} | كويز",
    ),
    "science": (
        "{hook} 🧠 | معلومة تُضيء",
        "{hook}… سبحان الله 🧠",
        "{hook} | {kw} 🧠",
    ),
    "qfacts": (
        "معلومة تُضيء: {hook} 💡",
        "{hook} 💡 | هل تعلم؟",
        "{hook} | معلومات قرآنية 💡",
    ),
    "proverb": (
        "{hook} 🌿 | حكمة",
        "{hook}… من {kw} 🌿",
    ),
    "life": (
        "{hook} 🌿",
        "{hook} | {kw} 🌿",
        "{hook}… جرّب كده 🌿",
    ),
    "salah": (
        "مواقيت الصلاة النهاردة {kw} 🕌",
        "{hook} 🕌 | مواقيت الصلاة",
    ),
    "hijri": (
        "{hook} 🌙 | التقويم الهجري",
        "النهاردة {kw} هجريًا 🌙",
    ),
    "athkar": (
        "{hook} 📿 | أذكار",
        "{hook}… اقراها وارتاح 📿",
    ),
    "asma": (
        "{hook} | أسماء الله الحسنى ✨",
        "{hook}… معنى جميل ✨",
    ),
}


def _emoji_re() -> str:
    return r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"


def _same_ish(a: str, b: str) -> bool:
    """هل النصين نفس المعنى تقريبًا؟ (للحماية من العنوان المكرّر)"""
    a, b = _clean(a).lower(), _clean(b).lower()
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    wa, wb = set(a.split()), set(b.split())
    if not wa or not wb:
        return False
    return len(wa & wb) / float(min(len(wa), len(wb))) >= 0.6


def _clean(text: str, limit: int = 0) -> str:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if limit and len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0].rstrip("،,.…") + "…"
    return t


def _emoji_for(item: dict, kind: str) -> str:
    blob = f"{item.get('emotion', '')} {item.get('field', '')} {item.get('theme', '')} {kind}"
    for key, ch in EMOJI.items():
        if key in blob:
            return ch
    return ""


def _num_of(item: dict) -> str:
    a, b = item.get("ayah"), item.get("ayah_to")
    if a and b and str(b) != str(a):
        return f"الآيات {a}–{b}"
    if a:
        return f"آية {a}"
    return ""


def title_for(item: dict, *, hook: str = "", kind: str = "", kw: str = "",
              reciter: str = "", ref: str = "", long_title: str = "") -> str:
    """يبني عنوان احترافي مُحسَّن للنقر والبحث.

    آمن: لو مفيش قوالب للنوع، بيرجّع الوصلة الأصلية زي ما هي.
    """
    if long_title:
        return _clean(long_title, 100)

    k = str(kind or item.get("kind") or item.get("plan_kind") or "life")
    h = _clean(hook or item.get("hook") or item.get("title") or "", 62)

    # 🛡️ عنوان الطويل (حلقات الساعات) مكتوب بإيد في مصنع الطويل وجواه المدة
    #    الحقيقية بالدقيقة — فمفيش أي قالب يزوّده أو يكرّره. بنسيبه زي ما هو.
    #    (باج حقيقي 2026-10-16: الطويل كان عنوانه بيتكرّر مرتين لأن الـkw
    #     بتاعه هو نفسه عنوانه — القالب «{hook} | {kw} 🌿» طبعه مرتين.)
    if k in ("long", "long_qissa", "long_story"):
        out = _clean(long_title or h or "فيديو هادئ", 100)
        if not re.search(_emoji_re(), out):
            out = f"{out} 🌿"
        return out

    patterns = TITLE_PATTERNS.get(k)
    if not patterns:
        patterns = TITLE_PATTERNS["life"]
    surah = _clean(kw or item.get("surah_name") or item.get("surah")
                   or item.get("theme") or item.get("field") or "", 24)
    rec = _clean(reciter or item.get("reciter_name") or "", 26)
    num = _num_of(item)

    seed = sum(ord(c) for c in str(item.get("id") or item.get("hook") or "نور"))
    # أفضلية أول قالب لو مفيش قارئ (مش بنحط «تلاوة » فاضية)
    # 🛡️ لو الـkw مكرّر للهوك (أو جزء منه) نشيله — من غير عنوان مكرّر
    if surah and _same_ish(surah, h):
        surah = ""

    usable = [p for p in patterns if "{rec}" not in p or rec]
    tpl = usable[seed % len(usable)] if usable else patterns[0]

    out = tpl.format(hook=h, kw=surah, num=num, rec=rec).strip()
    # لمسة نظافة: قوالب كان فيها {kw} ومفيش kw ⇒ فاضلة «| 🌿» أو «| » — تتلمّ
    out = re.sub(r"\s*[|—]\s*(?=" + _emoji_re() + ")", " ", out)
    out = re.sub(r"\s*[|—]\s*$", "", out)
    out = re.sub(r"\s*[|—]\s*(?=[|—])", " ", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" |—.")
    if not out:
        out = h or "آية وسكينة"

    # إيموجي احتياطي لو مفيش أي إيموجي
    if not re.search(_emoji_re(), out):
        out = f"{out} {_emoji_for(item, k) or '🤍'}".strip()
    return _clean(out, 95)


def description_for(item: dict, *, hook: str = "", body: str = "", ref: str = "",
                    sources: Iterable[str] = (), kind: str = "",
                    reciter: str = "", mood_credit: str = "",
                    effects: Iterable[str] = (), extra_tags: str = "",
                    brand: str = "") -> str:
    """يبني وصف كامل: فايدة أولًا → نص → إسناد → شكر → تفاعل → هاشتاجات."""
    brand = brand or BRAND
    k = str(kind or item.get("kind") or item.get("plan_kind") or "life")
    h = _clean(hook or item.get("hook") or "", 220)

    # ── ١) أول سطرين: الأهم للبحث والقرار (يوتيوب بيقتطع بعد ~١٥٠ حرف)
    first = h if h else _clean(body, 140)
    opening = f"{first}\n\n"

    # ── ٢) سياق قصير بيقوّي الفهم
    ctx_bits: list[str] = []
    if ref:
        ctx_bits.append(f"﴿ {ref} ﴾")
    if reciter:
        ctx_bits.append(f"🎙️ تلاوة: {reciter}")
    context = ("\n".join(ctx_bits) + "\n\n") if ctx_bits else ""

    # ── ٣) النص الكامل (عمق للفهرسة + قيمة للمشاهد)
    text = _clean(body, 2200)
    text_block = f"{text}\n\n" if text and text not in opening else ""

    # ── ٤) الإسناد والمصادر
    src_lines = []
    for s in sources:
        s = str(s or "").strip()
        if s:
            src_lines.append(s if s.startswith(("📚", "🧩", "🎵", "🎬", "🎞️")) else f"📚 {s}")
    if mood_credit:
        src_lines.append(mood_credit)
    eff = [e for e in effects if e]
    if eff:
        src_lines.append("🎞️ الاستوديو: " + " · ".join(eff[:5]))
    src_lines.append("🚫 صفر موسيقى محفوظة · صفر لقطات مسروقة · كل ميديا مرخّصة أو مولّدة للمصنع.")
    sources_block = "\n".join(src_lines) + "\n\n"

    # ── ٥) دعوة تفاعل واحدة واضحة (مش ٣) — و**متنوّعة لكل حلقة** (ممنوع قالب
    #    ثابت: سياسة ٢٠٢٦ بتعاقب التكرار الحرفي)
    if str(k).startswith("long"):
        seed_cta = sum(ord(c) for c in str(item.get("id") or hook or brand))
        long_ctas = (
            f"🤍 الجلسة كلها شغل هادي ومفيد — لو وصلت لآخرها اكتب في تعليق "
            f"أي جزء لمس قلبك.\n🔔 ولو حابب النور يكمل معاك: اشترك في «{brand}» "
            f"وفعّل الجرس، فيديو طويل جديد كل ما يجي وقته.",
            f"🤍 خد منها اللي تحتاجه وارجعلها وقت ما تحب — الفيديو مقسّم "
            f"بفهرس فوق تنقّل من غير ما تتوه.\n🔔 اشترك في «{brand}» عشان "
            f"الجلسات الجاية توصلك لوحدها.",
            f"🤍 لو الجلسة دي هدّت قلبك، ابعت النصيحة لحد يهمك — الدال على "
            f"الخير كفاعله.\n🔔 واشترك في «{brand}» — كل حلقة بتتصنع مخصوصة، "
            f"مش نسخة من اللي قبلها.",
        )
        cta = long_ctas[seed_cta % len(long_ctas)]
    else:
        cta = (
            f"🤍 لو الكلام ده أفادك: اكتب اللي حسّيته في تعليق، وابعت الفيديو "
            f"لحد يهمك — الدال على الخير كفاعله.\n"
            f"🔔 اشترك في «{brand}» وفعّل الجرس — آية وسكينة وحديث صحيح كل ساعة."
        )

    # ── ٦) هاشتاجات: ٥ بالكتير، الأول #shorts دايمًا
    tags = _hashtags(k, extra_tags)

    tail = "\n\n" + cta + "\n\n" + tags

    room = 4900 - len(opening) - len(context) - len(text_block) - len(sources_block) - len(tail)
    if room < 0:
        text_block = ""
        room = 4900 - len(opening) - len(context) - len(sources_block) - len(tail)
        if room < 0:
            sources_block = ""
            room = 4900 - len(opening) - len(context) - len(tail)
            if room < 0:
                # آخر خط دفاع: نقصّ من المتن نفسه (الوصف ما يتجاوزش حد يوتيوب أبدًا)
                keep = max(0, len(context) + room)
                context = context[:keep].rstrip(" \n،,")
    out = opening + context + text_block + sources_block + tail
    # ضمان نهائي بالحساب: الحد ٥٠٠٠ في يوتيوب، واحنا بنسيب هامش ١٠٠ حرف
    return out[:4900]


def _hashtags(kind: str, extra: str = "") -> str:
    base = {
        "ayah": "#shorts #قرآن #تلاوة_خاشعة #تدبر #آية_وسكينة",
        "quran": "#shorts #قرآن #تلاوة_خاشعة #سكينة #تدبر",
        "hadith": "#shorts #حديث_صحيح #السنة_النبوية #تذكير #إسلاميات",
        "dua": "#shorts #دعاء #أدعية #سكينة #قلب_مطمئن",
        "story": "#shorts #قصص_الأنبياء #قصص_القرآن #عبرة #إسلاميات",
        "quiz": "#shorts #كويز #اختبر_معرفتك #معلومات_إسلامية #تحدي",
        "science": "#shorts #معلومة #هل_تعلم #علم #إفادة",
        "qfacts": "#shorts #معلومات_قرآنية #هل_تعلم #إسلاميات #تدبر",
        "life": "#shorts #حياة #نصيحة #خير #هدوء",
        "proverb": "#shorts #حكمة #أمثال #تراث #عبرة",
        "salah": "#shorts #مواقيت_الصلاة #الصلاة #أذان #إسلاميات",
        "hijri": "#shorts #التقويم_الهجري #رمضان #مناسبات #إسلاميات",
        "athkar": "#shorts #أذكار #ذكر_الله #حصن_المسلم #تسبيح",
        "asma": "#shorts #أسماء_الله_الحسنى #توحيد #إسلاميات #تأمل",
        # 🎥 الفيديو الطويل **مش شورت** — وسم #shorts على حلقة ١٠ دقايق بيلخبط
        #    التصنيف في نظر يوتيوب وضد قواعده. فالطويل ليه مجموعته الخاصة.
        "long": "#تدبر #قرآن #سكينة #جلسة_إيمانية #تذكير",
        "long_qissa": "#قصص_القرآن #تدبر #عبرة #قرآن #سكينة",
        "long_story": "#قصص_القرآن #تدبر #عبرة #قرآن #سكينة",
    }.get(kind)
    if not base:
        base = ("#نور #خير #هدوء #إفادة #تذكير" if str(kind).startswith("long")
                else "#shorts #نور #خير #هدوء #إفادة")
    extra = " ".join(str(extra or "").split()[:4])
    return f"{base} {extra}".strip()


def tags_for(item: dict, *, kind: str = "", kw: str = "", reciter: str = "",
             book: str = "") -> list[str]:
    """١٥ وسم مركّز: عام + محدد + قارئ + إنجليزي."""
    k = str(kind or item.get("kind") or "life")
    kw = _clean(kw or item.get("surah_name") or item.get("theme") or "", 30)
    who = _clean(item.get("who") or "", 24)

    heads = {
        "ayah": ["آيات قرآنية", f"سورة {kw}" if kw else "قرآن كريم", "تلاوة خاشعة", "تدبر القرآن", "آية وسكينة"],
        "quran": ["قرآن كريم", f"سورة {kw}" if kw else "سور قرآنية", "تلاوة هادئة", "سكينة", "تلاوة قبل النوم"],
        "hadith": ["حديث صحيح", "أحاديث نبوية", book or "صحيح البخاري", "السنة النبوية", "تذكير"],
        "dua": ["دعاء", "أدعية قرآنية", "دعاء مستجاب", "سكينة", "قلب مطمئن"],
        "story": [f"قصة {who}" if who else "قصص القرآن", "قصص الأنبياء", "قصص إسلامية", "عبرة", "تلاوة خاشعة"],
        "quiz": ["كويز إسلامي", "اختبر معرفتك", "أسئلة دينية", "من أي سورة", "تحدي قرآني"],
        "science": ["معلومات عامة", "هل تعلم", "حقائق علمية", "إفادة", "معلومة تُضيء"],
        "qfacts": ["معلومات قرآنية", "هل تعلم", "القرآن الكريم", "معلومات إسلامية", "quran facts"],
        "life": ["نصائح حياة", "حكمة", "تطوير ذات", "هدوء", "كلمة تنفع"],
        "proverb": ["أمثال عربية", "حكمة", "أقوال", "تراث", "wisdom"],
        "salah": ["مواقيت الصلاة", "أوقات الصلاة", "الصلاة", "أذان", "prayer times"],
        "hijri": ["التقويم الهجري", "التاريخ الهجري", "مناسبات إسلامية", "hijri date", "رمضان"],
        "athkar": ["أذكار", "حصن المسلم", "أذكار الصباح والمساء", "ذكر الله", "تسبيح"],
        "long": ["فيديو طويل", f"{kw}" if kw else "جلسة هادئة", "تدبر القرآن",
                 "تذكير", "راحة نفسية"],
        "long_qissa": ["قصص القرآن", "عبرة", f"{kw}" if kw else "تدبر", "فيديو طويل", "سكينة"],
        "long_story": ["قصص القرآن", "عبرة", f"{kw}" if kw else "تدبر", "فيديو طويل", "سكينة"],
        "asma": ["أسماء الله الحسنى", "التوحيد", "معاني أسماء الله", "أسماء الله", "إسلاميات"],
    }.get(k, ["نور", "خير", "إفادة", "هدوء", "كلمة تنفع"])

    long_form = str(k).startswith("long")
    core_ar = (["جلسة إيمانية", "تذكير", "نور", "راحة نفسية", "فيديو طويل"]
               if long_form else
               ["إسلاميات", "تذكير", "نور", "راحة نفسية", "محتوى هادف"])
    core_en = (["long video", "islamic", "quran", "reminder", "peaceful"]
               if long_form else
               ["shorts", "islamic", "quran", "reminder", "peaceful"])

    out, seen = [], set()
    for t in [*heads, *([reciter] if reciter else []), *core_ar, *core_en]:
        t = _clean(t, 40)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out[:15]


def pinned_comment(item: dict, *, hook: str = "", kind: str = "") -> str:
    """تعليق مثبّت — بيرفع التفاعل وبيوجّه المحادثة (إشارة قوية للخوارزمية)."""
    k = str(kind or item.get("kind") or "life")
    prompts = {
        "ayah": "الآية دي لمسّت فيك إيه؟ اكتب كلمة 🤍",
        "hadith": "إيه اللي هتطبّقه من الحديث ده النهاردة؟",
        "dua": "اكتب «آمين» وشاركنا دعوتك 🤲",
        "story": "إيه الدرس اللي خدته من القصة دي؟",
        "quiz": "اكتب إجابتك قبل ما تشوف الآخر 👀",
        "science": "معلومة جديدة عليك؟ قولّنا 💡",
        "life": "جرّبت الحاجة دي قبل كده؟ احكيلنا 🌿",
        "qfacts": "عرفت المعلومة دي قبل كده؟ 💡",
        "proverb": "المثل ده فكّرك بإيه؟ 🌿",
        # 🎥 الطويل: سؤال يفتح حوار حقيقي على فيديو ١٠ دقايق (التعليق = إشارة قوية)
        "long": "من الفهرس اللي في الوصف… أي جزء تحب أعملك جلسة أطول عنه؟ 🤍",
        "long_qissa": "إيه اللي وقف معاك في القصة دي؟ اكتبه وشاركنا 🤍",
        "long_story": "إيه اللي وقف معاك في القصة دي؟ اكتبه وشاركنا 🤍",
    }
    return prompts.get(k, "قولّنا رأيك في تعليق 🤍")


def short_for(item: dict, *, hook: str = "", kind: str = "") -> str:
    """نص الوصف المختصر لـShorts/Reels (المطلوب في منصات تانية)."""
    h = _clean(hook or item.get("hook") or "", 110)
    return f"{h}\n\n{_hashtags(str(kind or 'life'))}"
