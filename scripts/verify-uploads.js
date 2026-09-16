// Verify that every recorded upload still resolves on YouTube.
// Usage: node scripts/verify-uploads.js
//
// Reads data/saved_videos.json and asks YouTube about each video id:
//   1. YouTube Data API v3 videos.list when OAuth credentials or an API key are
//      configured (data/config.json, or YOUTUBE_* secrets via run-autopilot.js).
//   2. The public oEmbed endpoint otherwise (works for public videos, no key).
// Nothing here is simulated: an id that cannot be confirmed is reported as
// unverified and the script exits non-zero.

import fs from 'node:fs';
import { verifyYouTubeVideo } from '../server/youtubeService.js';

const records = JSON.parse(fs.readFileSync('data/saved_videos.json', 'utf-8'));

if (!Array.isArray(records) || records.length === 0) {
  console.log('No confirmed uploads recorded in data/saved_videos.json — nothing to verify.');
  console.log('A real publish requires YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN.');
  process.exit(0);
}

let failures = 0;
for (const record of records) {
  const result = await verifyYouTubeVideo(record.id);
  if (result.verified) {
    console.log(
      `OK   ${record.id}  ${result.url}\n` +
      `     method=${result.method} uploadStatus=${result.uploadStatus ?? 'n/a'} privacy=${result.privacyStatus ?? 'n/a'}\n` +
      `     title="${result.title ?? record.title}"`
    );
  } else {
    failures += 1;
    console.log(`FAIL ${record.id}  ${result.url}  reason=${result.reason} (method=${result.method})`);
  }
}

console.log(`\n${records.length - failures}/${records.length} recorded uploads verified against YouTube.`);
if (failures > 0) process.exitCode = 1;
