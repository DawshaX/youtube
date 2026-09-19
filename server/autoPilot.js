// Cosmic Auto-Pilot Engine
// Runs autonomously without human intervention: scans trends, generates scripts, and publishes

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { publishVideo } from './youtubeService.js';
import { startProduceJob, getJobStatus, listProductionQueue } from './videoFactoryBridge.js';
import { loadSavedVideos, getYouTubeClient } from './youtubeService.js';
import { emitEvent } from './bus.js';

const ROOT_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const PRODUCTION_LOG_PATH = path.join(ROOT_DIR, 'data', 'production_log.json');

// Artifact paths are stored relative to the repo root so the log stays valid on
// any machine (local sandbox, CI runner) instead of pinning one absolute path.
const repoRel = abs => path.relative(ROOT_DIR, abs).split(path.sep).join('/');

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
  totalProduced: 0,
  currentPublishingTitle: '',
  lastArtifact: null,
  publishBlockedReason: null,
  logs: []
};

// ─────────────────────────────────────────────────────────────
// سقف الحصة اليومية ليوتيوب
// ─────────────────────────────────────────────────────────────
// يوتيوب بيحسب الحصة من منتصف الليل بتوقيت المحيط الهادئ (PT)، والرفعة الواحدة
// بتكلّف 1600 وحدة من أصل 10,000 يوميًا = **6 رفعات يوميًا كحد أقصى** بالحصة
// الافتراضية. النشر الساعي معناه 24 محاولة في اليوم → بعد السادسة كل محاولة
// هتفشل بـ quotaExceeded وتستهلك Actions بلا داعي. فبنعدّ ونوقف بهدوء (خروج
// ناجح) ونكمّل تلقائيًا بعد تجديد الحصة.
const QUOTA_TZ = 'America/Los_Angeles';
const DEFAULT_DAILY_CAP = 6;

export function quotaDayKey(value) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: QUOTA_TZ, year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(d);
}

export function uploadsInCurrentQuotaDay(records = [], log = [], now = new Date()) {
  // ⚠️ مش بنجمع القايمتين: saved_videos وproduction_log بيوصفوا **نفس** الرفعات
  // (بمعرّفات مختلفة: video id مقابل topicId) — فجمعهم بيعدّ الرفعة مرتين
  // ويخلّي السقف يتفعّل بدري. الأولوية للسجل المؤكد (saved_videos).
  const today = quotaDayKey(now);
  const confirmed = new Set();
  for (const record of records) {
    if (!record || typeof record !== 'object') continue;
    const stamp = record.publishedAt || record.uploadedAt || record.verifiedAt;
    if (!stamp || quotaDayKey(stamp) !== today) continue;
    confirmed.add(record.id || record.videoId || String(stamp));
  }
  if (confirmed.size) return confirmed.size;

  // مفيش سجل رفعات مؤكد لليوم ده → نرجع لسجل الإنتاج (المنشور فقط، مش المنتَج)
  const produced = new Set();
  for (const record of log) {
    if (!record || typeof record !== 'object' || record.published === false) continue;
    const stamp = record.producedAt || record.publishedAt;
    if (!stamp || quotaDayKey(stamp) !== today) continue;
    produced.add(record.videoId || record.topicId || record.filePath || String(stamp));
  }
  return produced.size;
}

export function dailyUploadCap() {
  const raw = Number(process.env.XT_MAX_UPLOADS_PER_DAY ?? DEFAULT_DAILY_CAP);
  return Number.isFinite(raw) && raw > 0 ? Math.floor(raw) : DEFAULT_DAILY_CAP;
}

export function loadProductionLog() {
  try {
    if (fs.existsSync(PRODUCTION_LOG_PATH)) {
      return JSON.parse(fs.readFileSync(PRODUCTION_LOG_PATH, 'utf-8'));
    }
  } catch (err) {
    console.error('Error reading production log:', err.message);
  }
  return [];
}

