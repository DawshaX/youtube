// Cosmic Auto-Pilot Engine
// Runs autonomously without human intervention: scans trends, generates scripts, and publishes

import path from 'path';
import fs from 'fs';
import { getTrendingVideos, publishVideo, loadConfig, saveConfig } from './youtubeService.js';
import { generateViralBlueprint, generateInfiniteViralIdeas } from './viralEngine.js';
import { listProducedVideos } from './videoFactoryBridge.js';

let autoPilotInterval = null;
let turboTimeout = null;

let autoPilotState = {
  running: false,
  continuousTurbo: false,
  lastRun: null,
  nextRun: null,
  intervalHours: 0.5,
  turboDelaySeconds: 20,
  totalAutoPublished: 0,
  currentPublishingTitle: '',
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
    let ideaTitle = '';
    let category = 'challenges';

    if (autoPilotState.continuousTurbo) {
      // Pick a fresh viral idea from the infinite matrix
      const freshIdeas = generateInfiniteViralIdeas(1);
      const chosen = freshIdeas[0];
      ideaTitle = chosen.titleAr;
      category = chosen.niche || 'challenges';
      addAutoPilotLog(`[الوضع التوربيني المستمر] سحب فكرة جديدة من مصفوفة الملايين: "${ideaTitle}"`);
    } else {
      // 1. Scan Global Trends
      addAutoPilotLog('مسح ترندات يوتيوب العالمية لرصد الفيديوهات رقم 1...');
      const trends = await getTrendingVideos('US', 'all');
      if (trends && trends.length > 0) {
        const topTrend = trends[Math.floor(Math.random() * Math.min(trends.length, 5))];
        ideaTitle = topTrend.title;
        category = topTrend.category || 'challenges';
        addAutoPilotLog(`تم التقاط أقوى فكرة متصدرة: "${ideaTitle}"`);
      } else {
        const fresh = generateInfiniteViralIdeas(1)[0];
        ideaTitle = fresh.titleAr;
        category = fresh.niche;
      }
    }

    autoPilotState.currentPublishingTitle = ideaTitle;

    // 2. Generate Viral Package
    addAutoPilotLog('توليد السيناريو، خطاف الـ 3 ثواني، وسيو التوزيع الخوارزمي...');
    const blueprint = generateViralBlueprint(ideaTitle, category);

    const chosenTitle = blueprint.titles[0]?.titleAr || ideaTitle;
    const desc = `${blueprint.multiLanguagePack?.arabic?.description || ''}\n\n${blueprint.hashtagsString}`;

    // 3. Link with produced MP4 video file
    let videoFilePath = null;
    let thumbnailFilePath = null;
    try {
      const producedList = listProducedVideos();
      if (producedList && producedList.length > 0) {
        // Pick the latest produced video or mrbeast_challenge
        const matchedVid = producedList.find(v => v.id === 'mrbeast_challenge') || producedList[0];
        videoFilePath = matchedVid.path;
        const cover = path.resolve('content/vids', `${matchedVid.id}-cover.png`);
        if (fs.existsSync(cover)) thumbnailFilePath = cover;
        addAutoPilotLog(`ربط ملف الفيديو الفيروسي الحقيقي MP4 (${matchedVid.filename}, ${matchedVid.sizeMB}MB)...`);
      }
    } catch (e) {
      console.warn('Video linking notice:', e.message);
    }

    // 4. Auto Publish / Queue
    addAutoPilotLog(`نشر الفيديو تلقائياً لقناتك: "${chosenTitle}"`);
    const result = await publishVideo({
      videoFilePath,
      thumbnailFilePath,
      title: chosenTitle,
      description: desc,
      tags: blueprint.tags,
      privacyStatus: 'public',
      categoryId: '24',
      isShort: true
    });

    autoPilotState.totalAutoPublished += 1;
    addAutoPilotLog(`✅ تم النشر التلقائي بنجاح! رابط الفيديو: ${result.video.url}`);

    // If Continuous Turbo Mode is ON, immediately queue the next video!
    if (autoPilotState.continuousTurbo && autoPilotState.running) {
      const delay = autoPilotState.turboDelaySeconds || 20;
      autoPilotState.nextRun = new Date(Date.now() + delay * 1000).toISOString();
      addAutoPilotLog(`⚡ [الوضع التوربيني المستمر] تم إنجاز الفيديو #${autoPilotState.totalAutoPublished}! سيبدأ تجهيز ونشر الفيديو التالي تلقائياً بعد ${delay} ثانية...`);
      
      if (turboTimeout) clearTimeout(turboTimeout);
      turboTimeout = setTimeout(() => {
        if (autoPilotState.running && autoPilotState.continuousTurbo) {
          runAutoPilotCycle();
        }
      }, delay * 1000);
    }

  } catch (err) {
    addAutoPilotLog(`❌ خطأ أثناء دورة الأتمتة: ${err.message}`);
  }
}

export function startAutoPilot(intervalHours = 0.5, continuousTurbo = false, turboDelaySeconds = 20) {
  if (autoPilotInterval) clearInterval(autoPilotInterval);
  if (turboTimeout) clearTimeout(turboTimeout);

  autoPilotState.running = true;
  autoPilotState.continuousTurbo = Boolean(continuousTurbo);
  autoPilotState.turboDelaySeconds = Number(turboDelaySeconds) || 20;
  autoPilotState.intervalHours = Number(intervalHours) || 0.5;

  if (autoPilotState.continuousTurbo) {
    addAutoPilotLog(`🚀 تم تفعيل الوضع التوربيني المستمر (النشر المتواصل غير المنقطع: كل ما ينتهي فيديو يُنشر التالي فوراً بعد ${autoPilotState.turboDelaySeconds} ثانية).`);
    runAutoPilotCycle();
  } else {
    const ms = autoPilotState.intervalHours * 60 * 60 * 1000;
    autoPilotState.nextRun = new Date(Date.now() + ms).toISOString();
    const intervalMins = Math.round(autoPilotState.intervalHours * 60);
    addAutoPilotLog(`⚡ تم تفعيل الطيار الآلي المستمر بنجاح (النشر التلقائي يعمل دورياً كل ${intervalMins} دقيقة 24/7).`);
    runAutoPilotCycle();

    autoPilotInterval = setInterval(() => {
      runAutoPilotCycle();
      autoPilotState.nextRun = new Date(Date.now() + ms).toISOString();
    }, ms);
  }

  return autoPilotState;
}

export function stopAutoPilot() {
  if (autoPilotInterval) {
    clearInterval(autoPilotInterval);
    autoPilotInterval = null;
  }
  if (turboTimeout) {
    clearTimeout(turboTimeout);
    turboTimeout = null;
  }
  autoPilotState.running = false;
  autoPilotState.continuousTurbo = false;
  autoPilotState.nextRun = null;
  addAutoPilotLog('تم إيقاف الطيار الآلي والوضع التوربيني مؤقتاً.');
  return autoPilotState;
}
