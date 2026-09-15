// Viral Engine & Reverse Engineering System
// Designed to emulate the world's most viral YouTube formulas (MrBeast, Kurzgesagt, Zach King, etc.)

export const VIRAL_CATEGORIES = [
  { id: 'all', nameAr: 'كل الفئات العالمية', nameEn: 'All Viral Categories' },
  { id: 'challenges', nameAr: 'تحديات كبرى وجوائز (MrBeast)', nameEn: 'High Stakes Challenges' },
  { id: 'science', nameAr: 'غرائب الكون والعلوم (Kurzgesagt)', nameEn: 'Cosmic & Science Mysteries' },
  { id: 'magic', nameAr: 'خدع بصرية وإبهار صامت (Visual Magic)', nameEn: 'Visual Illusions & Magic' },
  { id: 'experiments', nameAr: 'تجارب وحرف خارقة (Extreme Experiments)', nameEn: 'Extreme Experiments' },
  { id: 'shorts', nameAr: 'شورتس فيروسية خاطفة (Viral Shorts)', nameEn: 'Hypnotic Shorts' },
  { id: 'curiosity', nameAr: 'ألغاز وقصص سينمائية (Docu-Mysteries)', nameEn: 'Cinematic Documentaries' }
];

export const TOP_GLOBAL_TRENDS = [
  {
    id: 'trend-01',
    title: 'عشت 7 أيام في غرفة بيضاء بالكامل بدون أي صوت أو بشر!',
    titleEn: 'I Survived 7 Days in a Completely White Silent Room!',
    channelTitle: 'Cosmic Explorer',
    channelAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&auto=format&fit=crop&q=80',
    views: 48920000,
    likes: 3120000,
    comments: 184000,
    publishedDaysAgo: 5,
    category: 'challenges',
    thumbnail: 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop&q=80',
    velocity: '9.7M مشاهدة / يوم',
    viralScore: 98,
    hookBreakdown: 'في الثانية 0، يغلق الباب الحديدي الضخم بصوت مرعب ويسأل المضيف: هل يصمد العقل البشري أمام الصمت التام؟',
    tags: ['تحديات', 'mrbeast', 'عزلة', 'تجارب حقيقية', 'white room', 'psychology experiment', 'survival', '7 days challenge', 'viral'],
    retentionSecret: 'إيقاع سريع جداً، ساعة عد تنازلي على الشاشة تظهر تدهور الإدراك البصري كل 12 ساعة.'
  },
  {
    id: 'trend-02',
    title: 'ماذا لو ابتلع ثقب أسود حجمه حبة رمل كوكب الأرض؟',
    titleEn: 'What If a Sand-Sized Black Hole Collided with Earth?',
    channelTitle: 'Cosmic Minds',
    channelAvatar: 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=120&auto=format&fit=crop&q=80',
    views: 32450000,
    likes: 2450000,
    comments: 92000,
    publishedDaysAgo: 12,
    category: 'science',
    thumbnail: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80',
    velocity: '2.7M مشاهدة / يوم',
    viralScore: 95,
    hookBreakdown: 'عرض حبة رمل تسقط في كوب ماء، وفجأة انفجار كوني يسحب الغلاف الجوي خلال 4 ثواني!',
    tags: ['ثقب اسود', 'black hole', 'فضاء', 'فيزياء', 'kurzgesagt', 'ماذا لو', 'space animation', 'earth destruction', 'science'],
    retentionSecret: 'رسوم متحركة مذهلة وربط الخطر الكوني بحياة المشاهد اليومية بدقة.'
  },
  {
    id: 'trend-03',
    title: 'بنيت أغلى بيت تحت الأرض ضد الكوارث في 100 ساعة!',
    titleEn: 'I Built a $1,000,000 Underground Bumper in 100 Hours!',
    channelTitle: 'Extreme Builders',
    channelAvatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80',
    views: 61800000,
    likes: 4100000,
    comments: 215000,
    publishedDaysAgo: 9,
    category: 'challenges',
    thumbnail: 'https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=600&auto=format&fit=crop&q=80',
    velocity: '6.8M مشاهدة / يوم',
    viralScore: 99,
    hookBreakdown: 'مشهد جرافة عملاقة تسقط صخرة خرسانية على السقف لاختبار مقاومة الملجأ في أول ثانيتين.',
    tags: ['ملجأ سري', 'bunker', 'بناء سريع', 'underground house', 'survival bunker', 'تحدي 100 ساعة', 'extreme build'],
    retentionSecret: 'كل 30 ثانية يتم الكشف عن غرفة سرية جديدة وميزة دفاعية غير متوقعة.'
  },
  {
    id: 'trend-04',
    title: 'الخدعة التي حيرت 100 مليون شخص في العالم (بدون كلام)',
    titleEn: 'The Optical Illusion That Fooled 100,000,000 People',
    channelTitle: 'Visual Mind Magic',
    channelAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80',
    views: 89400000,
    likes: 7200000,
    comments: 310000,
    publishedDaysAgo: 14,
    category: 'magic',
    thumbnail: 'https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?w=600&auto=format&fit=crop&q=80',
    velocity: '6.3M مشاهدة / يوم',
    viralScore: 97,
    hookBreakdown: 'الكرة تتدحرج إلى أعلى الدرج متجاوزة الجاذبية في الثانية الأولى بدون أي صوت.',
    tags: ['خدع بصرية', 'zach king', 'optical illusion', 'satisfying', 'impossible', 'magic trick', 'mind blown'],
    retentionSecret: 'عدم وجود كلام يجعل الفيديو عابراً للقارات بدون حاجة لأي ترجمة.'
  },
  {
    id: 'trend-05',
    title: 'وضعنا 10,000 لتر كوكاكولا في بركان مينتوس عملاق!',
    titleEn: 'Dropping 10,000 Liters of Cola into Giant Mentos Volcano',
    channelTitle: 'Science Boom',
    channelAvatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80',
    views: 74200000,
    likes: 5400000,
    comments: 178000,
    publishedDaysAgo: 7,
    category: 'experiments',
    thumbnail: 'https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=600&auto=format&fit=crop&q=80',
    velocity: '10.6M مشاهدة / يوم',
    viralScore: 100,
    hookBreakdown: 'ارتفاع نافورة رغوة عملاقة لارتفاع 50 متراً في السماء مع صوت صرير الانفجار الفوري.',
    tags: ['mentos', 'coca cola', 'extreme experiment', 'تجارب علمية', 'انفجار بركاني', 'giant reaction', 'satisfying explosion'],
    retentionSecret: 'التصوير فائق البطء (Slow Motion) بجودة 4K بملايين الإطارات في الثانية.'
  },
  {
    id: 'trend-06',
    title: 'أسرع طريقة للهروب من أخطر فخاخ العالم في 30 ثانية',
    titleEn: 'Fastest Way to Escape the World\'s Most Dangerous Traps',
    channelTitle: 'Cosmic Survival',
    channelAvatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&auto=format&fit=crop&q=80',
    views: 41200000,
    likes: 3800000,
    comments: 89000,
    publishedDaysAgo: 3,
    category: 'shorts',
    thumbnail: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80',
    velocity: '13.7M مشاهدة / يوم',
    viralScore: 99,
    hookBreakdown: 'الرمال المتحركة تبتلع شخصاً حتى رقبته، وشرح حيلة إنقاذ بالجسد في أول ثانية.',
    tags: ['shorts', 'survival tips', 'حيل نجاة', 'رمال متحركة', 'escape tricks', 'life hacks', 'quick survival'],
    retentionSecret: 'حلقة فيديو متصلة بلا نهاية (Infinite Loop) تجعل المشاهد يعيد الفيديو مرتين تلقائياً.'
  }
];

