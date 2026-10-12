#!/usr/bin/env python3
"""🛡️ حارس الذاكرة — يمنع فساد ملفات `state/` للأبد.

القصة الحقيقية (2026-10-12): الدورة كانت بتعمل
`git pull --rebase --autostash` قبل الدفع. لما حصل تعارض في ملفات الذاكرة،
git ساب **علامات التعارض** (`<<<<<<<`, `=======`, `>>>>>>>`) جوه الملفات،
والدورة كومّتتها على `main` وهي مكسورة → كل دورة بعدها بتفشل في قراءة JSON
→ المصنع وقف 10 ساعات وهو «شغال».

الحل: بوابة إجبارية قبل أي كوميت — تصلّح أو تسترجع أو ترفض. مفيش ملف مكسور
يوصل لـ git تاني.

الاستخدام:
    python3 scripts/state_guard.py --check      # فحص بس (كود خروج 1 لو فيه مكسور)
    python3 scripts/state_guard.py --fix        # إصلاح في المكان
    python3 scripts/state_guard.py --fix --quiet
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# الملفات الحرجة — الملفات دي لو اتلفت المصنع كله يقف
CRITICAL = [
    "state/noor_library.json",
    "state/noor_state.json",
    "state/published.json",
    "state/media_used.json",
    "state/yt_recent.json",
    "state/last_publish.json",
    "state/last_cycle.json",
    "state/noor_pool.json",
    "state/noor_ledger.json",
    "state/produced.json",
    "state/ledger.json",
    "state/quota_ceiling.json",
    "state/reciter_badlist.json",
    "state/reciter_proven.json",
]

CONFLICT_RE = re.compile(
    r"<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n", re.S
)
ANY_MARKER = re.compile(r"^(<<<<<<<|=======|>>>>>>>)", re.M)


def _json_ok(text: str):
    """يرجّع (True, obj) لو النص JSON سليم، أو (False, سبب) لو مكسور."""
    try:
        return True, json.loads(text)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _from_git(path: str) -> str | None:
    """آخر نسخة سليمة من الفرع البعيد (أو HEAD)."""
    for ref in ("origin/main", "HEAD"):
        try:
            out = subprocess.run(
                ["git", "show", f"{ref}:{path}"],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout
        except Exception:
            pass
    return None


def repair_text(text: str) -> tuple[str | None, str]:
    """يحاول يصلّح نص فيه علامات تعارض. يرجّع (نص سليم أو None, وصف اللي حصل)."""
    if not ANY_MARKER.search(text):
        ok, obj = _json_ok(text)
        return (text, "سليم أصلًا") if ok else (None, f"مكسور بدون تعارض ({obj})")

    n = len(CONFLICT_RE.findall(text))
    candidates: list[tuple[str, str]] = []

    # 1) ناخد جانب «Stashed changes» (الشغل المحلي الأحدث) لكل تعارض
    candidates.append((CONFLICT_RE.sub(lambda m: m.group(2), text), "جانبنا (Stashed)"))
    # 2) ناخد جانب «Updated upstream» لكل تعارض
    candidates.append((CONFLICT_RE.sub(lambda m: m.group(1), text), "جانب المصدر (Upstream)"))
    # 3) نحاول دمج الجانبين (يمشي مع المصفوفات والأوبجكتات المتوافقة)
    candidates.append(
        (CONFLICT_RE.sub(lambda m: m.group(1).rstrip("\n,\n") + ",\n" + m.group(2), text), "دمج الجانبين")
    )

    for cand, label in candidates:
        ok, _ = _json_ok(cand)
        if ok:
            return cand, f"اتصلّح بأخذ {label} ({n} تعارض)"

    # 4) نجيب النسخة السليمة من git
    return None, f"مفيش حل محلي ({n} تعارض)"


def guard_file(path: str, fix: bool, quiet: bool = False) -> tuple[bool, str]:
    """يرجّع (تمام؟, رسالة)."""
    p = ROOT / path
    if not p.exists():
        return True, f"{path}: مش موجود (تمام)"

    text = p.read_text(encoding="utf-8", errors="replace")
    ok, err = _json_ok(text)
    if ok:
        return True, f"{path}: ✅ سليم"

    if not fix:
        return False, f"{path}: ❌ مكسور — {err}"

    # محاولة إصلاح
    fixed, how = repair_text(text)
    if fixed is None:
        git_text = _from_git(path)
        if git_text:
            gok, _ = _json_ok(git_text)
            if gok:
                fixed, how = git_text, "اتسترجع من آخر نسخة سليمة في git"

    if fixed is None:
        # آخر حل: ننسخ المكسور جانب ونبدأ من هيكل فاضي
        p.with_suffix(p.suffix + ".corrupt-backup").write_text(text, encoding="utf-8")
        fixed, how = ("[]" if path.endswith("published.json") else "{}"), "فاضي + نسخة احتياطية من المكسور"

    # نتأكد إن اللي هنكتبه سليم فعلًا
    fok, ferr = _json_ok(fixed)
    if not fok:
        return False, f"{path}: ❌ فشل الإصلاح ({ferr})"

    p.write_text(fixed, encoding="utf-8")
    if not quiet:
        print(f"   🔧 {path}: {how}", flush=True)
    return True, f"{path}: 🔧 {how}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="إصلاح في المكان")
    ap.add_argument("--check", action="store_true", help="فحص بس")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--all", action="store_true", help="افحص كل ملفات state/*.json مش الحرجة بس")
    args = ap.parse_args()

    targets = list(CRITICAL)
    if args.all:
        for f in sorted((ROOT / "state").glob("*.json")):
            rel = str(f.relative_to(ROOT))
            if rel not in targets:
                targets.append(rel)

    bad, fixed, ok = 0, 0, 0
    for path in targets:
        good, msg = guard_file(path, fix=args.fix, quiet=args.quiet)
        if good:
            if "🔧" in msg or "استرجع" in msg:
                fixed += 1
            else:
                ok += 1
        else:
            bad += 1
        if not args.quiet and (bad or "🔧" in msg or args.check):
            print("  ", msg, flush=True)

    if not args.quiet:
        print(f"🛡️ حارس الذاكرة: {ok} سليم · {fixed} اتصلّح · {bad} مكسور", flush=True)

    if args.check and bad:
        return 1
    return 0 if bad == 0 or args.fix else 1


if __name__ == "__main__":
    raise SystemExit(main())