function appendProductionRecord(record) {
  const list = loadProductionLog();
  list.unshift(record);
  fs.mkdirSync(path.dirname(PRODUCTION_LOG_PATH), { recursive: true });
  fs.writeFileSync(PRODUCTION_LOG_PATH, JSON.stringify(list, null, 2), 'utf-8');
  return record;
}

// A workspace reset removes the rendered MP4s (they are gitignored) but not the
// log, so dead UNPUBLISHED entries drop out before the queue is read.
// Entries with `published: true` are historical record — they stay forever,
// even when the artifact is gone from disk, so the committed log never loses
// what actually went live on YouTube (saved_videos.json backs this up too).
export function pruneProductionLog() {
  const list = loadProductionLog();
  const kept = list.filter(entry => entry.published === true
    || (entry.filePath && fs.existsSync(path.join(ROOT_DIR, entry.filePath))));
  if (kept.length !== list.length) {
    fs.writeFileSync(PRODUCTION_LOG_PATH, JSON.stringify(kept, null, 2), 'utf-8');
  }
  return list.filter(entry => !kept.includes(entry));
}

// Next queue entry that has neither been rendered nor published yet.
export function pickNextProductionTopic() {
  pruneProductionLog();
  const published = loadSavedVideos().filter(v => v.liveUploaded);
  const produced = loadProductionLog();
  const queue = listProductionQueue();
  return queue.find(topic => {
    const title = topic.title_ar;
    if (published.some(v => v.title === `${title} #Shorts` || v.title === title)) return false;
    return !produced.some(p => p.topicId === topic.id);
  }) || null;
}