// Generate an ultra-viral production package based on any topic or existing viral video
export function generateViralBlueprint(topicOrVideo, category = 'challenges') {
  const baseTopic = typeof topicOrVideo === 'string' ? topicOrVideo : (topicOrVideo.title || 'أقوى تحدي في العالم');

  const titles = [
    {
      titleAr: `تحديت 100 شخص للبقاء في ${baseTopic} والرابح يأخذ كل شيء!`,
      titleEn: `I Trapped 100 People in ${baseTopic} - Winner Takes Everything!`,
      predictedCtr: '17.8%',
      style: 'MrBeast Extreme Stakes (أقصى إثارة وتحدي مالي)'
    },
    {
      titleAr: `ماذا يحدث حقاً إذا دخلت ${baseTopic} لأول مرة في التاريخ؟`,
      titleEn: `What ACTUALLY Happens If You Enter ${baseTopic}?`,
      predictedCtr: '16.4%',
      style: 'Cosmic Curiosity & Revelation (الفضول المعرفي الكوني)'
    },
    {
      titleAr: `قضيت 24 ساعة داخل ${baseTopic} المستحيل.. (نهاية غير متوقعة)`,
      titleEn: `I Spent 24 Hours Inside the Impossible ${baseTopic}..`,
      predictedCtr: '15.9%',
      style: 'Personal High Stakes Adventure (المغامرة والغموض)'
    },
    {
      titleAr: `السر المحرم وراء ${baseTopic} الذي يخفيه الجميع عنك!`,
      titleEn: `The Dark Secret of ${baseTopic} Nobody Is Telling You`,
      predictedCtr: '14.8%',
      style: 'Curiosity Cliffhanger (كشف الأسرار العالمية)'
    },
    {
      titleAr: `جربت ${baseTopic} لمدة 30 يوماً.. والنتيجة صدمت الأطباء والعلماء!`,
      titleEn: `I Tried ${baseTopic} for 30 Days.. The Result Shocked Scientists!`,
      predictedCtr: '15.2%',
      style: 'Transformation & Science (التحول والنتائج الصادمة)'
    }
  ];

  const storyboard = [
    {
      timestamp: '0:00 - 0:03',
      stage: 'الخطاف البصري الصاعق (The 3-Second Hook)',
      visual: 'لقطة مقربة درامية سريعة، الكاميرا تتحرك بسرعة نحو الهدف، تأثير صوتي عنيف (Whoosh + Boom). لا وجود لأي مقدمة أو ترحيب!',
      speechAr: `في هذه اللحظة، نحن على وشك تجربة ${baseTopic}، وإذا فشلنا في الـ 60 ثانية القادمة، ستنهار الخطة بالكامل!`,
      speechEn: `Right now, we are attempting ${baseTopic}, and if this fails in the next 60 seconds, everything is lost!`,
      retentionGoal: 'منع المشاهد من التمرير أو المغادرة (رفع نسبة الاحتفاظ فوق 90%).'
    },
    {
      timestamp: '0:04 - 0:18',
      stage: 'القواعد والرهان المستحيل (Stakes & Rules)',
      visual: 'ظهور شاشة جرافيك ثلاثية الأبعاد سريعة توضح العقبات الثلاث الكبرى والعداد التنازلي الحقيقي.',
      speechAr: 'القاعدة الأولى واضحة: لا تراجع، والوقت ينفد بسرعة جنونية. شاهد ما الذي سيحدث هنا!',
      speechEn: 'Rule number one: No turning back, and the clock is ticking down right now. Watch closely!',
      retentionGoal: 'بناء الفضول وإعطاء المشاهد سبباً واضحاً لمتابعة الفيديو حتى النهاية.'
    },
    {
      timestamp: '0:19 - 0:50',
      stage: 'الصدمة الأولى والتصعيد (Escalation Beat 1)',
      visual: 'انقطاع مفاجئ أو مفاجأة لم تكن في الحسبان، ردود أفعال حقيقية ومصورة بزوايا سينمائية متعددة.',
      speechAr: 'لم نكن نتوقع حدوث هذا إطلاقاً! انظروا إلى هذه القراءة غير الطبيعية!',
      speechEn: 'We did not plan for this at all! Look at these numbers right now!',
      retentionGoal: 'كسر الروتين وإشعال الأدرينالين لمنع الانخفاض الكلاسيكي للدقيقة الأولى.'
    },
    {
      timestamp: '0:51 - 1:45',
      stage: 'المفاجأة الكبرى والتحول المزدوج (The Mid-Video Twist)',
      visual: 'دخول عنصر جديد كلياً في اللعبة يقلب الموازين ويغير مسار التجربة بالكامل.',
      speechAr: 'إذا كنتم تظنون أن هذا صعب، فالجزء القادم سيبدو مستحيلاً علمياً!',
      speechEn: 'If you thought that was intense, what happens next was considered mathematically impossible!',
      retentionGoal: 'إعادة شحن انتباه المشاهد للوصول إلى ذروة الفيديو.'
    },
    {
      timestamp: '1:46 - النهاية',
      stage: 'الذروة والمكافأة الخارقة (The Climax & Zero-Drop Payoff)',
      visual: 'النتيجة النهائية الصادمة تظهر في آخر 5 ثوانٍ، تليها دعوة ذكية للاشتراك ترتبط بالفيديو القادم مباشرة.',
      speechAr: 'لقد حدثت المعجزة! إذا أردتم رؤية التحدي القادم الأكبر، اضغطوا اشتراك الآن قبل انطلاق المغامرة!',
      speechEn: 'We actually did it! If you want to witness the next impossible challenge, hit subscribe now!',
      retentionGoal: 'تحويل المشاهد المنبهر إلى مشترك دائم بضغطة زر واحدة.'
    }
  ];

  const thumbnailConcepts = [
    {
      conceptNumber: 1,
      title: 'مفهوم الصدمة والتباين الشديد (MrBeast Style)',
      layout: 'وجه مقرب في الجانب الأيمن بتعبير ذهول واقعي وعيون متسعة، وفي الجانب الأيسر مشهد ضخم لـ ' + baseTopic + ' مع إضاءة نيون قوية ومتباينة (أحمر وأزرق).',
      textOnThumb: 'مستحيل؟! / IMPOSSIBLE?!',
      whyItWorks: 'التباين البصري يجذب العين في أجزاء من الثانية وسط بحر الفيديوهات المقترحة.'
    },
    {
      conceptNumber: 2,
      title: 'مفهوم الغموض والكون الساحر (Kurzgesagt Style)',
      layout: 'رسم سينمائي أو لقطة ثلاثية الأبعاد لكوكب أو غرفة غامضة يتصاعد منها شعاع ضوئي عملاق، مع سهم أصفر دقيق يشير إلى تفصيلة غير متوقعة.',
      textOnThumb: 'الحقيقة الصادمة / THE TRUTH',
      whyItWorks: 'إثارة الفضول المعرفي الذي لا يستطيع المشاهد مقاومته.'
    },
    {
      conceptNumber: 3,
      title: 'مفهوم قبل وبعد والمقارنة الفورية (Before vs After)',
      layout: 'شاشة مقسومة نصفين بخط ضوئي عمودي حاد: النصف الأول عادي وبسيط، والنصف الثاني متحول ومبهر بشكل لا يصدق.',
      textOnThumb: '1$ مقابل 1,000,000$',
      whyItWorks: 'المقارنات التباينية من أكثر صيغ الصور المصغرة تحقيقاً لمعدلات النقر العالية تاريخياً.'
    }
  ];

  const multiLanguagePack = {
    arabic: {
      title: `أقوى تجربة لـ ${baseTopic} في العالم - النتيجة لا تصدق!`,
      description: `شاهد كيف خضنا أشرس تجربة مع ${baseTopic}. لا تنس الاشتراك وتفعيل الجرس ليصلك كل جديد كوني!`
    },
    english: {
      title: `Surviving the World's Most Extreme ${baseTopic} Challenge!`,
      description: `We attempted what everyone called impossible with ${baseTopic}. Subscribe for more extreme experiments worldwide!`
    },
    spanish: {
      title: `¡Sobreviví al reto más extremo de ${baseTopic} en el mundo!`,
      description: `Hicimos lo que todos creían imposible. ¡Suscríbete para los mejores desafíos globales!`
    },
    hindi: {
      title: `दुनिया की सबसे ख़तरनाक ${baseTopic} चुनौती! (चौंकाने वाला परिणाम)`,
      description: `देखें कि क्या हुआ जब हमने दुनिया का सबसे बड़ा प्रयोग किया। अभी सब्सक्राइब करें!`
    },
    portuguese: {
      title: `Sobrevivi ao desafio mais insano de ${baseTopic}!`,
      description: `Tentamos o impossível e o resultado vai te chocar. Inscreva-se no canal agora!`
    },
    french: {
      title: `J'ai survécu au défi le plus extrême de ${baseTopic} au monde!`,
      description: `Nous avons fait l'impossible. Abonnez-vous pour les plus grandes aventures du monde!`
    },
    japanese: {
      title: `世界で最も危険な ${baseTopic} に挑んだ結果…衝撃の結末！`,
      description: `誰もが不可能だと言った挑戦の全貌を公開。チャンネル登録をお願いします！`
    },
    german: {
      title: `Ich habe das extremste ${baseTopic} Experiment der Welt überlebt!`,
      description: `Was als Experiment begann, schockierte alle. Jetzt abonnieren für mehr weltweite Abenteuer!`
    }
  };

  const tags = [
    baseTopic,
    'تحديات',
    'mrbeast',
    'تجارب عالمية',
    'غرائب',
    'viral',
    'world record',
    'survival challenge',
    'science experiment',
    'shorts',
    'impossible challenge',
    'trending now',
    'extreme build',
    'mind blown',
    'satisfying',
    'top 10',
    'documentary',
    'kurzgesagt',
    'universe mystery',
    'arabic youtube',
    'global reach',
    'highest views'
  ];

  const hashtags = [
    '#Viral',
    '#MrBeast',
    '#Challenge',
    '#Trending',
    '#Shorts',
    '#YouTube',
    '#Cosmic',
    '#WorldRecord'
  ];

  return {
    topic: baseTopic,
    category,
    titles,
    storyboard,
    thumbnailConcepts,
    multiLanguagePack,
    tags,
    tagsString: tags.join(', '),
    hashtags,
    hashtagsString: hashtags.join(' '),
    estimatedViralScore: 96,
    recommendedDuration: '8:45 دقيقة (أفضل مدة لتحقيق أقصى ربح واحتفاظ)'
  };
}

