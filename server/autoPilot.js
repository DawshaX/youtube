// Cosmic Auto-Pilot Engine
// Runs autonomously without human intervention: scans trends, generates scripts, and publishes

import path from 'path';
import fs from 'fs';
import { publishVideo } from './youtubeService.js';
import { startProduceJob, getJobStatus } from './videoFactoryBridge.js';
import { loadSavedVideos, getYouTubeClient } from './youtubeService.js';

let cycleActive = false;

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
  if (cycleActive) throw new Error('A publishing cycle is already running');
  cycleActive = true;
  autoPilotState.lastRun = new Date().toISOString();
  try {
    const { client, isOAuth } = getYouTubeClient();
    if (!isOAuth || !client) throw new Error('YouTube OAuth is missing. Configure client ID, client secret and refresh token.');
    const channels = await client.channels.list({ part: ['snippet'], mine: true });
    if (!channels.data.items?.length) throw new Error('No YouTube channel found for this authorization');
    addAutoPilotLog(`القناة المتصلة: ${channels.data.items[0].snippet.title}`);

    // Use a finite, authored queue, not unrelated trending titles or recycled MP4s.
    const topics = JSON.parse(fs.readFileSync(path.resolve('content/topics.json'), 'utf8'));
    const published = loadSavedVideos().filter(v => v.liveUploaded);
    const topic = topics.find(t => !published.some(v => v.title === `${t.title_ar} #Shorts` || v.title === t.title_ar));
    if (!topic) throw new Error('Topic queue exhausted. Add new original topics before publishing again.');
    autoPilotState.currentPublishingTitle = topic.title_ar;
    const job = await startProduceJob(topic);
    const deadline = Date.now() + 20 * 60 * 1000;
    let status;
    while (Date.now() < deadline) {
      status = getJobStatus(job.jobId);
      if (status.status === 'error') throw new Error(status.error);
      if (status.status === 'completed') break;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    if (status?.status !== 'completed') throw new Error('Video production timed out');
    const result = await publishVideo({
      videoFilePath: status.outputVideo.filePath,
      title: topic.title_ar,
      description: [topic.hook_ar, ...(topic.facts_ar || []), topic.outro_ar].join('\n\n'),
      tags: (topic.tags || '').split(','),
      privacyStatus: 'public', categoryId: '28', isShort: true
    });
    if (!result.video?.liveUploaded) throw new Error('Live upload was not confirmed');
    autoPilotState.totalAutoPublished += 1;
    addAutoPilotLog(`✅ رابط الفيديو الحقيقي: ${result.video.url}`);
    return result;
  } catch (err) {
    addAutoPilotLog(`❌ ${err.message}`);
    throw err;
  } finally {
    cycleActive = false;
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
    runAutoPilotCycle().catch(() => {});
  } else {
    const ms = autoPilotState.intervalHours * 60 * 60 * 1000;
    autoPilotState.nextRun = new Date(Date.now() + ms).toISOString();
    const intervalMins = Math.round(autoPilotState.intervalHours * 60);
    addAutoPilotLog(`⚡ تم تفعيل الطيار الآلي المستمر بنجاح (النشر التلقائي يعمل دورياً كل ${intervalMins} دقيقة 24/7).`);
    runAutoPilotCycle().catch(() => {});

    autoPilotInterval = setInterval(() => {
      runAutoPilotCycle().catch(() => {});
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
