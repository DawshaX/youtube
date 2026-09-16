import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { publishVideo, verifyYouTubeVideo } from '../server/youtubeService.js';
import { runAutoPilotCycle, pickNextProductionTopic, loadProductionLog } from '../server/autoPilot.js';
import { listProductionQueue } from '../server/videoFactoryBridge.js';

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
  assert.ok(queue.length > 0, 'expected radar and authored topics');
  const ids = queue.map(topic => topic.id);
  assert.equal(new Set(ids).size, ids.length, 'duplicate topic ids cannot be deduplicated');
  assert.ok(queue.every(topic => !String(topic.id).startsWith('infinite-')),
    'randomly generated infinite ideas must not drive production');
  assert.ok(queue.every(topic => ['authored', 'radar'].includes(topic.source)));
  const next = pickNextProductionTopic();
  assert.ok(next && queue.some(topic => topic.id === next.id));
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
