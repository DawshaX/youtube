// Cosmic Auto-Pilot Engine
// Runs autonomously without human intervention: scans trends, generates scripts, and publishes

import { getTrendingVideos, publishVideo, loadConfig, saveConfig } from './youtubeService.js';
import { generateViralBlueprint } from './viralEngine.js';

let autoPilotInterval = null;
let autoPilotState = {
  running: false,
  lastRun: null,
  nextRun: null,
  intervalHours: 6,
  totalAutoPublished: 0,
  logs: []
};

export function getAutoPilotStatus() {
  return autoPilotState;
}

export function addAutoPilotLog(message) {
  const timestamp = new Date().toLocaleTimeString();
  const entry = `[${timestamp}] ${message}`;
  autoPilotState.logs.unshift(entry);
  if (autoPilotState.logs.length > 50) autoPilotState.logs.pop();
  console.log(`🤖 [AutoPilot] ${entry}`);
}

export async function runAutoPilotCycle() {
  addAutoPilotLog('بدء دورة الأتمتة الكونية الشاملة...');
  autoPilotState.lastRun = new Date().toISOString();

  try {
    // 1. Scan Global Trends
    addAutoPilotLog('مسح ترندات يوتيوب العالمية لرصد الفيديوهات رقم 1...');
    const trends = await getTrendingVideos('US', 'all');
    if (!trends || trends.length === 0) {
      addAutoPilotLog('تعذر جلب الترندات الحالية، تخطي الدورة.');
      return;
    }

    // Pick top velocity video
    const topTrend = trends[0];
    addAutoPilotLog(`تم التقاط أقوى فكرة متصدرة: "${topTrend.title}"`);

    // 2. Generate Viral Package
    addAutoPilotLog('توليد السيناريو، خطاف الـ 3 ثواني، وسيو التوزيع الخوارزمي...');
    const blueprint = generateViralBlueprint(topTrend.title, topTrend.category || 'challenges');

    const chosenTitle = blueprint.titles[0]?.titleAr || topTrend.title;
    const desc = `${blueprint.multiLanguagePack?.arabic?.description || ''}\n\n${blueprint.hashtagsString}`;

    // 3. Auto Publish / Queue
    addAutoPilotLog(`نشر الفيديو تلقائياً لقناتك: "${chosenTitle}"`);
    const result = await publishVideo({
      videoFilePath: null,
      thumbnailFilePath: null,
      title: chosenTitle,
      description: desc,
      tags: blueprint.tags,
      privacyStatus: 'public',
      categoryId: '24',
      isShort: false
    });

    autoPilotState.totalAutoPublished += 1;
    addAutoPilotLog(`✅ تم النشر التلقائي بنجاح! رابط الفيديو: ${result.video.url}`);

  } catch (err) {
    addAutoPilotLog(`❌ خطأ أثناء دورة الأتمتة: ${err.message}`);
  }
}

export function startAutoPilot(intervalHours = 6) {
  if (autoPilotInterval) {
    clearInterval(autoPilotInterval);
  }

  autoPilotState.running = true;
  autoPilotState.intervalHours = intervalHours;
  const ms = intervalHours * 60 * 60 * 1000;
  autoPilotState.nextRun = new Date(Date.now() + ms).toISOString();

  addAutoPilotLog(`تم تفعيل الطيار الآلي المستمر بنجاح (يعمل كل ${intervalHours} ساعات تلقائياً).`);

  // Run first cycle immediately
  runAutoPilotCycle();

  autoPilotInterval = setInterval(() => {
    runAutoPilotCycle();
    autoPilotState.nextRun = new Date(Date.now() + ms).toISOString();
  }, ms);

  return autoPilotState;
}

export function stopAutoPilot() {
  if (autoPilotInterval) {
    clearInterval(autoPilotInterval);
    autoPilotInterval = null;
  }
  autoPilotState.running = false;
  autoPilotState.nextRun = null;
  addAutoPilotLog('تم إيقاف الطيار الآلي مؤقتاً.');
  return autoPilotState;
}
