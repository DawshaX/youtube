// سياسة التحقق من المنشور: إيه اللي يُعد فشل، وإيه اللي «سجل قديم»؟
//
// الدرس (تشغيل 2026-09-19): خطوة التحقق في cosmic-autopilot فشلت والسير كله
// اتعلّم عليه فاشل، مع إن الفيديو الجديد اتنشر واتأكد فعلًا:
//     OK   MGVIVX-Sa3U  method=youtube.videos.list uploadStatus=uploaded privacy=public
//     FAIL 4gBNYCYaDRM … reason=YouTube returned no video for this id   (مقطع قديم اتشال)
// يعني 4 سجلات قديمة لمقاطع اتشالت من القناة كانت بتسقّط كل دورة نشر ساعية.
//
// القاعدة الصحيحة:
//   - فيديو المنشور **دلوقتي** (داخل نافذة الحداثة) لازم يتأكد، وإلا السير يفشل.
//   - سجل قديم مش لاقي الفيديو بتاعه على يوتيوب = «سجل قديم/مُزال» وبيتعرض
//     كتحذير واضح، مش فشل — بلا ما نمسح بيانات المستخدم من نفسنا.

const HOUR_MS = 3600 * 1000;

function recordTime(record) {
  for (const key of ['publishedAt', 'uploadedAt', 'verifiedAt', 'liveUploaded']) {
    const value = record?.[key];
    if (!value) continue;
    const ms = Date.parse(value);
    if (!Number.isNaN(ms)) return ms;
  }
  return null;
}

export function summarizeVerification(records, results, options = {}) {
  const strictHours = Number(options.strictHours ?? process.env.VERIFY_STRICT_HOURS ?? 24);
  const now = Number(options.now ?? Date.now());

  const verified = [];
  const failures = [];
  const stale = [];

  records.forEach((record, index) => {
    const result = results[index] || {};
    if (result.verified) {
      verified.push({ record, result });
      return;
    }
    const at = recordTime(record);
    const isRecent = at !== null && (now - at) <= strictHours * HOUR_MS;
    (isRecent ? failures : stale).push({ record, result });
  });

  return {
    verified,
    failures,
    stale,
    strictHours,
    // سجل قديم مش بيوقف النشر — بس بيتعرض. الفشل الحقيقي: منشور حديث مش متأكد.
    exitCode: failures.length > 0 ? 1 : 0,
  };
}
