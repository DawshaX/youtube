"""١٠٠ صنف خير — شكل مختلف لكل فيديو، من غير ما نكسر جدول الـ١٢.

الجدول ينشر ١٥ في اليوم. المكتبة دي تمشي في خانة الروح،
وكل فيديو — حتى الآية — ياخد تركيبة شكل لا تتكرر مع اللي قبله:
مكان النص، الإطار، الدرجة، حجم الكلمة، والشخصية.
النصوص هنا تأليف المصنع. مفيش آية ولا حديث متألف.
"""
from __future__ import annotations

# (معرّف، اسم، هوك، سطر، مشهد حر بلا وجوه)
_RAW = [
    ("nafs", "نفس", "قبل ما ترد… خد نفس", "نفس واحد بطيء يغيّر الجملة اللي بعدها.", "slow breath morning window light"),
    ("ma", "ماء", "اشرب، وافتكر", "كوب ماء نعمة صغيرة تستاهل وقفة.", "clear water glass light"),
    ("mashy", "مشي", "امشِ بهدوء", "عشر دقايق مشي أهدى من ساعة قلق.", "empty park path morning"),
    ("basma", "ابتسامة", "ابتسم بلا سبب", "ابتسامة من غير طلب بتفتح باب.", "sunlight through leaves soft"),
    ("shukr", "شكر", "قل شكرًا اليوم", "كلمة شكر لشخص واحد تكفي.", "morning table soft light"),
    ("samt", "صمت", "اصمت دقيقة", "الصمت قبل الحكم رحمة.", "quiet room window dawn"),
    ("i3tithar", "اعتذار", "لو غلطت، اعتذر", "جملة اعتذار أقصر من خصام طويل.", "two empty chairs window"),
    ("wa3d", "وعد", "لا تعد فوق طاقتك", "الوعد الصغير الصادق خير من الكبير.", "handshake no faces close"),
    ("jar", "جار", "اسأل على جارك", "كلمة على الباب خير من غياب طويل.", "apartment door morning light"),
    ("umm", "أم", "كلّم أمك", "اتصال قصير يهون يومها.", "phone on wooden table"),
    ("ab", "أب", "اسمع أباك", "الإنصات له هدية أكبر من الرد.", "old chair window light"),
    ("sadeeq", "صديق", "ابعث جملة طيبة", "صديق بعيد يكفيه سطر.", "letter and envelope light"),
    ("kabeer", "كبير", "ساعد كبيرًا", "خطوة تساعده أغلى من نصيحة.", "walking cane path no face"),
    ("tifl", "لعب", "العب خمس دقايق", "اللعب الهادئ يبني أمانًا.", "soft toys sunlight"),
    ("dayf", "ضيف", "رحّب قبل الأكل", "الترحيب أول الضيافة.", "tea cups table steam"),
    ("ta3am", "لقمة", "لا ترمِ لقمة", "اللقمة نعمة، حتى الصغيرة.", "bread on cloth light"),
    ("nazafa", "ترتيب", "رتّب ركنًا", "ركن مرتب يريح العين والقلب.", "tidy shelf morning"),
    ("ta3allum", "تعلّم", "كلمة جديدة", "كلمة واحدة في اليوم طريق.", "open notebook pen"),
    ("sabr", "دور", "استنى دورك", "الانتظار بهدوء قوة هادية.", "empty queue morning hall"),
    ("sidq", "صدق", "قل الحقيقة بلطف", "الصدق اللطيف لا يجرح ليغلب.", "soft lamp desk"),
    ("amana", "أمانة", "ردّ ما ليس لك", "الأمانة راحة، والمماطلة ثقل.", "keys on table light"),
    ("adl", "عدل", "لا تظلم في مزحة", "المزحة التي تؤذي ليست خفة.", "empty cafe table morning"),
    ("karam", "كرم", "أعطِ مما تحب", "العطاء الصغير من القلب يكفي.", "fruit bowl shared light"),
    ("tawado3", "تواضع", "لا ترفع صوتك لتغلب", "الصوت الهادي يُفهم أكثر.", "quiet courtyard arches"),
    ("hilm", "حلم", "أخّر الرد", "عشر ثوانٍ قبل الغضب تنقذ جملة.", "hourglass soft light"),
    ("afw", "عفو", "سامح مرة", "العفو يرفع عنك قبل أن يرفع عن غيرك.", "open window breeze curtain"),
    ("lutf", "لطف", "اختر الألطف", "بين كلمتين، خذ الألطف.", "flower on table light"),
    ("insat", "إنصات", "اسمع للنهاية", "لا تقطع المتحدث. الإنصات هدية.", "two cups facing"),
    ("salam", "سلام", "سلّم أولاً", "السلام يبدأ بك، لا بالآخر.", "sunny alley empty"),
    ("sirr", "سر", "احفظ السر", "السر أمانة حتى لو كان صغيرًا.", "closed book ribbon"),
    ("waqt", "موعد", "لا تتأخر", "احترام الوقت احترام للناس.", "simple clock wall light"),
    ("amal", "إتمام", "أتمم ما بدأته", "النهاية الهادية أشرف من بداية لامعة.", "half finished sketch"),
    ("raha", "راحة", "ارتاح بلا ذنب", "الراحة حق، ليست كسلاً إذا صدقت.", "hammock shade garden"),
    ("fajr", "فجر", "اصحُ بهدوء", "أول النهار للهدوء قبل الضجيج.", "sunrise empty street"),
    ("layl", "ليل", "نم وقلبك خفيف", "لا تحمل الخصام إلى الوسادة.", "night lamp low"),
    ("matar", "مطر", "افرح بالمطر", "المطر رزق قبل أن يكون إزعاجًا.", "rain on leaves close"),
    ("shajar", "شجر", "اسقِ نبتة", "سقية واحدة خير صغير ظاهر.", "watering small plant"),
    ("tayr", "سماء", "انظر للسماء", "دقيقة سماء توسّع الهم.", "birds sky gold no close faces"),
    ("bahr", "بحر", "تذكّر وسع البحر", "أنت صغير أمام البحر، وهذا يريح.", "calm sea horizon"),
    ("nahr", "نهر", "استمر كالنهر", "الماء الجاري لا يقف عند حجر.", "river stones clear"),
    ("jabal", "جبل", "اثبت", "الثبات أجمل من العجلة.", "mountain mist dawn"),
    ("qamar", "قمر", "في الليل نور", "حتى الليل فيه نور.", "moon over water"),
    ("nojoom", "نجوم", "ارفع رأسك", "الدنيا أوسع من همّ اليوم.", "stars desert night"),
    ("reeh", "ريح", "دع الهم يمر", "الريح تمر. لا تمسكها.", "grass wind field"),
    ("hadiqa", "حديقة", "الجمال القريب", "حديقة صغيرة تكفي للنظر.", "small garden path"),
    ("tareeq", "طريق", "خطوة واحدة", "الطريق يبدأ بخطوة لا بخطة كاملة.", "path through trees"),
    ("bab", "باب", "اطرق بلطف", "الطرق الخفيف أكرم من الدفع.", "wooden door morning"),
    ("noor", "نافذة", "افتح نافذة", "نور الغرفة يغيّر المزاج.", "open window sunlight"),
    ("zill", "ظل", "استظل واشكر", "الظل نعمة في الحر.", "shade tree courtyard"),
    ("bathra", "بذرة", "ابدأ صغيرًا", "الخير بذرة قبل أن يكون شجرة.", "seed in soil hands no face"),
    ("yad", "يد", "مدّ يدك أولاً", "المساعدة قبل الكلام.", "open palm light no face"),
    ("qalb", "قلب", "رتّب قلبك", "دقيقة ترتيب قبل أن ترتب يومك.", "still lake reflection"),
    ("lisan", "لسان", "كلمة قد تداوي", "اختر كلمة تداوي لا كلمة تغلب.", "ink and paper"),
    ("ayn", "نظر", "انظر للخير أولاً", "العين تجد ما تبحث عنه.", "flower macro soft"),
    ("uthun", "أذن", "الإنصات هدية", "أذن صاغية أندر من رأي جاهز.", "quiet bench park"),
    ("khotwa", "مقارنة", "لا تقارن خطوتك", "قارن نفسك بأمسك فقط.", "footprints sand empty"),
    ("ghad", "غد", "الغد يُصنع بهدوء", "عمل صغير اليوم خير من قلق الغد.", "calendar page light"),
    ("ams", "أمس", "اترك أمس", "لا تعش في جملة انتهت.", "sunset empty road"),
    ("alan", "الآن", "هذه اللحظة تكفي", "ابدأ الآن ناقصًا.", "clock and plant"),
    ("hodoo", "هدوء", "القوة ليست صراخًا", "الهدوء يُسمع أكثر.", "library empty aisle"),
    ("dahk", "ضحك", "اضحك بلا سخرية", "الضحك الطيب لا يحتاج ضحية.", "sunlight curtain"),
    ("dam3", "دمع", "الدمع ليس ضعفًا", "اسمح للحزن أن يمر.", "rain window night"),
    ("wahda", "خلوة", "الخلوة ليست عقابًا", "وقت وحدك قد يكون أصفى وقت.", "single chair window"),
    ("suhba", "صحبة", "اختر من يذكّرك بخيلك", "الصحبة اتجاه.", "two cups outdoor table"),
    ("bayt", "بيت", "اجعل بيتك ألطف", "كلمة في البيت تغيّر ليلته.", "warm living room lamp"),
    ("maida", "مائدة", "كل بلا هاتف", "الوجود على المائدة هدية.", "family table empty plates light"),
    ("hatif", "هاتف", "ضع الهاتف", "حين يكلمك أحد، انظر له.", "phone face down wood"),
    ("kitab", "صفحة", "اقرأ صفحة", "صفحة واحدة باب.", "open book window"),
    ("so2al", "سؤال", "اسأل قبل أن تفترض", "السؤال يمنع خصامًا.", "question mark notebook"),
    ("khata", "خطأ", "الخطأ باب", "إذا اعتذرت، الخطأ لا يسجنك.", "erased pencil sketch"),
    ("najah", "نجاح", "لا تتكبر", "النجاح أمانة لا تاج.", "mountain top clouds empty"),
    ("fashal", "درس", "الفشل ليس هويتك", "هو درس، ثم تمشي.", "rain then sun path"),
    ("mareed", "عيادة", "عد بكلمة", "رسالة للمريض تخفف.", "soft blanket light"),
    ("farah", "فرح الغير", "افرح لغيرك", "فرحهم لا ينقصك.", "balloons soft daylight distant"),
    ("hozn", "حزن", "اجلس بلا وعظ", "الحزين يحتاج وجودًا لا خطبة.", "empty bench autumn"),
    ("faqir", "عطاء سر", "أعطِ سرًا", "الصدقة الهادية أكرم.", "hands giving bread no faces"),
    ("ghina", "شكر الغنى", "الغنى شكر", "ليس فخرًا. هو مسؤولية.", "full fruit basket"),
    ("souq", "سوق", "كن صادقًا في البيع", "الكلمة في السعر أمانة.", "market stalls morning empty"),
    ("tareeq3am", "طريق الناس", "لا ترمِ في الطريق", "الطريق مشترك.", "clean sidewalk morning"),
    ("hayawan", "رفق", "ارفق بالحيوان", "الحيوان يفهم اللطف.", "bird on branch distant"),
    ("nabat", "غصن", "لا تكسر عبثًا", "الغصن الحي ليس لعبة.", "green branch close"),
    ("israf", "ماء البيت", "لا تُسرِف في الماء", "أغلق الصنبور. هذا خير.", "tap water drop"),
    ("light", "مصباح", "أطفئ ما لا تحتاج", "النور الزائد إسراف.", "single lamp night"),
    ("sawt", "صوت البيت", "اخفض صوتك", "البيت يهدأ إذا هدأت.", "closed door soft light"),
    ("samt2", "صمت جميل", "الصمت أحيانًا يكفي", "ليس كل فراغ يحتاج كلامًا.", "still pond reeds"),
    ("amal2", "أمل صغير", "الأمل عمل", "جملة أمل بلا خطوة لا تكفي. اعمل صغيرًا.", "seedling pot window"),
    ("khawf", "خوف", "سمِّ خوفك", "الاسم يصيّر الخوف أصغر.", "foggy path morning"),
    ("ghadab", "غضب", "أخّر الغضب", "عشر ثوانٍ تنقذ علاقة.", "tea steam pause"),
    ("hasad", "حسد", "ادعُ لمن حسدته", "الدعاء له يحررك.", "sunrise clouds gold"),
    ("moqarana", "أمسِك", "قارن نفسك بأمسك", "هذا العدل مع ذاتك.", "old photo frame empty"),
    ("kamal", "كمال", "لست مطالبًا بالكمال", "الكامل المزعوم متعِب للناس.", "handmade cup imperfect"),
    ("bidaya", "بداية", "ابدأ ناقصًا", "الكمال يؤجّل الخير.", "first line in notebook"),
    ("nihaya", "خاتمة اليوم", "أنهٍ بجملة شكر", "يومك يستاهل سطرًا قبل النوم.", "night window city far"),
    ("sama", "سماء", "السماء أوسع", "فوقك وسع أكبر من ضيق الغرفة.", "open sky blue"),
    ("khobz", "خبز", "لا تُهِن الخبز", "الخبز نعمة على المائدة.", "bread loaf cloth"),
    ("malh", "قليل", "القليل يصلح", "الملح القليل يطيّب، والكثير يفسد. كذلك الكلام.", "salt bowl wood"),
    ("resala", "رسالة", "اكتب جملة وابعثها", "سطر طيب يصل أبعد من زيارتك اليوم.", "pen and paper morning"),
    ("ibtisam2", "سبب ابتسامة", "كن سبب ابتسامة", "يكفي أن أحدًا يبتسم بسببك.", "sunflower field light"),
    ("tariq", "طريق العودة", "ارجع بلطف", "العودة بهدوء خير من العناد.", "path home dusk"),
    ("hadiya", "هدية صغيرة", "هدية بلا مناسبة", "شيء صغير في غير موعده يُفرح.", "small wrapped gift"),
    ("sama3", "سماع", "اسمعه مرتين", "أحيانًا الجملة الثانية هي المقصودة.", "headphones on desk"),
    ("nizam", "نظام", "رتّب غدك في سطر", "سطر واحد ينظّم الصباح.", "simple list paper"),
    ("shams", "شمس", "اخرج للشمس", "عشر دقايق شمس تغيّر الجسم.", "sunlight courtyard empty"),
    ("thawb", "ستر", "استر على غيرك", "لا تنقل عيبًا رأيته.", "curtain closed soft"),
    ("da3wa", "دعوة طيبة", "ادعُ لغيرك بخير", "دعوة صادقة بلا مقابل.", "sunrise hands no face"),
    ("bayt2", "نظافة القلب", "لا تدخل البيت بخصام", "اتركه عند الباب.", "doorstep plant"),
    ("lagha", "لغو", "اترك اللغو", "ليس كل حديث يستاهل مشاركتك.", "empty cafe corner"),
    ("yusr", "يسر", "يسّر على أحد", "تيسير صغير يُنسى عندك ويُذكر عنده.", "open gate garden"),
]

