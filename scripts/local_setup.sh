#!/usr/bin/env bash
# إعداد النسخة المحلية (بيحتاج يتشغّل بعد أي استرجاع لمساحة العمل).
# السبب: ملف .git/config مستثنى من لقطات مساحة العمل (بيدخل ضمن ملفات
# الاعتمادات الحساسة)، فبيرجع الريبو بلا ريموت وبلا هوية — السكربت ده يرجّعهم.
set -euo pipefail
cd "$(dirname "$0")/.."
TOK="${1:-$(grep '^CL=' .token_cache 2>/dev/null | cut -d= -f2)}"
[ -z "$TOK" ] && { echo "⚠️ مفيش توكن — حُطّه في .token_cache أو مرّره كأول وسيط"; exit 1; }
git config user.name "daousha-factory"
git config user.email "daousha-factory@users.noreply.github.com"
git remote remove origin 2>/dev/null || true
git remote add origin "https://x-access-token:${TOK}@github.com/DawshaX/youtube.git"
echo "✓ النسخة المحلية جاهزة (ريموت + هوية) — الشغل الرسمي على GitHub"