// The Infinite Million-Ideas Matrix Generator
export const IDEA_COMPONENTS = {
  subjects: [
    { ar: '100 شخص من 100 دولة مختلفة', en: '100 People from 100 Different Countries' },
    { ar: '50 طفلاً ضد 50 بالغاً', en: '50 Kids vs 50 Adults' },
    { ar: 'أقوى حارس أمن ضد أذكى لص في العالم', en: 'World\'s Best Security Guard vs Master Thief' },
    { ar: 'بنيت أغلى ملجأ تحت الأرض بـ 1,000,000$', en: 'I Built a $1,000,000 Underground Bunker' },
    { ar: 'عشت 100 ساعة في أبرد غرفة في العالم (-50°C)', en: 'I Survived 100 Hours in -50°C Coldest Room' },
    { ar: 'ماذا لو اصطدم كويكب من الألماس الخالص بالأرض؟', en: 'What If a Pure Diamond Asteroid Hit Earth?' },
    { ar: 'وضعت 50,000 لتر نيتروجين سائل في مسبح عملاق!', en: 'Dropping 50,000L Liquid Nitrogen in Giant Pool' },
    { ar: 'تحديت أبطال العالم للهروب من أصعب لغز في 60 ثانية', en: 'World Champions Escape the Hardest Maze' },
    { ar: 'اشتريت أغرب 10 أشياء محظورة على الإنترنت المظلم', en: 'I Bought 10 Most Bizarre Banned Mystery Boxes' },
    { ar: 'آخر شخص يرفع يده عن جبل النقود يربح 250,000$', en: 'Last to Take Hand Off Cash Wins $250,000' },
    { ar: 'حبست نفسي في سجن أمني خارق وحاولت الهروب!', en: 'I Escaped the World\'s Most Secure Maximum Prison' },
    { ar: 'ماذا لو توقف الزمن لمدة 10 ثوانٍ لجميع البشر؟', en: 'What If Time Actually Stopped for 10 Seconds?' },
    { ar: 'صنعت أقوى سيف ليزر حقيقي يقطع الحديد كالمعجون!', en: 'I Built a Real 4000°C Plasma Lightsaber' },
    { ar: 'أغرب 7 خدع سحرية بصرية بدون أي كلمة واحدة', en: '7 Impossible Visual Magic Illusions (No Words)' },
    { ar: 'تحدي بقاء 7 أيام على جزيرة مهجورة بدون أي طعام!', en: '7 Days Stranded on a Deserted Island with Nothing' }
  ],
  twists: [
    { ar: 'والرابح يأخذ كل شيء نقداً!', en: 'Winner Takes Everything in Cash!' },
    { ar: 'والنتيجة صدمت أكبر علماء الفيزياء!', en: 'And the Result Shocked Physicists!' },
    { ar: 'النهاية غير متوقعة كلياً (لحظات تحبس الأنفاس)', en: 'The Ending Nobody Saw Coming!' },
    { ar: 'بدون أي كلمة واحدة تفهمها كل شعوب الأرض!', en: '100% Visual Magic Any Human Understands' },
    { ar: 'قبل أن ينفجر المؤقت التنازلي في آخر ثانية!', en: 'Before the Real Countdown Clock Hits Zero!' },
    { ar: 'مع عقبات مستحيلة تتغير كل 10 دقائق!', en: 'With Impossible Rule Changes Every 10 Minutes' }
  ],
  niches: ['challenges', 'science', 'magic', 'experiments', 'shorts', 'curiosity']
};

