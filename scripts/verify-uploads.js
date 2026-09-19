// Verify that every recorded upload still resolves on YouTube.
// Usage: node scripts/verify-uploads.js
//
// Reads data/saved_videos.json and asks YouTube about each video id:
//   1. YouTube Data API v3 videos.list when OAuth credentials or an API key are
//      configured (data/config.json, or YOUTUBE_* secrets via run-autopilot.js).
//   2. The public oEmbed endpoint otherwise (works for public videos, no key).
// Nothing here is simulated: an id that cannot be confirmed is reported as
// unverified. A **recent** unconfirmed upload fails the run; an old record whose
// video was removed from YouTube is reported as stale (see uploadVerification.js).

import fs from 'node:fs';
import { verifyYouTubeVideo } from '../server/youtubeService.js';
import { summarizeVerification } from '../server/uploadVerification.js';

const records = JSON.parse(fs.readFileSync('data/saved_videos.json', 'utf-8'));

if (!Array.isArray(records) || records.length === 0) {
  console.log('No confirmed uploads recorded in data/saved_videos.json — nothing to verify.');
  console.log('A real publish requires YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN.');
  process.exit(0);
}

const results = [];
for (const record of records) {
  results.push(await verifyYouTubeVideo(record.id));
}

const summary = summarizeVerification(records, results);

for (const { record, result } of summary.verified) {
  console.log(
    `OK    ${record.id}  ${result.url}\n` +
    `      method=${result.method} uploadStatus=${result.uploadStatus ?? 'n/a'} privacy=${result.privacyStatus ?? 'n/a'}\n` +
    `      title="${result.title ?? record.title}"`
  );
}
for (const { record, result } of summary.failures) {
  console.log(`FAIL  ${record.id}  ${result.url}  reason=${result.reason} (method=${result.method})` +
    `\n      منشور حديث لازم يتأكد — ده فشل حقيقي.`);
}
for (const { record, result } of summary.stale) {
  console.log(`STALE ${record.id}  ${result.url}  reason=${result.reason}` +
    `\n      سجل قديم: الفيديو مش موجود على يوتيوب (اتشال/اتمسح) — مش فشل نشر.)`);
}

console.log(
  `\n${summary.verified.length}/${records.length} recorded uploads verified against YouTube` +
  ` (نافذة الحداثة ${summary.strictHours} ساعة) — ` +
  `حديث غير مؤكد: ${summary.failures.length}، سجل قديم مُزال: ${summary.stale.length}.`
);
process.exitCode = summary.exitCode;
