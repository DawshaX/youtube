# 🧰 أدوات المصنع

## أدوات أصلية (كانت موجودة)
`noor_grid_check.py` · `noor_sense_check.py` · `noor_thousand_check.py` · `noor_tree_check.py` · `noor_variety_check.py`

## أدوات مُدمجة من `DawshaX/XTreNDAW` (2026-10-12 · إضافة بحتة)
| الأداة | بتعمل إيه | حالة التشغيل |
|---|---|---|
| `hadith_clean_check.py` | فحص ذاتي لتنقية بنك الحديث من سلسلة الرواة («حدثنا…» في العنوان) | ⚠️ بيحتاج أسماء دوال `din.py` بتاعة XTreNDAW. **تحققنا يدويًا:** مكتبتنا (7512 عنصر) فيها **صفر** عنصر فيه سلسلة رواة، فالأداة شبكة أمان للمستقبل |
| `quran_sample.py` | يبني عينة تلاوة للفحص بلا نشر | جاهز |
| `release_sample.py` | يرفع عينة على Releases | جاهز |
| `voice_lab.py` | معمل أصوات (XTTS-v2) — نستفيد منه في اختيار صوت كل ركيزة | جاهز (بيحتاج TTS_HOME) |
| `expand_bank.py` | توسيع بنك المحتوى (26KB) | جاهز |
| `cleanup.py` | تنضيف | جاهز |
| `tg_fix.py` | تعديل/حذف رسالة تليجرام على القناة | جاهز (بيحتاج TELEGRAM_BOT_TOKEN + CHAT_ID) |

**المصدر:** `https://github.com/DawshaX/XTreNDAW/tree/main/tools` — نقلناهم هنا عشان تبقى كل الأدوات في مكان واحد (المصنع النهائي)، ومفيش حاجة اتشالت من الريبو الأصلي.