export function generateInfiniteViralIdeas(count = 12, niche = 'all') {
  const ideas = [];
  const subjects = IDEA_COMPONENTS.subjects;
  const twists = IDEA_COMPONENTS.twists;

  for (let i = 0; i < count; i++) {
    const sub = subjects[Math.floor(Math.random() * subjects.length)];
    const twist = twists[Math.floor(Math.random() * twists.length)];
    const chosenNiche = niche !== 'all' ? niche : IDEA_COMPONENTS.niches[Math.floor(Math.random() * IDEA_COMPONENTS.niches.length)];
    const viralScore = Math.floor(94 + Math.random() * 6); // 94-99%
    const estViews = `${(Math.random() * 40 + 15).toFixed(1)}M`;

    ideas.push({
      id: `infinite-${Date.now()}-${i}-${Math.random().toString(36).substr(2, 5)}`,
      titleAr: `${sub.ar}.. ${twist.ar}`,
      titleEn: `${sub.en}.. ${twist.en}`,
      niche: chosenNiche,
      viralScore,
      predictedViews: estViews,
      predictedCtr: `${(14.5 + Math.random() * 4).toFixed(1)}%`,
      hook3s: `في أول ثانية، الكاميرا تكشف اللحظة الأخطر مع مؤقت تنازلي باللون الأحمر الصارخ وصوت صفارة إنذار توقف الأنفاس!`,
      tags: [sub.ar.split(' ')[0], 'mrbeast', 'تحديات', 'viral', 'impossible', 'explore', '2026'],
      thumbnailConcept: `وجه مصدوم بتعبير ذهول واقعي، إضاءة نيون قوية، والنص: مستحيل؟! / IMPOSSIBLE?!`
    });
  }

  return ideas;
}
export function extractViralTags(keyword = '') {
  const clean = keyword.trim().toLowerCase();
  const defaultTags = [
    keyword,
    'تحدي',
    'viral',
    'mrbeast',
    'shorts',
    'ترند',
    'يوتيوب',
    'أسرار',
    'world record',
    'high retention',
    'top trending',
    'experiment',
    'satisfying',
    'amazing facts',
    'science',
    'fun',
    'entertainment',
    'explore',
    'global',
    '2026'
  ];

  const specificTags = [
    `${keyword} تحدي`,
    `كيف تصنع ${keyword}`,
    `أسرار ${keyword}`,
    `${keyword} viral video`,
    `${keyword} compilation`,
    `best of ${keyword}`,
    `surviving ${keyword}`,
    `${keyword} explained`,
    `what happens if ${keyword}`,
    `extreme ${keyword}`
  ];

  const allTags = Array.from(new Set([...specificTags, ...defaultTags])).slice(0, 30);
  const hashtags = [
    `#${clean.replace(/\s+/g, '')}`,
    '#Shorts',
    '#Viral',
    '#Trending',
    '#Explore',
    '#YouTube',
    '#MrBeast',
    '#Challenge',
    '#Experiment',
    '#WorldRecord'
  ];

  return {
    tags: allTags,
    tagsString: allTags.join(', '),
    hashtags,
    hashtagsString: hashtags.join(' '),
    seoScore: 94,
    recommendations: [
      'ضع أول 3 وسوم (#) في السطر الأول من الوصف للظهور أعلى العنوان في يوتيوب.',
      'اجعل الكلمة المفتاحية الرئيسية في أول 50 حرف من العنوان والسطر الأول من الوصف.',
      'انسخ الوسوم المدمجة بالكامل وضعها في خانة Tags داخل استوديو يوتيوب.'
    ]
  };
}
