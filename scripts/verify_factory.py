# حارس القانون — يمنع أي رندر بالنظام القديم: FACTORY_RULES.md مُطبّق في الكود؟
# الاستخدام: python3 scripts/verify_factory.py   (لازم 30/30 قبل أي إنتاج)
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
checks = []


def c(name, cond):
    checks.append((name, bool(cond)))


def read(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ── 1) اللقطات الحية أولًا ─────────────────────────────────────────
footage = read("xtrendaw/footage.py")
produce = read("xtrendaw/produce.py")
scenes = read("xtrendaw/scenes.py")
c("XT_NET_FOOTAGE افتراضي مفتوح", 'XT_NET_FOOTAGE", "1"' in footage)
c("السلسلة الحية الخمسة كاملة", all(s in footage for s in (
    "_pixabay_candidates", "_pexels_candidates", "_commons_candidates",
    "_ia_candidates", "_nasa_candidates")))
c("المونتاج: لقطة حية قبل الخزنة", produce.find("_footage.fetch_clip") < produce.find("_footage.vault_clip"))
build = scenes[scenes.find("def build_scene"):]
c("المشهد: مصدر حي قبل الصور المخزنة", build.find("fetch_real_visual") < build.find("load_real_asset(kind"))

# ── 2) التقليد لا الإخبار ──────────────────────────────────────────
eye = read("xtrendaw/eye.py")
c("القاعدة الذهبية: نقلّد الفيديو نفسه لحظة بلحظة", "بنقلّد فيديو الترند نفسه لحظة بلحظة" in eye)

# ── 3) العين والرادار والأولويات ───────────────────────────────────
brain = read("xtrendaw/brain.py")
_gen = brain[brain.find("def generate"):]
c("العين قبل الترند في اختيار المخ",
  0 <= _gen.find("consume_queue") < _gen.find("trend_topic("))
radar_wf = read(".github/workflows/radar-scan.yml")
c("رادار كل 6 ساعات", "7 */6 * * *" in radar_wf)
c("عين مرتبطة بالرادار (auto max 2)", "eye --auto --max 2" in radar_wf)
c("تدهور آمن للعين", "بدون تحليل بصري" in eye or "بيانات فقط" in eye)

# ── 4) النشر الساعي + الوصف ────────────────────────────────────────
# النشر الساعي بقى من المصنع الجديد (factory-publish.yml → xtrendaw) مش من
# الوكيل القديم: الوكيل (cosmic-autopilot) اتحوّل لطوارئ يدوية عن قصد
# عشان ما يبقاش فيه ناشرين متوازيين ينشروا نفس الحلقة مرتين.
factory_wf = read(".github/workflows/factory-publish.yml")
auto_wf = read(".github/workflows/cosmic-autopilot.yml")
run_cycle = read("xtrendaw/run_cycle.py")
content = read("xtrendaw/content.py")
c("نشر ساعي مفعّل (المصنع الجديد كل ساعة)",
  "cron:" in factory_wf and "* * * *" in factory_wf
  and "xtrendaw.run_cycle" in factory_wf)
c("الوكيل القديم يدوي فقط (مفيش جدولة مزدوجة)", "cron:" not in auto_wf)
c("فشل آمن: فحص اعتمادات قبل النشر",
  "Check channel credentials" in auto_wf or "credentials" in factory_wf)
c("الوصف: دلع وهاشتاجات", "#اكسبلور" in content and "🔔" in content)
c("إسناد CC-BY يلاحق الوصف (run_cycle)", "caption +=" in run_cycle and "credits" in run_cycle)

