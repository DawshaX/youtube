#!/usr/bin/env python3
"""🎥 مصنع الطويل — يحوّل المكتبة القصيرة لحلقات **٩–١٥ دقيقة** حقيقية.

**المشكلة اللي بيحلّها (مقيسة):**
المكتبة فيها ٤٥٦ حلقة قصيرة (١٢–١٥ ثانية كلام)، وأطول حاجة فيها اسمها
«طويل» = **١١٤ كلمة ≈ ٤٥ ثانية**. يعني القناة مش عندها «طويل» أصلًا.
ووقت المشاهدة (وهو اللي بيجيب المشتركين ويوتيوب بيوزّع بسببه) بيتولّد من
الطويل، مش من ١٥ ثانية.

**طريقة العمل:**
١) بيلمّ السلاسل المتقاربة في **مجموعة** بموضوع واحد («بيت أهدى»…).
٢) بيبني نص واحد متصل: مقدمة → فصول بتجمّع حلقات موضوع واحد → خلاصة
   عملية → خاتمة. كل جملة من كلام المكتبة **الأصلي** (مفيش كلام ملفّق).
٣) بيكتب الناتج كحلقة **واحدة طويلة** في نفس ملف المكتبة — فالمحرّك
   الحالي نفسه (noor_one → noor_next.produce) بيرندرها زي أي حلقة.
   يعني **مفيش مسار جديد يتعطّل** ومفيش كود قديم بيتشال.

**قاعدة التكرار:** كل مجموعة بتاخد مقدمة وخاتمة ووصلات **خاصة بيها**
(مش نفس القالب على الكل) — عشان ما نقعش في «المحتوى المتشابه» تاني.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LIB = ROOT / "data" / "noor_next" / "one_library.jsonl"

# ── مجموعات الموضوع الواحد: (المعرّف، العنوان، السلاسل، الفصول، مقدمة، خاتمة)
#    قائمة السلاسل **مرشّحين مرتّبين** — البرنامج بياخد منهم لحد ما يوصل
#    الطول المستهدف، لأن نص المكتبة متكرر (اتأكدنا بالقياس: ~٥٠٪ تكرار)،
#    فمجموعة من ٤ سلاسل بتطلّع ٥ دقايق بس مش ١٠.
COLLECTIONS = [
    {
        "id": "bayt",
        "title": "بيت أهدى: رحلة {m} دقيقة لبيت مرتاح",
        "series": ["ser-family", "ser-clean", "ser-kitchen", "ser-host",
                   "ser-field-بيت", "ser-field-ملابس", "ser-field-هندام",
                   "ser-plant", "ser-field-درج", "ser-field-ثلاجة",
                   "ser-field-خضار", "ser-field-شوربة", "ser-field-حديقة"],
        "chapters": ["الأهل", "البيت", "المطبخ", "الضيافة", "الترتيب",
                     "الملابس", "الهندام", "الزرع", "الأدراج", "الثلاجة",
                     "الخضار", "الشوربة", "الحديقة"],
        "open": ("مش محتاج تغيّر حياتك كلها. محتاج تفهم حاجات صغيرة، وتعملها "
                 "واحدة واحدة. الجلسة دي معاك على مهلك: أهل بيتك، ثم أوضتك "
                 "ومطبخك، وبعدها حاجات صغيرة بتفرق كل يوم."),
        "close": ("خلاصة الجلسة: أهل بيتك أولى بحسنك، والبيت المرتّب بيريح "
                  "راسك، والمطبخ الآمن بيحميك، والتفاصيل الصغيرة بتجمّع "
                  "راحة. تجيب حاجة واحدة من الجلسة دي النهاردة."),
    },
    {
        "id": "yom",
        "title": "يوم مرتّب: رحلة {m} دقيقة ترجّعلك وقتك",
        "series": ["ser-day", "ser-study", "ser-road", "ser-queue",
                   "ser-field-ساعة", "ser-field-عادة", "ser-field-امتحان",
                   "ser-field-إيقاع", "ser-field-صباح", "ser-field-سفر",
                   "ser-field-مطار", "ser-field-شغل", "ser-field-مدرسة"],
        "chapters": ["طرف النهار", "المذاكرة", "الطريق", "الزحمة", "الساعة",
                     "العادة", "الامتحان", "الإيقاع", "الصباح", "السفر",
                     "المطار", "الشغل", "المدرسة"],
        "open": ("الوقت مش بيضيع مرّة واحدة. بيضيع حتّة حتّة: في الصبح، وفي "
                 "المذاكرة، وفي الطريق، وفي الطابور. الجلسة دي بنمشي على "
                 "الحاجات دي بالترتيب، ونطلّع وقتك من إيدهم."),
        "close": ("خلاصة الجلسة: صبحك بيحدّد نهارك، والمذاكرة نظام مش مزاج، "
                  "وطريقك له أدب، وزحمتك بتفوت. لو نفّذت واحد بس منهم كل "
                  "يوم، بعد شهر هتحس إن نهارك بقى أطول."),
    },
    {
        "id": "nafas",
        "title": "نَفَس أوسع: رحلة {m} دقيقة هدوء في يوم ضاغط",
        "series": ["ser-sky", "ser-rain", "ser-field-لحظة", "ser-body",
                   "ser-field-بحر", "ser-field-طبيعة", "ser-field-فصول",
                   "ser-field-ظل", "ser-field-جبل", "ser-field-صحرا",
                   "ser-field-طير", "ser-field-نمل", "ser-field-نخلة"],
        "chapters": ["السماء", "المطر", "اللحظة", "الجسم", "البحر", "الطبيعة",
                     "الفصول", "الظل", "الجبل", "الصحرا", "الطير", "النمل",
                     "النخلة"],
        "open": ("لو يومك ضاغط، الجلسة دي اتفرغت عشانك. مش هنطلب منك تعمل "
                 "حاجة كبيرة. هنبصّ لفوق شوية، ونسمع المطر، ونفهم إزاي تلحق "
                 "اللحظة اللي انت فيها، وإن شاء الله تطلع من هنا أهدى."),
        "close": ("خلاصة الجلسة: لما تلاقي نفسك مضغوط، ابصّ لفوق، واسمع "
                  "اللي حواليك، وارجع للحظة اللي انت فيها. الجسم بيمشي مع "
                  "النَفَس — خد نَفَس هادي وهيكمّل."),
    },
    {
        "id": "lisan",
        "title": "لسان وكلمة: رحلة {m} دقيقة تحفظ لسانك",
        "series": ["ser-lang", "ser-tongue", "ser-field-ضحك نظيف",
                   "ser-field-عبرة", "ser-field-صدى", "ser-field-صوت",
                   "ser-field-مقال", "ser-field-ناس", "ser-field-صداقة",
                   "ser-field-ضحك", "ser-field-نكشة", "ser-field-استماع",
                   "ser-field-خفة", "ser-field-مقابلة"],
        "chapters": ["الكلمة", "الإشاعة", "الضحك", "العبرة", "الصدى", "الصوت",
                     "المقال", "الناس", "الصداقة", "الضحك", "النكشة",
                     "الاستماع", "الخفة", "المقابلة"],
        "open": ("الكلمة بتخرج من بوقك وتمشي. متقدرش ترجّعها، بس تقدر "
                 "تختارها. الجلسة دي عن الكلمة: إمتى تنفع، وإمتى تسكت، "
                 "وإمتى الضحك بيقرّب وإمتى بيوجع."),
        "close": ("خلاصة الجلسة: الكلمة الطيبة بتفضل، والإشاعة بتوجع ناس مش "
                  "مستاهلة، والضحك النضيف بيجمع، والعبرة بتعلّم من غير "
                  "توبيخ. امبارح كم كلمة ودّك ترجّعها؟"),
    },
    {
        "id": "sitr",
        "title": "ستر ورفق: رحلة {m} دقيقة في حسن الصحبة",
        "series": ["ser-phone", "ser-child", "ser-animal",
                   "ser-field-وهم ونفس", "ser-field-يتيم", "ser-field-حياء",
                   "ser-field-حسد", "ser-field-سلامة", "ser-field-نفس",
                   "ser-field-رزق", "ser-money", "ser-field-تجربة",
                   "ser-field-متحف", "ser-field-وثائقي"],
        "chapters": ["الموبايل", "الطفل", "الحيوان", "الوهم", "اليتيم",
                     "الحياء", "الحسد", "السلامة", "النفس", "الرزق", "المال",
                     "التجربة", "المتحف", "الوثائقي"],
        "open": ("فيه حاجات بنعملها كل يوم وبتقول عننا أكتر من كلامنا: إزاي "
                 "بنستخدم الموبايل، وإزاي بنكلّم الطفل، وإزاي بنعامل "
                 "الحيوان، وإزاي بنتعامل مع وهم جوه نفسنا."),
        "close": ("خلاصة الجلسة: شاشة محدّدة بتحمي بيتك، وطفل بيتسمع له بيكبر "
                  "سويّ، وحيوان بيلاقي رحمة منك، ووهم بيفضل وهم لو سيبته."),
    },
    {
        "id": "iman",
        "title": "إيمان وسكينة: رحلة {m} دقيقة تفكّر وتريّح",
        "series": ["ser-faith", "ser-field-علم الحياة", "ser-field-علم الأرض",
                   "ser-field-سؤال", "ser-field-ذاكرة", "ser-field-حياة",
                   "ser-field-عبرة", "ser-field-تاريخ", "ser-field-خريطة",
                   "ser-field-جغرافيا", "ser-field-فلك".replace("فلك", "فيزياء"),
                   "ser-field-كيمياء", "ser-field-حروف", "ser-field-كتاب"],
        "chapters": ["تذكير", "علم الحياة", "علم الأرض", "سؤال", "الذاكرة",
                     "الحياة", "العبرة", "التاريخ", "الخريطة", "الجغرافيا",
                     "الفيزياء", "الكيمياء", "الحروف", "الكتاب"],
        "open": ("مش هنجبرك على حاجة. هنقرا مع بعض حاجات تفكّر: تذكير خيف، "
                 "وبعدين ننزل نشوف اللي بيتكرر في الحياة، وبعدها الأرض "
                 "وتاريخها، وآخرها سؤال بتنساه وأنت مربوط فيه."),
        "close": ("خلاصة الجلسة: التذكير بيلطّف القلب، وسنن الحياة بتتكرر قبل "
                  "ما فهمها حد، والأرض كتبت تاريخها في الحجر، والسؤال اللي "
                  "بيهزّك هو اللي بيوقفك."),
    },
]

# ── وصلات بين الفصول: كل مجموعة بتاخد مفرداتها (مش نفس القالب)
# ── وصلات الفصول: بنى مختلفة بتدور — عشان ما يبقاش نفس القالب كل مرة
BRIDGE_STYLES = [
    "نبدأ بـ{name}.", "ونروح على {name}.", "بنكمل مع {name}.",
    "محطة {name}.", "وبعدها {name}.", "نقف شوية عند {name}.",
    "ونمسك {name}.", "وتحلية الجلسة {name}.",
]


def _bridge(col_id: str, i: int, name: str) -> str:
    """وصلة الفصل — بتدور على بنى مختلفة، ومتثبّتة لكل مجموعة (مش عشوائية)."""
    import zlib
    slot = (zlib.crc32(f"{col_id}:{i}".encode()) + i) % len(BRIDGE_STYLES)
    return BRIDGE_STYLES[slot].format(name=name)


def _rows() -> list[dict]:
    if not LIB.exists():
        return []
    out = []
    for line in LIB.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def _by_series() -> dict[str, list[dict]]:
    fam: dict[str, list[dict]] = defaultdict(list)
    for row in _rows():
        if row.get("engine") == "life" and row.get("kind") == "short":
            fam[str(row.get("series_id") or "")].append(row)
    for famo in fam.values():
        famo.sort(key=lambda r: int(r.get("episode") or 0))
    return fam


# ── الكتاب التاني: المخزون الديني المنطوق (٢٠٢ صف · ١٨٥ ينفع للطويل)
#    ليه ده مهم؟ الطويل محتاج **وقود مستمر**. حلقات الأصناف بتطلّع ~١٨ حلقة
#    طويلة بس (المكتبة كلها ٤٥٦ حلقة قصيرة ≈ ٢٤ ألف كلمة). المخزون الديني
#    (أدعية/أذكار/أحاديث/معلومات) بيضيف وقود تاني بنفس الأسلوب، وكل جملة
#    من النص الأصلي الموثّق — بلا تأليف وبلا زيادة.
RELIGIOUS = [
    {
        "id": "adhkar",
        "title": "أذكار تريّح قلبك: جلسة {m} دقيقة",
        "shelves": ["ذكر من المصدر", "دعاء من المصدر"],
        "open": ("الجلسة دي معاك على مهلك. مش محتاج تحفظ حاجة، ولا تلزم نفسك "
                 "بعدد. اسمع الذكر مرة، ولو عجبك كرّره في يومك. "
                 "بسم الله نبدأ."),
        "close": ("لو وصلت لآخر الجلسة، خُد ذكر واحد بس وكرّره النهاردة. "
                  "الذكر اللي بيثبت هو اللي بيبقى معاك في يومك."),
    },
    {
        "id": "duaa",
        "title": "أدعية من الكتاب والسنّة: جلسة {m} دقيقة",
        "shelves": ["دعاء من المصدر", "ذكر من المصدر"],
        "open": ("الأدعية دي مش كلام نتألّفه — دي أدعية محفوظة من الكتاب "
                 "والسنة، بنسمعها مع بعض بالترتيب. ادعي بواحد بس بقلب حاضر، "
                 "خير من كتير بصوت سايب."),
        "close": ("خد دعوة واحدة بس من الجلسة دي وكرّرها كل يوم. "
                  "الدعاء اللي بيصبر عليه صاحبه هو اللي بيفرحه."),
    },
    {
        "id": "hadith-silsila",
        "title": "من كلام النبي ﷺ ومعلومة تنفع: جلسة {m} دقيقة",
        "shelves": ["حديث من المصدر", "معلومة من المصدر"],
        "open": ("هنسمع مع بعض أحاديث صحيحة، واحدة واحدة، بلا شرح طويل "
                 "وبلا تأويل من عندنا. الحديث له مصدره مكتوب في الوصف، "
                 "وشوف بعينك قبل ما تنقل."),
        "close": ("خد حديث واحد بس من اللي سمعته، ونفّذه النهاردة. "
                  "العلم اللي بيتعمل بيه هو اللي ينفع صاحبه."),
    },
    {
        "id": "maarifa",
        "title": "معلومات تنفعك: جلسة {m} دقيقة",
        "shelves": ["معلومة من المصدر"],
        "open": ("جلسة معلومة، كل معلومة معاها مصدرها. مفيش أرقام من دماغنا "
                 "ومفيش مبالغة — انت حر تراجع كل حاجة بنفسك."),
        "close": ("المعرفة اللي بتفضل معاك هي اللي بتحلّ مشكلة عندك فعلًا. "
                  "خد معلومة واحدة وجرّبها."),
    },
    {
        "id": "jalsa",
        "title": "جلسة ذكر وحكمة: {m} دقيقة مع الكتاب والسنة",
        "shelves": ["ذكر من المصدر", "دعاء من المصدر", "حديث من المصدر",
                    "معلومة من المصدر"],
        "open": ("الجلسة دي جامعة: ذكر، ودعاء، وكلام من النبي ﷺ، ومعلومة تنفعك. "
                 "خدها على مهلك — مش مطلوب منك تسمعها كلها في مرة. "
                 "لو وقفت عند حاجة أثّرت فيك، ارجع لها تاني."),
        "close": ("اللي بينفع مش اللي سمعته، اللي عملت بيه. خد واحد بس "
                  "من الجلسة دي — ذكر تلزمه، أو دعاء تدعو بيه، أو عمل "
                  "تعمله — وريّح قلبك."),
    },
]


# ── دفعة تانية من المجموعات: بتغطّي باقي المكتبة (١٤ + ١٤ + ...)
COLLECTIONS_B = [
    {
        "id": "ilm",
        "title": "علم وحياة: {m} دقيقة تفهم بيها اللي حواليك",
        "series": ["ser-field-علم الحياة", "ser-field-علم الأرض",
                   "ser-field-فيزياء", "ser-field-كيمياء", "ser-field-جغرافيا",
                   "ser-field-خريطة", "ser-field-تاريخ", "ser-field-أرض",
                   "ser-field-صخر", "ser-field-قمح", "ser-field-خضار",
                   "ser-field-مغناطيس", "ser-field-كثافة", "ser-field-رقم"],
        "chapters": ["علم الحياة", "علم الأرض", "الفيزياء", "الكيمياء",
                     "الجغرافيا", "الخريطة", "التاريخ", "الأرض", "الصخر",
                     "القمح", "الخضار", "المغناطيس", "الكثافة", "الرقم"],
        "open": ("اللي حواليك مش مبهم. كل حاجة ليها سبب تقدر تفهمه، ولو فهمته "
                 "بتعيش أهدى ومتخافش من وهم. الجلسة دي مش امتحان — دي فهم "
                 "هادى لحاجات بتشوفها كل يوم."),
        "close": ("خلاصة الجلسة: اللي فهمته مش هيتوهك. مفيش خرافة تقف قصاد "
                  "حقيقة عارفة تفسيرها. خد معلومة واحدة النهاردة وشوف إزاي "
                  "تغيّر نظرتك لحاجة كنت خايف منها."),
    },
    {
        "id": "shughl",
        "title": "شغل وحرفة: {m} دقيقة في أصول الصنعة",
        "series": ["ser-field-شغل", "ser-field-حرفة", "ser-field-نجارة",
                   "ser-field-هندسة", "ser-field-بناء", "ser-field-تصميم",
                   "ser-field-خياطة", "ser-field-حروف", "ser-field-خط",
                   "ser-field-ورق", "ser-field-كتاب", "ser-field-مقال",
                   "ser-field-فلتر", "ser-field-لقطة"],
        "chapters": ["الشغل", "الحرفة", "النجارة", "الهندسة", "البناء",
                     "التصميم", "الخياطة", "الحروف", "الخط", "الورق",
                     "الكتاب", "المقال", "الفلتر", "اللقطة"],
        "open": ("الصنعة مش موهبة غامضة — أصول بتتعلمها وتتكرر. الجلسة دي "
                 "عن الشغل بإيدك: من النجارة للخياطة للهندسة للتصميم. "
                 "بلا كلام كبير، أصول تنفعك في شغلك."),
        "close": ("خلاصة الجلسة: الشغل النضيف بيبان. الأصول بتوفر وقتك "
                  "وتمنع غلطك. خد أصل واحد من الجلسة دي وطبّقه في أول "
                  "شغلة تعملها."),
    },
    {
        "id": "safar",
        "title": "طريق وسفر: {m} دقيقة قبل ما تتحرك",
        "series": ["ser-field-سفر", "ser-field-مطار", "ser-field-طريق",
                   "ser-road", "ser-field-مدرسة", "ser-field-مقعد",
                   "ser-field-مقابلة", "ser-field-اجتماع", "ser-field-ساعة",
                   "ser-field-صباح", "ser-field-إعادة", "ser-field-درج"],
        "chapters": ["السفر", "المطار", "الطريق", "الشارع", "المدرسة",
                     "المقعد", "المقابلة", "الاجتماع", "الساعة", "الصباح",
                     "الإعادة", "الدرج"],
        "open": ("أي مشوار — ولو صغير — له أصول تخلّيه أسهل: قبل ما تتحرك، "
                 "وإنت في الطريق، ولما توصل. الجلسة دي بتجهّزك للمشوار "
                 "قبل ما تبدأه."),
        "close": ("خلاصة الجلسة: التجهيز قبل الحركة بيوفر عليك كل حاجة. "
                  "خد حاجة واحدة بس من الجلسة، وحطّها في شنطة المشوار "
                  "الجاي."),
    },
    {
        "id": "seha",
        "title": "عافية وراحة: {m} دقيقة لجسمك ونَفَسك",
        "series": ["ser-field-رياضة", "ser-field-جسم ونَفَس", "ser-body",
                   "ser-field-ملعب", "ser-field-عين", "ser-field-ظل",
                   "ser-field-طقس", "ser-field-فصول", "ser-field-حديقة",
                   "ser-field-خضار", "ser-field-أكل", "ser-field-ثلاجة"],
        "chapters": ["الرياضة", "الجسم والنَفَس", "الجسم", "الملعب", "العين",
                     "الظل", "الطقس", "الفصول", "الحديقة", "الخضار",
                     "الأكل", "الثلاجة"],
        "open": ("مش هنوعدك بعلاج ولا بمعجزة — وعدنا الصدق. الجلسة دي عن "
                 "حاجات بسيطة بتفرق في جسمك: حركة، ونَفَس، وعين بتريّح، "
                 "وموسم بتتأقلم معاه، وأكل بتخزنه صح. ولو في أي شكوى صحية، "
                 "الدكتور أولى."),
        "close": ("خلاصة الجلسة: الحركة الخفيفة المستمرة أنفع من المجهود "
                  "المتقطع. خد حاجة واحدة بس النهاردة — مش تمارين، حركة "
                  "بسيطة تكرّرها."),
    },
    {
        "id": "akhlaq",
        "title": "أخلاق الناس: {m} دقيقة في التعامل",
        "series": ["ser-field-ناس", "ser-field-صداقة", "ser-field-مقابلة",
                   "ser-field-استماع", "ser-field-حياء", "ser-field-أخ",
                   "ser-field-يتيم", "ser-host", "ser-field-سلامة",
                   "ser-field-حسد", "ser-field-وهم ونفس", "ser-field-نفس"],
        "chapters": ["الناس", "الصداقة", "المقابلة", "الاستماع", "الحياء",
                     "الأخ", "اليتيم", "الضيافة", "السلامة", "الحسد",
                     "الوهم والنفس", "النفس"],
        "open": ("أصعب حاجة في الدنيا مش الشغل — الناس. الجلسة دي عن "
                 "التعامل بإيد مفتوحة ولسان محترم: إمتى تسمع، وإمتى تسكت، "
                 "وإمتى تعتذر، وإزاي تحمي نفسك من وهم جواك."),
        "close": ("خلاصة الجلسة: احترامك للناس بيرجع لك. خد موقف واحد من "
                  "الجلسة دي وصلّحه في تعاملك النهاردة."),
    },
    {
        "id": "dahk",
        "title": "ضحك خفيف: {m} دقيقة تفرّح قلبك",
        "series": ["ser-field-ضحك نظيف", "ser-field-نكشة", "ser-field-ضحك",
                   "ser-field-خفة", "ser-field-ملعب", "ser-field-كرة",
                   "ser-field-سطح", "ser-field-بلكونة", "ser-animal",
                   "ser-plant", "ser-field-ألوان", "ser-field-حروف"],
        "chapters": ["الضحك النظيف", "النكشة", "الضحك", "الخفة", "الملعب",
                     "الكورة", "السطح", "البلكونة", "الرفق بالحيوان",
                     "الزرع", "الألوان", "الحروف"],
        "open": ("الجلسة دي للقلب المكتم: ضحك نضيف بلا إساءة، ونكشة خفيفة "
                 "بلا جرح، وحاجات صغيرة بتفرّح. اسمعها بالهنا."),
        "close": ("خلاصة الجلسة: الضحك اللي بيقرّب الناس هو الضحك النضيف. "
                  "لو ضحكت النهاردة على حاجة من دول، ابعت حاجة تفرّح حد."),
    },
    {
        "id": "khayr",
        "title": "رزق وستر: {m} دقيقة عن المال والأمانة",
        "series": ["ser-money", "ser-field-رزق", "ser-field-تجربة",
                   "ser-field-بناء", "ser-field-تدوير", "ser-field-حريق",
                   "ser-field-متحف", "ser-field-وثائقي", "ser-field-صوت",
                   "ser-field-صدى", "ser-field-شبكة", "ser-field-مغناطيس"],
        "chapters": ["المال", "الرزق", "التجربة", "البناء", "التدوير",
                     "الحريق", "المتحف", "الوثائقي", "الصوت", "الصدى",
                     "الشبكة", "المغناطيس"],
        "open": ("الفلوس مش عيب، والستر نعمة. الجلسة دي مش عن الغنى ولا "
                 "وعود بالثراء — دي عن الأمانة: إزاي تكسب، وإزاي تحافظ، "
                 "وإزاي تفهم حاجة قبل ما تخاف منها."),
        "close": ("خلاصة الجلسة: الرزق بيتبنى على خطوات صغيرة وأمانة. "
                  "مفيش وعد ثراء هنا — في وعد إنك تفهم قرارك الجاي أحسن."),
    },
]


def _spoken_by_shelf() -> dict[str, list[dict]]:
    """المخزون الديني المنطوق مجمّع بالرف (مع استبعاد الكلام المقدّس —
    المحرّك بيرفض يحوّل آية أو نص مقدّس لصوت، وده محترم بالكامل)."""
    from xtrendaw.noor_next.timeline import sacred_text
    out: dict[str, list[dict]] = defaultdict(list)
    for row in _rows():
        if row.get("engine") != "spoken":
            continue
        text = str(row.get("spoken") or "").strip()
        if not text or sacred_text(text):
            continue
        out[str(row.get("series_title") or "")].append(row)
    return out


def build_religious(col: dict, shelves: dict[str, list[dict]],
                    cap_words: int) -> dict | None:
    """حلقة طويلة من المخزون الديني — بلا تكرار جملة، وبخاتمة حقيقية."""
    uniq = Unique()
    parts: list[str] = []
    lead = uniq.add(col["open"])
    parts.append(lead)
    words = len(lead.split())
    used = 0
    for shelf in col["shelves"]:
        items = shelves.get(shelf) or []
        if not items:
            continue
        for row in items:
            if words >= cap_words:
                break
            got = uniq.add(str(row.get("spoken") or ""))
            if not got:
                continue
            parts.append(got)
            words += len(got.split())
            used += 1
    if used < 8:
        return None
    tail = uniq.add(col["close"])
    if tail:
        parts.append(tail)
    text = "\n\n".join(p for p in parts if p.strip())
    text = _regroup(text, int(os.environ.get("NOOR_LONG_LINE_WORDS") or "15"))
    floor = int(os.environ.get("NOOR_LONG_MIN_WORDS") or "700")
    if len(text.split()) < floor:
        print(f"[طول] {col['id']}: {len(text.split())} كلمة — أقل من الأرضية "
              f"({floor})", flush=True)
        return None
    mins = max(1, round(estimate_sec(text) / 60))
    title = str(col["title"]).replace("{m}", str(mins))
    return {
        "id": f"long-{col['id']}",
        "series_id": f"longmix-{col['id']}",
        "series_title": title,
        "episode": 1,
        "episodes_in_series": 1,
        "kind": "long",
        "engine": "life",
        "emotion": "سكينة",
        "hook": title,
        "spoken": text,
        "scene": "calm wide shot no faces",
        "search": [str(col["title"]).split(":")[0], "أذكار", "دعاء", "أحاديث",
                   "ذكر", "راحة نفسية"],
        "benefit": col["close"].strip(),
        "factory": False,
        "ready_for_factory": True,
        "status": "ready",
        "origin": "مصنع الطويل — من المخزون الديني الموثّق",
        "rules": ["من غير وجوه", "من غير نص مقدس متألف",
                  "من غير وعد علاج أو ثراء", "المدة من الكلام مش من صمت"],
    }


def estimate_sec(text: str) -> float:
    """مدة الكلام المتوقّعة — بالمعدل **المقيس** مش بالتخمين.

    ليه ده مهم؟ العنوان بيقول المدة، فلازم يطابق الحقيقة. استخدمنا قبل كده
    ١٤٠ كلمة/دقيقة (تخمين)، وقِسنا الصوت الفعلي على نص حقيقي: ٧٤٩ كلمة
    = ٤٠٠ ثانية ⇒ **1.87 كلمة/ثانية** (≈١١٢ كلمة/دقيقة). يعني العناوين
    القديمة كانت بتقول «٨ دقايق» والحلقة فعلًا ~١٠.٥ — العنوان لازم يقول
    الحقيقة بالظبط، قِسناها واحنا محسوبين عليها.
    """
    return len(text.split()) / 1.87


def _norm(sentence: str) -> str:
    """بصمة الجملة للمقارنة: بلا تشكيل ولا ترقيم ولا إيموجي."""
    import re
    t = str(sentence or "")
    t = re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06ED]", "", t)
    t = re.sub(r"[^\u0621-\u064A\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _sentences(text: str) -> list[str]:
    from xtrendaw.noor_next.timeline import sentences
    return [s.strip() for s in sentences(text) if s and s.strip()]


class Unique:
    """منع تكرار الجمل — **بمستوى الجملة مش الحلقة**.

    ليه؟ حلقات السلسلة الواحدة بتتراكب: حلقة ٢ بتبدأ بجملة حلقة ١ أحيانًا،
    وبتحلقة كاملة بتتشابه. الفحص القديم كان بيقارن «الحلقة كلها» بحاجة
    موجودة ⇒ التكرار الجزئي كان بيعدّي. النتيجة في أول نسخة: «الأرض بتدور،
    فالنور ييجي ويروح» اتكررت مرتين ورا بعض. ده بيحرق وقت المشاهد **وبيبان
    آلي** — وهو بالظبط اللي يوتيوب بيعاقب عليه.
    """

    def __init__(self) -> None:
        self.seen: set[str] = set()

    def add(self, text: str) -> str:
        keep = []
        for s in _sentences(text):
            k = _norm(s)
            if len(k) < 8 or k in self.seen:
                continue
            self.seen.add(k)
            keep.append(s)
        return " ".join(keep)



def _regroup(text: str, target_words: int = 15) -> str:
    """بيجمّع الجمل الصغيرة في جمل أطول طبيعية.

    ليه ده مهم؟ المحرّك بيرندر **لقطة لكل جملة**. النص كان ٣٣٩ جملة ⇒
    ٣٣٩ لقطة ⇒ تحميل ٣٣٩ مقطع من النت + مونتاج ⇒ أكيد يتخطّى مهلة الدورة
    (٤٥ دقيقة) ويفشل. بعد التجميع: ~٨٥ جملة ⇒ رندر واقعي و **مونتاج أهدى**
    (لقطة كل ٨–١٠ ثواني بدل قص كل ٣ ثواني — وده أنسب للطويل أصلًا).
    """
    from xtrendaw.noor_next.timeline import sentences
    out_paras: list[str] = []
    for para in (text or "").split("\n\n"):
        para = para.strip()
        if not para:
            continue
        buf: list[str] = []
        words = 0
        built: list[str] = []
        for sent in sentences(para):
            s_words = len(sent.split())
            if buf and words + s_words > int(target_words * 1.35):
                built.append("، ".join(buf).rstrip("، ") + ".")
                buf, words = [], 0
            clause = sent.rstrip(".").strip()
            # وصل سلس بين الجمل: «و» قبل الفعلية القصيرة (نفس أسلوب الكلام
            # الطبيعي)، وبس فاصلة قبل الاسمية — عشان ما يبقاش كلام متقطّع.
            if buf and not clause.startswith(("و", "ثم", "لكن", "بس", "غير")):
                clause = "و" + clause
            buf.append(clause)
            words += s_words
        if buf:
            built.append("، ".join(buf).rstrip("، ") + ".")
        out_paras.append(" ".join(built))
    return "\n\n".join(out_paras)


def build(col: dict, fam: dict[str, list[dict]], cap_words: int) -> dict | None:
    """بيبني نص الحلقة الطويلة من كلام المكتبة الأصلي (بلا تكرار جملة)."""
    uniq = Unique()
    lead = uniq.add(col["open"])
    words = len(lead.split())
    parts: list[str] = [lead]
    want = [s for s in col["series"] if fam.get(s)]
    if len(want) < 3:
        return None
    used_eps = 0
    for ci, sid in enumerate(want):
        eps = fam[sid]
        if not eps:
            continue
        if words >= cap_words:
            break
        name = col["chapters"][ci] if ci < len(col["chapters"]) else sid
        head = _bridge(col["id"], ci, name)
        chunk: list[str] = [head]
        for ep in eps:
            if words >= cap_words:
                break
            spoken = uniq.add(str(ep.get("spoken") or ""))
            if not spoken:
                continue
            chunk.append(spoken)
            words += len(spoken.split())
            used_eps += 1
            # خلاصة عملية — بس لما تكون جملة حقيقية مش كلمة واحدة
            ben = str(ep.get("benefit") or "").strip()
            if used_eps % 3 == 0 and len(ben.split()) >= 4:
                got = uniq.add(ben)
                if got:
                    chunk.append(got)
                    words += len(got.split())
        if len(chunk) > 1:
            parts.append(" ".join(chunk))
    tail = uniq.add(col["close"])
    if tail:
        parts.append(tail)
    text = "\n\n".join(p for p in parts if p.strip())
    text = _regroup(text, int(os.environ.get("NOOR_LONG_LINE_WORDS") or "15"))
    if len(text.split()) < 700:
        return None
    # العنوان بيقول المدة **الحقيقية** — الرقم يتولّد من النص، مش مكتوب بإيد.
    mins = max(1, round(estimate_sec(text) / 60))
    title = str(col["title"]).replace("{m}", str(mins))
    return {
        "id": f"long-{col['id']}",
        "series_id": f"longmix-{col['id']}",
        "series_title": title,
        "episode": 1,
        "episodes_in_series": 1,
        "kind": "long",
        "engine": "life",
        "emotion": "سكينة",
        "hook": title,
        "spoken": text,
        "scene": "calm wide shot no faces",
        "search": [str(col["title"]).split(":")[0], "نصيحة", "خير", "تدبر",
                   "حياة", "راحة نفسية"],
        "benefit": col["close"].strip(),
        "factory": False,
        "ready_for_factory": True,
        "status": "ready",
        "origin": "مصنع الطويل — مجمّع من مكتبة الأصناف",
        "rules": ["من غير وجوه", "من غير نص مقدس متألف",
                  "من غير وعد علاج أو ثراء", "المدة من الكلام مش من صمت"],
    }


def main() -> int:
    cap = int(os.environ.get("NOOR_LONG_TARGET_WORDS") or "1500")
    fam = _by_series()
    shelves = _spoken_by_shelf()
    have = {r.get("id") for r in _rows()}
    made = []
    for col in list(COLLECTIONS) + list(COLLECTIONS_B):
        row = build(col, fam, cap)
        if not row:
            print(f"[طول] ⚠️ مجموعة {col['id']} ناقصة سلاسل — اتخطّت")
            continue
        if row["id"] in have:
            print(f"[طول] ↺ {col['id']} موجود بالفعل — مش هنكرّره")
            made.append(row)
            continue
        made.append(row)
    # الكتاب التاني: حلقات من المخزون الديني (وقود مستمر للكيو)
    for col in RELIGIOUS:
        row = build_religious(col, shelves, cap)
        if not row:
            print(f"[طول] ⚠️ مجموعة {col['id']} ناقصة نصوص — اتخطّت")
            continue
        if row["id"] in have:
            print(f"[طول] ↺ {col['id']} موجود بالفعل — مش هنكرّره")
            made.append(row)
            continue
        made.append(row)
    if not made:
        print("[طول] مفيش حاجة اتعملت")
        return 1
    print(f"=== {len(made)} حلقة طويلة ===")
    for row in made:
        w = len(row["spoken"].split())
        sec = estimate_sec(row["spoken"])
        print(f"  {row['id']:14} {w:5} كلمة ≈ {sec / 60:4.1f} دقيقة | "
              f"{row['series_title'][:38]}")
    if os.environ.get("NOOR_LONG_WRITE") != "1":
        print("\n(تجربة — مش كتبنا. اكتب NOOR_LONG_WRITE=1 للنشر في المكتبة)")
        return 0
    new = [r for r in made if r["id"] not in have]
    if not new:
        print("مفيش جديد يتكتب")
        return 0
    with LIB.open("a", encoding="utf-8") as fh:
        for row in new:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\n✅ اتضافوا {len(new)} حلقة طويلة للمكتبة ({LIB.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
