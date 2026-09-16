import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { publishVideo, verifyYouTubeVideo } from '../server/youtubeService.js';
import { runAutoPilotCycle, pickNextProductionTopic, loadProductionLog } from '../server/autoPilot.js';
import { listProductionQueue, listAvailableTopics } from '../server/videoFactoryBridge.js';

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
  assert.ok(queue.every(topic => ['authored', 'daousha'].includes(topic.source)));
  const next = pickNextProductionTopic();
  assert.ok(next && queue.some(topic => topic.id === next.id));
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
  for (const entry of loadProductionLog()) {
    assert.ok(entry.filePath, 'every entry needs a real artifact path');
    assert.ok(fs.existsSync(path.resolve(entry.filePath)), `missing artifact: ${entry.filePath}`);
    assert.ok(entry.sizeBytes > 0, `empty artifact: ${entry.filePath}`);
    assert.ok(entry.audioSources.length > 0, 'audio source must be recorded');
    if (entry.published) {
      assert.match(String(entry.youtubeVideoId), /^[A-Za-z0-9_-]{11}$/);
      assert.equal(entry.youtubeUrl, `https://youtu.be/${entry.youtubeVideoId}`);
      assert.ok(entry.verifiedBy, 'a published entry must be verified');
    } else {
      assert.equal(entry.youtubeUrl, null, 'an unpublished render must not carry a YouTube link');
      assert.equal(entry.youtubeVideoId, null);
    }
  }
});
