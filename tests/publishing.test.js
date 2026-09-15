import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { publishVideo } from '../server/youtubeService.js';
import { runAutoPilotCycle } from '../server/autoPilot.js';

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