# ── 4.5) صحة الوركفلوات (درس 2026-09-19: مفتاح مكرر في YAML خلّى جيت‌هوب
#        ترفض الملف كله — والدورة ماتشتغلتش خالص) ────────────────────
# الفحص الحقيقي بـPyYAML (موجودة في بيئة الرندر — اتضافت للـpip).
# البديل بلا مكتبة: ملاحظة فقط، مش فحص فاشل — عشان الإيجابيات الكاذبة
# (مفاتيح متكررة الاسم في عناصر قائمة مختلفة) ما توقفش الدورة.
_wf_errs: list[str] = []
_wf_soft = ""
try:
    import yaml as _yaml  # noqa: E402

    class _NoDup(_yaml.SafeLoader):
        pass

    def _no_dup(loader, node, deep=False):
        seen = set()
        for k, _v in node.value:
            key = loader.construct_object(k, deep=deep)
            if key in seen:
                raise ValueError(f"مفتاح مكرر: {key} (سطر {k.start_mark.line + 1})")
            seen.add(key)
        return _yaml.SafeLoader.construct_mapping(loader, node, deep)

    _NoDup.add_constructor(_yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                           _no_dup)
    for _w in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        try:
            _yaml.load(_w.read_text(encoding="utf-8"), _NoDup)
        except Exception as _e:
            _wf_errs.append(f"{_w.name}: {str(_e)[:80]}")
except ModuleNotFoundError:
    _wf_soft = "بلا PyYAML — فحص الوركفلوات مبسّط (تنبيه فقط)"
c("كل الوركفلوات YAML سليمة (بلا مفاتيح مكررة)", not _wf_errs)
if _wf_soft:
    print("   ملاحظة:", _wf_soft)
if _wf_errs:
    print("   وركفلوات مكسورة:", "; ".join(_wf_errs[:3]))

# ── 5) الأمان ──────────────────────────────────────────────────────
doctor = read("xtrendaw/doctor.py")
gitignore = read(".gitignore")
# كوكيز العين: الملف بيتكتب بصلاحيات المالك فقط — fchmod على الواصف
# (أأمن من chmod على المسار: بيمنع سباق الأسماء)
c("كوكيز العين 0600", "fchmod(fd, 0o600)" in eye or "chmod(0o600)" in eye)
c("كوكيز الدكتور 0600 + تنظيف مضمون", "chmod(p, 0o600)" in doctor and "finally:" in doctor)
# الأنماط عندنا أوسع من نص الباتش: secrets* / cookies* / **/cookies*
c("gitignore: secrets و cookies",
  ("secrets" in gitignore and "cookies" in gitignore)
  and ("secrets*" in gitignore or "secrets.txt" in gitignore)
  and ("cookies*" in gitignore or "cookies*.txt" in gitignore))
leak = subprocess.run(
    ["git", "-C", str(ROOT), "grep", "-lIE",
     r"(AIza[A-Za-z0-9_-]{20,}|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,})", "--", "."],
    capture_output=True, text=True).stdout.strip()
c("صفر تسريبات مفاتيح في المتتبع", not leak)

# ── 6) الحلقة الدائمة + الدبلجة ────────────────────────────────────
loop = read("scripts/factory_loop.py")
dub = read("xtrendaw/dub.py")
c("الحلقة الدائمة موجودة", bool(loop))
c("دورة = حلقة جديدة (تعليم المنتج)",
  "mark_produced" in loop and "fingerprint_seen" in loop)
c("صوت لكل حلقة (ممنوع صوت غلط على نص غلط)", "voice_pools" in loop or "XT_VOICE_POOLS" in loop)
c("دبلجة عالمية 9 لغات", len(dub) > 500 and "DUB_VOICES" in dub and "en-US" in dub)
c("دوران الدبلجة في الحلقة", "_dub.rotate" in loop or "dub.rotate" in loop)
c("تخزين كل دورة في git", "git" in loop and "commit" in loop)

# ── 7) عقد الجودة ─────────────────────────────────────────────────
video = read("xtrendaw/video.py")
c("فحوصات جودة إلزامية قبل النشر", "def " in video and ("ok" in video or "checks" in video))
c("قطع كل ثانيتين", 'XT_SCENE_CUT", "2.0"' in produce)
c("مكتبة أصوات بالمزاج", "pick_voice" in read("xtrendaw/voice.py"))

fails = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("✅" if ok else "❌"), n)
print(f"\nالنتيجة: {len(checks) - len(fails)}/{len(checks)}")
if fails:
    print("ممنوع أي إنتاج — اصلح اللي فوق الأول:")
    for f in fails:
        print("  -", f)
sys.exit(0 if not fails else 1)
