// Produce one real episode from the radar queue and stop before publishing.
// Usage:
//   node scripts/produce-from-radar.js          -> render the next queued topic
//   node scripts/produce-from-radar.js --list   -> show the queue and what is done
//
// This is the production half of the 30-minute autopilot cycle. It renders an
// actual MP4 with the Python 2099 engine and records the artifact facts in
// data/production_log.json. It never writes a YouTube link, because nothing was
// uploaded.

import { runProductionCycle, pickNextProductionTopic, loadProductionLog } from '../server/autoPilot.js';
import { listProductionQueue } from '../server/videoFactoryBridge.js';

if (process.argv[2] === '--list') {
  const produced = loadProductionLog();
  for (const topic of listProductionQueue()) {
    const done = produced.some(p => p.topicId === topic.id);
    console.log(`${done ? '[produced]' : '[pending] '} ${topic.source.padEnd(8)} ${String(topic.id).padEnd(18)} ${topic.title_ar}`);
  }
  process.exit(0);
}

const next = pickNextProductionTopic();
if (!next) {
  console.error('Topic queue exhausted — every radar/authored topic has been produced. Add new topics to content/topics.json.');
  process.exit(1);
}
console.log(`Next in queue: [${next.source}] ${next.id} — ${next.title_ar}`);

try {
  const record = await runProductionCycle();
  console.log(JSON.stringify(record, null, 2));
  const audio = (record.audioSources || []).join('+') || 'unknown';
  if (audio === 'fallback') {
    console.warn('WARNING: narration used the offline tone fallback (TTS service unreachable). This artifact is not publishable quality.');
  } else {
    console.log(`Narration source: ${audio}`);
  }
} catch (error) {
  console.error(`Production failed: ${error.message}`);
  process.exitCode = 1;
}
