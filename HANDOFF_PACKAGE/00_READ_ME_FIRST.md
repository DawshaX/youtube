# 00 — اقرأ هذا أولًا

ترتيب القراءة:

1. هذا الملف.
2. `../HANDOFF_BRIEF.md` (القواعد الصارمة وحالة المراحل).
3. `NOTES_TO_NEXT_SESSION.md` (ما الذي تحقق فعليًا وكيف تتحقق منه بنفسك).
4. `../docs/FACTORY_BLUEPRINT.md` (الطبقات الـ12 — ما اكتمل وما لم يبدأ).
5. `../docs/MEDIA_VAULT_SOURCES.md` (سلم تراخيص مصادر الميديا).
6. `PASTE_THIS.md` فقط لو بدأت جلسة جديدة تمامًا من الصفر — الصقه كافتتاحية.

## أهم ثلاث نقاط

1. **اختبارات التوقيت المحلية ليست دليلًا** على `"timing_source": "word"` في الإنتاج.
   الدليل الوحيد: ملف `plan.json` من تشغيل حقيقي على GitHub Actions
   (سير `pilot-render` يرفعه كـ artifact باسم `pilot-evidence`).
2. **التكرار له بابان**: `data/production_log.json` (الملفات الوسيطة) و
   `state/saved_videos.json` (المنشور). أي منطق جديد يجب أن يحترم الاثنين —
   راجع `pruneProductionLog` في `server/autoPilot.js` والاختبار التاسع.
3. **حزمة الجلسة السابقة الأقدم كودها قديم** — الباتش الوحيد منها (تحسينات
   `cosmic-autopilot.yml`) مدموج أصلًا عبر PR #4. لا تطبق أي كود آخر منها.

## تحذيرات تشغيلية

- سطر واحد = توليفة صوتية واحدة دائمًا. أي تعديل على `xtrendaw/tts.py` يجب أن
  يُبقي `tests/test_tts_word_timing.py` أخضر.
- لا تضع `data/production_log.json` في `.gitignore`.
- أي مصدر ميديا جديد: سجّله في `vault/index.json` أولًا (رخصة مسموحة فقط —
  راجع `ALLOWED_LICENSES` في `xtrendaw/vault.py`) وإلا سيفشل الرندر عمدًا.
