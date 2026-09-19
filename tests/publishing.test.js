import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { publishVideo, verifyYouTubeVideo } from '../server/youtubeService.js';
import { runAutoPilotCycle, pickNextProductionTopic, loadProductionLog, pruneProductionLog,
         uploadsInCurrentQuotaDay, dailyUploadCap, quotaDayKey } from '../server/autoPilot.js';
import { listProductionQueue, listAvailableTopics } from '../server/videoFactoryBridge.js';
import { summarizeVerification } from '../server/uploadVerification.js';

// الاختبارات بتشغّل منطق الطابور الحقيقي (وبيعمل prune للوج) — عشان كده بنأمن
// نسخة من `data/production_log.json` قبل أي اختبار وبنرجعها بعد ما يخلصوا،
// عشان ما يمسحش شغل حقيقي من غير قصد لمجرد إن الاختبارات اتشغلت.
const LOG_PATH = path.resolve('data/production_log.json');
const LOG_BACKUP = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'prodlog-')), 'production_log.json');
test.before(() => {
  if (fs.existsSync(LOG_PATH)) fs.copyFileSync(LOG_PATH, LOG_BACKUP);
});
test.after(() => {
  if (fs.existsSync(LOG_BACKUP)) {
    fs.copyFileSync(LOG_BACKUP, LOG_PATH);
    fs.rmSync(path.dirname(LOG_BACKUP), { recursive: true, force: true });
  }
});

test('missing OAuth cannot create fake video records', async () => {
  assert.equal(fs.existsSync('data/config.json'), false, 'Run in an unconfigured checkout');
  const before = fs.readFileSync('data/saved_videos.json', 'utf8');
  await assert.rejects(publishVideo({ title: 'test' }), /OAuth/);
  assert.equal(fs.readFileSync('data/saved_videos.json', 'utf8'), before);
});
test('autopilot propagates missing authorization and releases cycle lock', async () => {
  await assert.rejects(runAutoPilotCycle(), /OAuth is missing/);
  await assert.rejects(runAutoPilotCycle(), /OAuth is missing/);
});
test('stored upload history carries no fabricated links', () => {
  const videos = JSON.parse(fs.readFileSync('data/saved_videos.json', 'utf8'));
  assert.ok(Array.isArray(videos), 'saved_videos.json must stay a list');
  for (const video of videos) {
    assert.equal(video.liveUploaded, true, `${video.id} is recorded without a confirmed upload`);
    assert.match(String(video.id), /^[A-Za-z0-9_-]{11}$/, `${video.id} is not a YouTube video id`);
    assert.equal(video.url, `https://youtu.be/${video.id}`);
  }
});
test('a fabricated cosmic_ id is never reported as verified', async () => {
  const result = await verifyYouTubeVideo('cosmic_1y3flilxj');
  assert.equal(result.verified, false);
  assert.equal(result.method, 'format');
});
test('the production queue is finite and deduplicated by stable ids', () => {
  const queue = listProductionQueue();
  assert.ok(queue.length > 0, 'expected catalog topics with authored scripts');
  const ids = queue.map(topic => topic.id);
  assert.equal(new Set(ids).size, ids.length, 'duplicate topic ids cannot be deduplicated');
  assert.ok(queue.every(topic => !String(topic.id).startsWith('infinite-')),
    'randomly generated infinite ideas must not drive production');
  // المصادر المسموحة: كتالوج «دۅۄشے»، السكربتات المكتوبة، ومواضيع العين
  // (العين بتكتب إصدارنا من فيديو ترند حقيقي) — والرادار كذلك.
  // الدرس (2026-09-19): أول موضوع للعين دخّل الطابور، والاختبار كان حاطط
  // مصدرين بس فوقع — الفلتر لازم يشمل كل مصدر شرعي، مش يتجاهله.
  assert.ok(queue.every(topic => ['authored', 'daousha', 'eye', 'radar'].includes(topic.source)),
    'مصدر غير معروف في الطابور: ' + JSON.stringify([...new Set(queue.map(t => t.source))]));
  const next = pickNextProductionTopic();
  assert.ok(next && queue.some(topic => topic.id === next.id));
});
test('pruning the log never makes the queue re-produce a live entry', () => {
  const first = pickNextProductionTopic();
  assert.ok(first, 'queue must still have a next topic after pruning');
  const again = pickNextProductionTopic();
  assert.equal(again.id, first.id,
    'two consecutive reads must pick the same topic — pruning must not reshuffle');
  const kept = loadProductionLog();
  for (const entry of kept) {
    if (entry.published) {
      assert.ok(entry.youtubeVideoId, 'a kept published entry keeps its proven record');
    } else {
      assert.ok(fs.existsSync(path.resolve(entry.filePath)),
        `a kept entry still points at a missing artifact: ${entry.filePath}`);
    }
  }
});
test('every queue topic carries its own authored script — no shared filler', () => {
  const queue = listProductionQueue();
  const fillers = [
    'في الدقيقة الأولى: تصعيد التحدي',
    'المرحلة الأولى: اختبار القواعد المستحيلة'
  ];
  for (const topic of queue) {
    assert.ok((topic.hook_ar || '').length > 10, `${topic.id} is missing a hook`);
    assert.ok(Array.isArray(topic.facts_ar) && topic.facts_ar.length >= 1,
      `${topic.id} is missing facts`);
    for (const fact of topic.facts_ar) {
      assert.ok(!fillers.some(f => fact.startsWith(f)),
        `${topic.id} still carries the duplicated boilerplate facts`);
    }
  }
});
test('the 509-topic daousha catalog is wired into the factory', () => {
  const raw = JSON.parse(fs.readFileSync('content/topics_daousha.json', 'utf-8'));
  assert.equal(raw.length, 509, 'the daousha catalog must keep its 509 topics');
  const available = listAvailableTopics();
  const ids = new Set(available.map(topic => topic.id));
  for (const entry of raw) {
    assert.ok(ids.has(entry.id), `daousha topic ${entry.id} is not reachable from the factory`);
  }
});
test('the production log only claims artifacts that exist on disk', () => {
  // The log is pruned exactly the way the queue reads it: a workspace reset
  // removes gitignored MP4s but not the log, so dead UNPUBLISHED entries drop
  // out first — published entries are historical record and stay forever.
  pruneProductionLog();
  for (const entry of loadProductionLog()) {
    assert.ok(entry.filePath, 'every entry needs a real artifact path');
    if (entry.published) {
      assert.match(String(entry.youtubeVideoId), /^[A-Za-z0-9_-]{11}$/);
      assert.equal(entry.youtubeUrl, `https://youtu.be/${entry.youtubeVideoId}`);
      assert.ok(entry.verifiedBy, 'a published entry must be verified');
    } else {
      assert.ok(fs.existsSync(path.resolve(entry.filePath)), `missing artifact: ${entry.filePath}`);
      assert.ok(entry.sizeBytes > 0, `empty artifact: ${entry.filePath}`);
      assert.ok(entry.audioSources.length > 0, 'audio source must be recorded');
      assert.equal(entry.youtubeUrl, null, 'an unpublished render must not carry a YouTube link');
      assert.equal(entry.youtubeVideoId, null);
    }
  }
});