assert len(_RAW) >= 100, len(_RAW)

GRADES = [
    "drawbox=x=0:y=0:w=iw:h=70:color=black:t=fill,drawbox=x=0:y=ih-70:w=iw:h=70:color=black:t=fill,eq=contrast=1.05",
    "drawbox=x=24:y=24:w=iw-48:h=ih-48:color=0xD4AF37:t=4,eq=saturation=1.1",
    "vignette=PI/5,eq=contrast=1.06:saturation=1.08",
    "eq=saturation=1.25:gamma=1.05,colorbalance=rs=0.07",
    "eq=brightness=-0.05:contrast=1.14:saturation=0.85,vignette=PI/4",
    "drawbox=x=0:y=ih-380:w=iw:h=380:color=black@0.5:t=fill,eq=contrast=1.04",
    "colorbalance=gs=0.09:bs=0.03,eq=saturation=1.18",
    "colorbalance=rs=0.09:gs=0.03,eq=gamma=1.04",
    "eq=brightness=-0.03:saturation=1.02,vignette=PI/5",
    "drawbox=x=40:y=100:w=iw-80:h=6:color=0xE8D5A3:t=fill,drawbox=x=40:y=ih-100:w=iw-80:h=6:color=0xE8D5A3:t=fill",
    "drawbox=x=0:y=0:w=36:h=ih:color=0x1B3A4B:t=fill,eq=saturation=1.05",
    "drawbox=x=0:y=0:w=iw:h=160:color=black@0.45:t=fill,eq=contrast=1.05",
    "colorbalance=bs=0.08,eq=saturation=1.12:contrast=1.04",
    "eq=contrast=1.16:saturation=1.02:gamma=0.98",
    "eq=contrast=0.96:saturation=1.2:gamma=1.08",
]
PLATES = ("bl", "br", "tl", "tr", "none")
YS = (0.30, 0.38, 0.46, 0.56, 0.64)
HOSTS = ("نور", "سَكينة", "أمل", "حَكيم", "راوي", "فارس")


