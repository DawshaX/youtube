#!/usr/bin/env python3
"""🛠️ صيانة القناة التلقائية — تشتغل جوّه دورة النشر العادية، بلا وظيفة زيادة.

ليه ده موجود؟ (2026-10-16)
    حلقة طويلة نزلت على القناة **١٥ ثانية** بدل ١٠ دقايق (باج الصوت اللي اتصلح).
    الحلقة المعطوبة لازم تتشال من القناة — بس **الحذف عن بُعد فقط**: أي ملف
    محلي بيفضل مكانه زي ما هو (قاعدة صاحب القناة: مفيش حذف لأي حاجة).

الطريقة (زيادة، مش تعديل):
    `gh workflow run -f mode=purge` كان بيستهلك دورة كاملة ويعطّل سلسلة النبضة.
    دلوقتي: طابور صيانة في `state/maintenance.json` — الدورة بتشوف الطابور في
    أولها، تنفّذ المطلوب، وتنقل العنصر من `todo` لـ`done` (مع الوقت) —
    فمفيش معرفة بتضيع، والطابور نفسه هو السجل.

الاستخدام: python scripts/maintenance_run.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
QUEUE = ROOT / "state" / "maintenance.json"


def _load() -> dict:
    try:
        d = json.loads(QUEUE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def main() -> int:
    bag = _load()
    todo = list(bag.get("todo") or [])
    if not todo:
        print("[صيانة] الطابور فاضي")
        return 0
    done = list(bag.get("done") or [])
    blocked = list(bag.get("blocked") or [])
    left = []
    rc = 0
    for row in todo:
        vid = str((row or {}).get("id") or "").strip()
        if not vid:
            continue
        print(f"[صيانة] حذف من القناة (عن بُعد): {vid} — {(row or {}).get('reason','')}",
              flush=True)
        try:
            p = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "video_delete.py"),
                 "--id", vid, "--yes"],
                capture_output=True, text=True, timeout=180, cwd=str(ROOT))
            out = (p.stdout or "").strip().splitlines()
            ok = p.returncode == 0
            print("[صيانة] " + (out[-1] if out else f"rc={p.returncode}"), flush=True)
        except Exception as exc:  # noqa: BLE001
            ok, out = False, [f"{type(exc).__name__}: {str(exc)[:120]}"]
            print(f"[صيانة] فشل: {out[0]}", flush=True)
        tries = int((row or {}).get("tries") or 0) + 1
        if ok:
            # العنصر **يتنقل** لسجل `done` كامل بوقته — مفيش حذف لأي معرفة
            done.append({**row, "id": vid, "ok": True, "tries": tries,
                         "at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
                         "local_files": "زي ما هي — الحذف عن بُعد فقط"})
        elif tries >= 5:
            # 🛡️ سقف المحاولات: الفشل المتكرر (زي صلاحية OAuth ناقصة) ما يفضلش
            #    يستهلك محاولة كل دورة للأبد. العنصر **يتنقل** لسجل `blocked`
            #    بكل تاريخه وسببه — مفيش حذف لأي معرفة، ونتنيبه في السجل.
            blocked.append({**row, "id": vid, "ok": False, "tries": tries,
                            "blocked_at": time.strftime(
                                "%Y-%m-%d %H:%M UTC", time.gmtime()),
                            "why": ((out[-1] if out else "")[:160] or
                                    "الفشل متكرر — محتاج صلاحية أوسع (delete) "
                                    "على توكن جوجل")})
            print(f"[صيانة] ⛔ {vid} اتوقف بعد {tries} محاولات — "
                  "محتاج صلاحية أوسع (اتسجّل في blocked)", flush=True)
        else:
            row = {**row, "id": vid, "tries": tries,
                   "last_try": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
                   "last_out": (out[-1] if out else "")[:160]}
            left.append(row)
            rc = 1
    bag["todo"] = left
    bag["done"] = done
    bag["blocked"] = blocked
    QUEUE.write_text(json.dumps(bag, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
