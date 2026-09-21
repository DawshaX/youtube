#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# حارس نور المحلي — المصنع بيشتغل من مساحة العمل: إنتاج + تخزين + مزامنة، كل ساعة
#
# ليه؟ عشان المصنع ما يوقفش لو سلسلة GitHub اتأخرت أو الجدولة اتلغت:
#  • بيصحي كل ساعة بالظبط ويشغّل دورة كاملة (طويل أول مرة في اليوم، وبعدها شورت).
#  • بيقفل على قفل واحد (flock) فمستحيل دورتين يشتغلوا في نفس الوقت.
#  • بيسحب آخر ذاكرة من GitHub قبل كل دورة (ما يكررش حلقة اتعملت في السحابة).
#  • بيرجّع الذاكرة + قائمة الموقع (public/noor.json) على GitHub بعد كل دورة.
#  • التخزين في الخزّان والنشر على يوتيوب زي السحابة بالظبط (نفس الكود).
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
cd /home/user/factory || exit 1
LOG=/home/user/noor_loop.log
LOCK=/tmp/noor_keeper.lock
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "[keeper] ⚠️ فيه حارس شغال بالفعل — مفيش تكرار" | tee -a "$LOG"
  exit 0
fi

# مفاتيح التشغيل (التوكن من ملف محلي خارج git)
TOK=$(grep '^CL=' .token_cache 2>/dev/null | cut -d= -f2)
export GITHUB_TOKEN="$TOK" GH_TOKEN="$TOK"
export XT_NET_FOOTAGE=1 XT_STATIC_VAULT=0 XT_YT=1 XT_DAILY_CAP=6
export NOOR_SLOTS='5,9,13,16,19,22'
export PYTHONUNBUFFERED=1

# مساعد الدفع (بلا كتابة التوكن في أي ملف)
cat > /tmp/askpass.sh <<'EOS'
#!/bin/sh
case "$1" in *Username*) echo "x-access-token" ;; *) echo "$GH_PASS" ;; esac
EOS
chmod 700 /tmp/askpass.sh

log() { echo "[$(date -u '+%Y-%m-%d %H:%M:%S')Z] $*" | tee -a "$LOG"; }
log "🚀 حارس نور اشتغل (pid $$) — دورة كل ساعة"

push_state() {
  git add -f state/noor_state.json state/noor_pool.json public/noor.json \
             state/published.json state/media_used.json state/yt_recent.json \
             state/last_publish.json state/last_cycle.json 2>/dev/null
  for f in state/noor_cache/h-*.json; do [ -f "$f" ] && git add -f "$f"; done
  git diff --staged --quiet && return 0
  git commit -q -m "noor(local): ذاكرة الدورة المحلية [skip ci]" 2>/dev/null || true
  for a in 1 2 3 4 5; do
    git pull -q --rebase --autostash origin main >/dev/null 2>&1 || true
    if GH_PASS="$TOK" GIT_ASKPASS=/tmp/askpass.sh git push -q origin HEAD:main 2>/dev/null; then
      log "✓ الذاكرة اتزامنت مع GitHub"; return 0
    fi
    sleep 6
  done
  log "⚠️ مزامنة الذاكرة فشلت — هتتزامن في الدورة الجاية"
}

while true; do
  # آخر حالة من GitHub (لو النت قطع، نكمل بالحالة المحلية)
  git pull -q --rebase --autostash origin main >/dev/null 2>&1 || \
    log "ℹ️ مقدرتش أسحب آخر ذاكرة — هكمل بالحالة المحلية"

  log "▶ دورة إنتاج (شورت/طويل + تخزين + نشر لو الحصة مفتوحة)"
  timeout 3480 python3 scripts/noor_runner.py --cycle 2>&1 | tee -a "$LOG" | tail -14
  log "■ الدورة خلصت (rc=${PIPESTATUS[0]})"
  push_state

  # ننام لحد بداية الساعة الجاية
  now=$(date +%s); next=$(( (now/3600 + 1) * 3600 )); sl=$(( next - now ))
  [ "$sl" -lt 45 ] && sl=45
  log "⏱️ نوم ${sl}ث لحد الساعة الجاية"
  sleep "$sl"
done