def recipe(i: int) -> dict:
    """تركيبة شكل. كل رقم يطلع إطار ومكان نص مختلفين."""
    return {
        "layout": i % len(GRADES),
        "plate": PLATES[i % len(PLATES)],
        "y": YS[(i // 5) % len(YS)],
        "step": 2 + ((i // 7) % 3),
        "host_i": (i // 11) % len(HOSTS),
        "size": 68 + (i % 5) * 6,
        "grade": GRADES[i % len(GRADES)],
    }


def kinds() -> list[dict]:
    out = []
    for i, (slug, name, hook, line, scene) in enumerate(_RAW):
        rec = recipe(i)
        out.append({
            "id": f"khair-{i:03d}-{slug}",
            "slug": slug,
            "name": name,
            "kind": "spirit",
            "plan_kind": "khair",
            "theme": name,
            "hook": hook,
            "lines": [line],
            "outro": f"لو نفعك «{name}»، طبّقه اليوم بهدوء.",
            "scenes": [scene, "soft natural light no people", "calm aerial no faces"],
            "source": "نور — كلام طيب من المصنع، ليس اقتباسًا",
            "variety": i,
            "recipe": rec,
        })
    return out


def cards() -> list[tuple[str, dict]]:
    return [(k["id"], k) for k in kinds()]


def look_for(item: dict) -> dict:
    """شكل الفيديو من معرّفه، مش من قالب واحد يتكرر."""
    seed = str(item.get("variety") if item.get("variety") is not None else item.get("id") or item.get("hook") or "noor")
    n = sum(ord(c) for c in seed) + len(seed) * 13
    if isinstance(item.get("variety"), int):
        n = int(item["variety"])
    rec = recipe(n)
    host = HOSTS[rec["host_i"]]
    return {
        "id": f"shape-{n % max(1, len(_RAW))}",
        "name": str(item.get("theme") or item.get("name") or f"شكل {n % 100}"),
        "y": rec["y"],
        "grade": rec["grade"],
        "plate": rec["plate"],
        "step": rec["step"],
        "host": host,
        "host_i": rec["host_i"],
        "voice": None,
    }


def signatures() -> list[tuple]:
    out = []
    for i in range(len(_RAW)):
        r = recipe(i)
        out.append((r["layout"], r["plate"], r["y"], r["step"], r["host_i"], r["size"]))
    return out