async function renderTopic(topic) {
  const job = await startProduceJob(topic);
  const deadline = Date.now() + 20 * 60 * 1000;
  let status = null;
  while (Date.now() < deadline) {
    status = getJobStatus(job.jobId);
    if (status.status === 'error') throw new Error(status.error);
    if (status.status === 'completed') break;
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  if (status?.status !== 'completed') throw new Error('Video production timed out');
  return status;
}

// Production half of the cycle: radar topic -> real MP4 on disk, nothing published.
// Safe to run without any YouTube credentials, and it never invents a video link.
export async function runProductionCycle() {
  if (cycleActive) throw new Error('A publishing cycle is already running');
  cycleActive = true;
  autoPilotState.lastRun = new Date().toISOString();
  try {
    const topic = pickNextProductionTopic();
    if (!topic) throw new Error('Topic queue exhausted. Add new original topics before producing again.');
    autoPilotState.currentPublishingTitle = topic.title_ar;
    emitEvent('cycle:produce-start', { topicId: topic.id, title: topic.title_ar, source: topic.source || 'queue' });

    const status = await renderTopic(topic);
    const out = status.outputVideo;
    const info = out.report?.validate?.info || {};
    const audioSources = out.audioSources || [];
    if (audioSources.length && audioSources.every(s => s === 'fallback')
        && process.env.COSMIC_ALLOW_FALLBACK_AUDIO !== '1') {
      // صوت النغمة الاصطناعية = حلقة بلا سرد حقيقي. ما نسجلهاش في سجل
      // الإنتاج (وإلا الموضوع يتعلم كـ"منتج" ويتشال من الطابور للأبد) —
      // الملف يتشال والموضوع يفضل في الطابور للمحاولة الجاية لما خدمة
      // النطق تبقى متاحة.
      try { fs.unlinkSync(path.resolve(out.filePath)); } catch (_) {}
      throw new Error('Narration fell back to a synthetic tone (TTS unreachable). Episode not recorded; the topic stays in the queue. Set COSMIC_ALLOW_FALLBACK_AUDIO=1 to override.');
    }
    const record = appendProductionRecord({
      topicId: topic.id,
      source: topic.source || 'queue',
      title: topic.title_ar,
      producedAt: new Date().toISOString(),
      filePath: repoRel(out.filePath),
      sizeBytes: out.sizeBytes || null,
      durationSeconds: info.duration || null,
      width: info.width || null,
      height: info.height || null,
      vcodec: info.vcodec || null,
      acodec: info.acodec || null,
      audioSources,
      coverPath: out.coverPath ? repoRel(out.coverPath) : null,
      published: false,
      youtubeVideoId: null,
      youtubeUrl: null
    });

    const audio = (record.audioSources || []).join('+') || 'unknown';
    autoPilotState.totalProduced += 1;
    autoPilotState.lastArtifact = record;
    emitEvent('cycle:produce-done', {
      topicId: record.topicId, title: record.title,
      filePath: record.filePath, durationSeconds: record.durationSeconds,
      width: record.width, height: record.height,
      audioSources: record.audioSources, published: false,
    });
    addAutoPilotLog(
      `🎬 إنتاج من الرادار: «${record.title}» → ${record.filePath} ` +
      `(${record.durationSeconds ?? '?'}s, ${record.width}x${record.height}, ${record.sizeBytes} بايت, صوت: ${audio}). لم يُنشر بعد.`
    );
    return record;
  } catch (err) {
    emitEvent('cycle:error', { stage: 'produce', error: err.message });
    addAutoPilotLog(`❌ ${err.message}`);
    throw err;
  } finally {
    cycleActive = false;
  }
}

export async function runAutoPilotCycle() {
  if (cycleActive) throw new Error('A publishing cycle is already running');
  cycleActive = true;
  autoPilotState.lastRun = new Date().toISOString();
  try {
    const cap = dailyUploadCap();
    const usedToday = uploadsInCurrentQuotaDay(loadSavedVideos(), loadProductionLog());
    if (usedToday >= cap) {
      const message = `⏸️ سقف الحصة اليومية ليوتيوب وصل (${usedToday}/${cap} رفعة) — `
        + 'بنحترم الحصة ونستنى تجديدها (منتصف الليل بتوقيت المحيط الهادئ) '
        + 'وبعدها الدورة الساعية بتكمّل لوحدها. مفيش فشل ومفيش رفع مهدور.';
      addAutoPilotLog(message);
      console.log(message);
      return { skipped: true, reason: 'daily_upload_cap', usedToday, cap };
    }

    const { client, isOAuth } = getYouTubeClient();
    if (!isOAuth || !client) throw new Error('YouTube OAuth is missing. Configure client ID, client secret and refresh token.');
    const channels = await client.channels.list({ part: ['snippet'], mine: true });
    if (!channels.data.items?.length) throw new Error('No YouTube channel found for this authorization');
    addAutoPilotLog(`القناة المتصلة: ${channels.data.items[0].snippet.title}`);

    // طابور المصنع نفسه يضع catalog=eye أولًا ثم الكتالوجات المؤلفة.
    const topic = pickNextProductionTopic();
    if (!topic) throw new Error('Topic queue exhausted. Add new original topics before publishing again.');
    autoPilotState.currentPublishingTitle = topic.title_ar;

    const status = await renderTopic(topic);
    const out = status.outputVideo;
    const audioSources = out.audioSources || [];
    if (out.report?.validate?.ok !== true) {
      throw new Error('فحص الجودة الإلزامي فشل؛ يُمنع النشر.');
    }
    if (audioSources.length && audioSources.every(s => s === 'fallback') && process.env.COSMIC_ALLOW_FALLBACK_AUDIO !== '1') {
      throw new Error('Narration fell back to a synthetic tone (TTS unavailable). Refusing to publish it; set COSMIC_ALLOW_FALLBACK_AUDIO=1 to override.');
    }

    const result = await publishVideo({
      videoFilePath: out.filePath,
      thumbnailFilePath: out.coverPath || null,
      title: topic.title_ar,
      description: [
        '🔥 ' + topic.hook_ar,
        ...(topic.facts_ar || []).map(x => '✨ ' + x),
        topic.outro_ar,
        '💬 اشترك وقل لنا رأيك وشارك الفيديو مع أصحابك!',
        ...(out.report?.credits || []),
        '#دوشة #Shorts #اكسبلور #فيرال #ترند'
      ].filter(Boolean).join('\n\n'),
      tags: [...new Set([...(topic.tags || '').split(','), 'دوشة', 'Shorts', 'اكسبلور', 'فيرال', 'ترند'].map(x => x.trim()).filter(Boolean))],
      privacyStatus: 'public', categoryId: '28', isShort: true
    });
    if (!result.video?.liveUploaded) throw new Error('Live upload was not confirmed');
    if (!result.video?.verified) throw new Error(`Upload was not verified on YouTube: ${result.video?.verifyError || 'unknown reason'}`);

    appendProductionRecord({
      topicId: topic.id,
      source: 'authored',
      title: result.video.title,
      producedAt: new Date().toISOString(),
      filePath: repoRel(out.filePath),
      sizeBytes: out.sizeBytes || null,
      durationSeconds: out.report?.validate?.info?.duration || null,
      width: out.report?.validate?.info?.width || null,
      height: out.report?.validate?.info?.height || null,
      vcodec: out.report?.validate?.info?.vcodec || null,
      acodec: out.report?.validate?.info?.acodec || null,
      audioSources,
      coverPath: out.coverPath ? repoRel(out.coverPath) : null,
      published: true,
      youtubeVideoId: result.video.id,
      youtubeUrl: result.video.url,
      verifiedBy: result.video.verifiedBy,
      verifiedAt: result.video.verifiedAt
    });

    autoPilotState.totalAutoPublished += 1;
    autoPilotState.totalProduced += 1;
    autoPilotState.publishBlockedReason = null;
    emitEvent('publish:done', {
      videoId: result.video.id, url: result.video.url,
      title: result.video.title, verifiedBy: result.video.verifiedBy,
    });
    addAutoPilotLog(`✅ رابط الفيديو الحقيقي: ${result.video.url} (مُتحقَّق عبر ${result.video.verifiedBy})`);
    return result;
  } catch (err) {
    emitEvent('cycle:error', { stage: 'publish', error: err.message });
    addAutoPilotLog(`❌ ${err.message}`);
    throw err;
  } finally {
    cycleActive = false;
  }
}

// What the 30-minute scheduler actually runs: publish when the channel is linked,
// otherwise keep producing from the radar and say plainly that publishing is blocked.
export async function runScheduledCycle() {
  const { client, isOAuth } = getYouTubeClient();
  emitEvent('cycle:scheduled', { mode: (isOAuth && client) ? 'publish' : 'produce-only' });
  if (isOAuth && client) {
    try {
      return await runAutoPilotCycle();
    } catch (err) {
      autoPilotState.publishBlockedReason = err.message;
      throw err;
    }
  }
  autoPilotState.publishBlockedReason = 'YouTube OAuth is missing — production only, nothing published.';
  return await runProductionCycle();
}

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

export function startAutoPilot(intervalHours = 0.5, continuousTurbo = false, turboDelaySeconds = 20) {
  if (autoPilotInterval) clearInterval(autoPilotInterval);
  if (turboTimeout) clearTimeout(turboTimeout);

  autoPilotState.running = true;
  autoPilotState.continuousTurbo = Boolean(continuousTurbo);
  autoPilotState.turboDelaySeconds = Number(turboDelaySeconds) || 20;
  autoPilotState.intervalHours = Number(intervalHours) || 0.5;

  if (autoPilotState.continuousTurbo) {
    addAutoPilotLog(`🚀 تم تفعيل الوضع التوربيني المستمر (النشر المتواصل غير المنقطع: كل ما ينتهي فيديو يُنشر التالي فوراً بعد ${autoPilotState.turboDelaySeconds} ثانية).`);
    runScheduledCycle().catch(() => {});
  } else {
    const ms = autoPilotState.intervalHours * 60 * 60 * 1000;
    autoPilotState.nextRun = new Date(Date.now() + ms).toISOString();
    const intervalMins = Math.round(autoPilotState.intervalHours * 60);
    addAutoPilotLog(`⚡ تم تفعيل الطيار الآلي المستمر بنجاح (النشر التلقائي يعمل دورياً كل ${intervalMins} دقيقة 24/7).`);
    runScheduledCycle().catch(() => {});

    autoPilotInterval = setInterval(() => {
      runScheduledCycle().catch(() => {});
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
