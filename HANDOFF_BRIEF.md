# HANDOFF_BRIEF — مصنع «دۅۄشے» (DawshaX/youtube)

> موجز تسليم لأي جلسة جديدة. اقرأ `HANDOFF_PACKAGE/00_READ_ME_FIRST.md` الأول.
> **آخر تحديث: 2026-09-17/18 — جلسة «العين» (اقرأ قسمها الأول).**

## جلسة 2026-09-17/18 — العين + الصوت + الدكتور (اقرأ ده قبل الجدول القديم)

**متدمج على `main` فعلًا (PRs #18–23):**
- **العين** `xtrendaw/eye.py`: تنزيل الفيديو الحقيقي (yt-dlp بـ6 عملاء + كوكيز
  من سر `YOUTUBE_COOKIES_B64`) + تسميات تلقائية بتوقيتات حقيقية (عربي ← إنجليزي)
  + مشاهد/ألوان/حركة + صوت لكل ثانية + وكيل 4 مراحل (DNA ← إصدارنا الأصلي في نفس
  السياق ← ناقد 0-100 ← إعادة كتابة لو <75). المخرجات: `data/eye/<vid>/report.json`
  + frames + `data/eye_topics.json` (طابور المصنع — أولوية أولى بعد طلبات المشاهدين
  في `brain.generate` وفي `listProductionQueue` بـ source=eye).
  **لا بيانات متخيلة**: مفيش تسميات ولا مشاهد = فشل صريح برسالة حل.
  التفعيل: **تاج `eye/<VIDEO_ID>` أو `eye/auto`** (البوت مفيشله workflow_dispatch).
  التشخيص الذاتي: أي فشل بيكتب `data/eye/diagnostics/run.log` وبيتحفظ في الجيت.
- **جهاز عصبي WebSocket**: `server/bus.js` + `src/components/LiveFeed.jsx` —
  كل حدث (طيار/إنتاج/عين/نشر/خطأ) بث لحظي `ws://…/ws` + سجل `data/events.jsonl`
  + `GET /api/events`.
- **إصلاح المخ**: `GROQ_API_KEY` كان مفيش كود بيقراه (المخ كان طافيًا بصمت) →
  fallback لـ `GEMINI_API_KEY` في `eye._llm` + `rstrip("/")` على base (كان 404).

**مش متدفع — كوميت محلي `3df654d` على فرع الجلسة (الجلسة اتقفلت قبل الدفع):**
- `xtrendaw/voice.py`: مكتبة 32 صوت — جدول moods (crazy/warm/calm/mysterious/serious)
  + دوران (ما يتكررش خلال آخر 5 حلقات من `data/production_log.json`) + حتمي حسب
  معرّف الموضوع. موصل: `tts.synthesize_segments(voice=)` ← `produce_episode`
  (بيختار حسب `topic.mood`) ← حقل `voice` في report.json وسجلات الإنتاج (bridge
  و autoPilot).
- `xtrendaw/doctor.py` + `.github/workflows/health-check.yml`: **فحص كل ساعة**
  لكل مفتاح وخدمة (YouTube API / Groq / Gemini / LLM مخصص / OAuth بتجديد
  token حقيقي / Pixabay / Pexels / NASA / Openverse / RESTCOUNTRIES /
  Freesound / GNews / Currents / edge-tts بتوليد صوت حقيقي / ffmpeg / الحزم /
  الأصوات / سلامة البيانات) → `data/health.json` + issue واحدة `[health]`
  بتتحدث دائمًا. أوضاع: `--local --json --md --fail`.
- `xtrendaw/world.py`: **مكتبة العالم** — بيانات حقيقية عن دولة الفيديو
  (restcountries.com؛ سر `RESTCOUNTRIES` اختياري — الخدمة شغالة من غيره).
  العين بتضيف قسم «الفيديو في العالم» في الـ digest (سكان/لغة/عملة/عاصمة)
  لما المنطقة معلومة — و`_radar_meta` بياخدها من الرادار snapshot تلقائيًا
  حتى للتاجات المباشرة. 8 اختبارات.
- **فحص أسماء أسرار المستخدم (2026-09-18)**: كل المفاتيح اللي حطها اسمها
  مظبوط ومتغطي (الكود بيغطي التسميات المختصرة PEXELS/NASA/OPENVERSE).
  `BASE64_API_KEY` مش بيتقرأ — على الأرجح مفتاح موقع ترميز مش الكوكيز؛
  الناقص الوحيد: **`YOUTUBE_COOKIES_B64`** (قيمة = الكوكيز نفسه base64).
- **الـ patch الجاهز**: `PENDING-voice-doctor-world.patch` (في مساحة عمل
  الجلسة أو عند المستخدم) — **بيتطبق على `main` مباشرة** (git am/apply).
  (الـ 0001 كامل من نقطة الفرع — مش مطلوب إلا لو الفرع لسه على 2d05549.)

**أول أوامر الجلسة الجديدة:**
```bash
git fetch origin && git log origin/main --oneline -3
# لو في نفس مساحة العمل (الكوميت المحلي موجود):
git rebase origin/main 3df654d && git push origin HEAD:<branch>   # ثم PR ← merge
# لو مساحة جديدة: اطلب من المستخدم الـ patch 0002 ثم:
git apply PENDING-voice-doctor-world.patch
python3 tests/test_eye.py && python3 tests/test_voice.py && python3 tests/test_doctor.py
node --test tests/publishing.test.js     # كله لازم يكون أخضر
```

**ما يلزم من المستخدم (على الكمبيوتر — لا يغني عنه شيء):**
1. `YOUTUBE_COOKIES_B64` = base64 لملف `cookies.txt` من متصفح **حساب فرعي مخصص
   للمصنع** (مفضل — الحساب الأساسي آمن أفضل). بلاها العين مش هتشوف أي فيديو من
   IP خوادم Actions (مؤكد بتشغيلين حقيقيين: التتنز + التسميات مقفلين).
2. تأكد صلاحية `GROQ_API_KEY` و/أو `GEMINI_API_KEY` (أول تشغيل LLM رجع 404 من
   Groq — غالبًا مفتاح منتهي).
3. **انشر تطبيق Google قبل 2026-09-23** وإلا توكن النشر بيتموت.
4. بعدين: تاج `eye/<VIDEO_ID>` لأي فيديو ترند قوي (أول مرشح: `OP3a2qzW5Yk` —
   39 مليون مشاهدة) → مراجعة التقرير مع المستخدم → أول حلقة.

**اختبارات الجلسة (كلها أوفلاين وأخضر):** عين 11 · صوت 10 · دكتور 8 · عالم 8 · نشر Node 9.

---

## ما هو المشروع

مصنع شورتس عمودي (9:16) عربي بالكامل: نصوص → صوت (edge-tts عربي بتوقيت كلمات حقيقي)
→ لقطات خزنة مولّدة برمجيًا + مشاهد مولّدة → مونتاج بقطع كل 2 ثانية → غلاف من إطار
حقيقي → ترخيص لكل ميديا → بوابة جودة → نشر متوقف لحين موافقة المستخدم على بايلوت.

## القواعد الصارمة (لا تُكسر)

1. **النشر موقوف** — لا نشر عام إطلاقًا قبل أن يعاين المستخدم حلقة بايلوت ويوافق.
2. **لا ميديا بلا ترخيص مسجل** — أي ملف وسائط غير مسجل في `vault/index.json`
   = فشل رندر صريح (`vault.require_license`)، وليس تجاهل.
3. **لا إعادة استخدام للقطة أكثر من مرتين في الحلقة** — `footage.pick_vault_clip(max_uses=2)`.
4. **لا جملة مكررة عبر 10 حلقات متتالية** — `script._sentence_repetition_probe()`.
5. **قياس بنية فقط** لمحتوى الآخرين — لا نسخ عناوين/نصوص/مشاهد.
6. **لا اختراع روابط أو نتائج** — كل ما يُعرض على المستخدم حقيقي وقابل للتدقيق.
7. **هوية واحدة: «دۅۄشے»** — صفر «XTreNDAW»/«CosmicTube» في أي مخرجات
   (النصوص/الأغلفة/الوصف). الأسماء القديمة تبقى فقط في بنى تحتية لا تخرج للجمهور.
8. **`data/production_log.json` لا يُضاف إلى `.gitignore`** — سير العمل يعتمد على
   `git add data/production_log.json`. المُضاف فقط: `content/vids/*-cover.png`.

## حالة المراحل الـ16 (من حزمة التسليم السابقة)

| # | المرحلة | الحالة |
|---|---------|--------|
| 1 | `WordBoundary` في edge-tts + كلمات لكل جملة في `plan.json` | ✅ منفّذ ومختبر |
| 2 | سطر واحد = توليفة واحدة (بلا تقسيم/فواصل صناعية) | ✅ منفّذ |
| 3 | قائمة الأصوات العربية على Actions | ✅ workflow يكتب `ar_voices.txt` artifact |
| 4 | ربط `footage.py` + `assets/footage/` (فيديو متحرك لا صور) | ✅ + 5 مقاطع جديدة |
| 5 | قطع كل 2 ثانية | ✅ `XT_SCENE_CUT=2.0` + `target_cut=2.0` |
| 6 | كاريوكي `{\k}` في `.ass` من توقيت الخدمة | ✅ `captions.build_ass` |
| 7 | `vault/index.json` + حارس ترخيص + مولد اعتمادات | ✅ `xtrendaw/vault.py` |
| 8 | رادار + محلل → `patterns.json` | ✅ الكود كامل (`radar.py` + `analyzer.py` + سير `radar-scan.yml`) — يشتغل فور وجود `YOUTUBE_API_KEY` |
| 9 | قتل `facts_ar` + 509 موضوعًا من كتالوج «دۅۄشے» | ✅ منفّذ |
| 10 | محرك أصوات متعدد (راوي + تفاعل) | ⏳ غير منفّذ |
| 11 | بوابة جودة + فحص رفع خاص على يوتيوب | ✅ جزئيًا (`gate.py` — فحص الرفع الخاص يحتاج توكن صالح) |
| 12 | غلاف من أفضل إطار فعلي (صفر `challenge_room.jpg`) | ✅ `brand.compose_cover` |
| 13 | توحيد البراند «دۅۄشے» | ✅ |
| 14 | إصلاحات المستودع (`pruneProductionLog` + README + .gitignore) | ✅ + 9 اختبارات |
| 15 | حلقة تغذية `data/analytics.json` (24/72 ساعة) | ⏳ غير منفّذ |
| 16 | بايلوت واحد → موافقة → نشر | ⏸ الحلقة اتعملت بالأدلة — في انتظار موافقة المستخدم |

## دليل حقيقي من GitHub Actions (مش محاكاة)

التشغيل `#35161163632` على `main` التزم الأدلة بنفسه في المستودع
(كوميتات `evidence(pilot)`):

- `data/pilot_evidence/plan.json` — كل المقاطع `timing_source: "word"`
  بتوقيتات كلمات حقيقية من الخدمة (مثال: `تظن 0.095→0.496`).
- `data/pilot_evidence/caps.ass` — كاريوكي فعلي:
  `{\k40}تظن {\k31}أنك {\k40}تسير ...`
- `state/ar_voices.txt` — 32 صوتًا عربيًا متاحًا لـ edge-tts.
- `data/pilot_report.json` — 40 قطعة على 21 لقطة مختلفة،
  **الحد الأقصى لاستخدام أي لقطة = 2**، كل فحوص البوابة خضراء.
- صوت الحلقة الحالية: `ar-SA-HamedNeural` (الافتراضي) — يُغيَّر بـ
  `XT_VOICE_AR` بعد اختيار المستخدم.
- الفيديو نفسه في الـartifact `pilot-episode` للتشغيل المذكور
  (في تبويب Actions على GitHub).

## أوائل الأوامر للجلسة الجديدة

```bash
git fetch origin && git status --short --branch
python3 tests/test_tts_word_timing.py
node --test tests/publishing.test.js
```

## ما يلزم من المستخدم (لا يغني عنه شيء)

1. إبطال توكنات الدردشة السابقة فورًا من إعدادات حسابه.
2. ~~تعطيل `cosmic-autopilot.yml`~~ ✅ تم بالدمج — الجدولة موقوفة على `main`.
3. نشر تطبيق Google OAuth قبل ~2026-09-23 وإلا مات توكن النشر.
4. اختيار صوت عربي من `state/ar_voices.txt` (32 صوتًا).
5. معاينة حلقة الباولوت والموافقة الصريحة قبل أي نشر.
6. المفاتيح في **Settings → Secrets → Actions** — الدليل الكامل بالروابط
   والحدود المجانية في `docs/API_KEYS_SETUP.md`. اتضاف فعلًا:
   `PIXABAY_API_KEY` · `PEXELS` · `YOUTUBE_API_KEY` · `NASA`/`NASA_API_KEY` ·
   `GROQ_API_KEY` · `GEMINI_API_KEY` · `GNEWS_API_KEY` · `OPENVERSE` ·
   `YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN` (النشر).
   الباقي: `FREESOUND_API_KEY` (بعد تدوير السر المكشوف) و`CURRENTS_API_KEY`
   و`UNSPLASH_ACCESS_KEY` (اختياريين). الكود بيقرأ الموجود تلقائيًا.
