import fs from 'node:fs';
const required = ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN'];
const missing = required.filter(key => !process.env[key]);
if (missing.length) {
  console.error(`Missing GitHub Actions secrets: ${missing.join(', ')}`);
  process.exit(1);
}
fs.mkdirSync('data', { recursive: true });
fs.writeFileSync('data/config.json', JSON.stringify({
  apiKey: process.env.YOUTUBE_API_KEY || '',
  clientId: process.env.YOUTUBE_CLIENT_ID,
  clientSecret: process.env.YOUTUBE_CLIENT_SECRET,
  tokens: { refresh_token: process.env.YOUTUBE_REFRESH_TOKEN },
  connected: true, mode: 'live'
}), { mode: 0o600 });
// مشروع جوجل تاني (اختياري): حصة يومية إضافية 10,000 وحدة
const alt = {
  clientId: process.env.YOUTUBE_CLIENT_ID_2,
  clientSecret: process.env.YOUTUBE_CLIENT_SECRET_2,
  refreshToken: process.env.YOUTUBE_REFRESH_TOKEN_2,
};
if (alt.clientId && alt.clientSecret && alt.refreshToken) {
  fs.writeFileSync('data/config.alt.json', JSON.stringify({
    apiKey: process.env.YOUTUBE_API_KEY || '',
    clientId: alt.clientId,
    clientSecret: alt.clientSecret,
    tokens: { refresh_token: alt.refreshToken },
    connected: true, mode: 'live'
  }), { mode: 0o600 });
  console.log('➕ اعتماد إضافي (مشروع تاني) متاح — الحصة هتتضاعف');
}

try {
  const { runAutoPilotCycle, refreshDataFromRemote } = await import('../server/autoPilot.js');
  // ناخد أحدث سجل نشر/طابور من الريموت قبل أي قرار — يمنع سباق النسخ القديمة
  if (refreshDataFromRemote()) console.log('↻ ملفات القرار اتحدّثت من origin/main');
  await runAutoPilotCycle();
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
} finally {
  fs.rmSync('data/config.json', { force: true });
  fs.rmSync('data/config.alt.json', { force: true });
}