test('verification: a recorded upload removed long ago is stale, not a run failure', async () => {
  const now = Date.parse('2026-09-19T03:00:00Z');
  const records = [
    { id: 'fresh', publishedAt: '2026-09-19T02:48:00Z' },
    { id: 'ancient', publishedAt: '2026-09-10T02:00:00Z' },
  ];
  const results = [
    { verified: true, url: 'https://youtu.be/fresh' },
    { verified: false, url: 'https://youtu.be/ancient', reason: 'no video' },
  ];
  const summary = summarizeVerification(records, results, { now, strictHours: 24 });
  assert.equal(summary.exitCode, 0, 'سجل قديم مُزال ما لازمش يفشّل دورة النشر');
  assert.equal(summary.stale.length, 1);
  assert.equal(summary.failures.length, 0);

  const bad = summarizeVerification(records, [
    { verified: false, url: 'https://youtu.be/fresh', reason: 'no video' },
    { verified: false, url: 'https://youtu.be/ancient', reason: 'no video' },
  ], { now, strictHours: 24 });
  assert.equal(bad.exitCode, 1, 'منشور جديد مش متأكد = فشل حقيقي');
  assert.equal(bad.failures.length, 1);
});


test('daily quota cap: counting uploads uses the YouTube (Pacific) day, not UTC', () => {
  // 2026-09-19 05:00 UTC = 2026-09-18 22:00 في كاليفورنيا → يوم حصة مختلف
  assert.equal(quotaDayKey('2026-09-19T05:00:00Z'), '2026-09-18');
  assert.equal(quotaDayKey('2026-09-19T08:00:00Z'), '2026-09-19');
  const now = new Date('2026-09-19T09:00:00Z');
  const records = [
    { id: 'a', publishedAt: '2026-09-19T08:10:00Z' },
    { id: 'b', publishedAt: '2026-09-19T08:20:00Z' },
    { id: 'old', publishedAt: '2026-09-18T22:00:00Z' }, // يوم الحصة السابق
  ];
  assert.equal(uploadsInCurrentQuotaDay(records, [], now), 2);
  assert.equal(uploadsInCurrentQuotaDay([], [{ topicId: 't1', producedAt: '2026-09-19T08:30:00Z' }], now), 1);
  // نفس الرفعة موجودة في القايمتين بمعرّفين → تتحسب مرة واحدة (بلاش تفعيل مبكر للسقف)
  assert.equal(uploadsInCurrentQuotaDay(
    [{ id: 'vid', publishedAt: '2026-09-19T08:10:00Z' }],
    [{ topicId: 'eye-abc', producedAt: '2026-09-19T08:10:05Z' }], now), 1);
  // إنتاج لم يُنشر مايتحسبش في الحصة
  assert.equal(uploadsInCurrentQuotaDay([], [
    { topicId: 't2', producedAt: '2026-09-19T08:40:00Z', published: false }], now), 0);
});

test('daily quota cap: default is the YouTube upload quota ceiling and is overridable', () => {
  const previous = process.env.XT_MAX_UPLOADS_PER_DAY;
  delete process.env.XT_MAX_UPLOADS_PER_DAY;
  assert.equal(dailyUploadCap(), 6, 'الحصة الافتراضية = 10000/1600 = 6 رفعات');
  process.env.XT_MAX_UPLOADS_PER_DAY = '3';
  assert.equal(dailyUploadCap(), 3);
  if (previous === undefined) delete process.env.XT_MAX_UPLOADS_PER_DAY;
  else process.env.XT_MAX_UPLOADS_PER_DAY = previous;
});
