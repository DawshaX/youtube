/**
 * مصنع دۅۄشے — سيرفر الحالة (قراءة فقط).
 *
 * ⛔ المصنع القديم (autoPilot / youtubeService / viralEngine / طابور الـ509 موضوع)
 * اتشال بالكامل في 2026-09-19 بأمر صاحب القناة. النشر والإنتاج بيحصلوا في
 * GitHub Actions فقط (factory-publish.yml → scripts/factory_loop.py) — يعني
 * مفيش أي مسار يقدر ينشر من هنا، ومفيش مصنع تاني يشتغل في الخفاء.
 *
 * اللي بيفضل: نافذة واحدة تقرأ حالة المصنع الحقيقية من الملفات اللي
 * بيتكتبها في كل دورة (data/*.json + state/*.json) وتعرضها زي ما هي.
 */
import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { attachBus, emitEvent } from './bus.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');

const app = express();
app.use(express.json());

const READ = (rel, fallback) => {
  try {
    return JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
  } catch {
    return fallback;
  }
};

/** حالة المصنع الكاملة — كل رقم هنا من ملف حقيقي، مفيش تقديرات. */
function factoryState() {
  const status = READ('data/factory_status.json', {});
  const cycle = READ('state/last_cycle.json', {});
  const health = READ('data/health.json', {});
  const published = READ('state/published.json', []);
  const produced = READ('state/produced.json', {}).episodes || {};
  const queue = READ('data/eye_topics.json', []);
  const consumed = READ('data/eye_consumed.json', []);
  const media = READ('state/media_used.json', {});
  const pending = READ('state/yt_pending.json', []);

  const now = Date.now() / 1000;
  const last24 = Array.isArray(published)
    ? published.filter((x) => now - Number(x.ts || 0) < 86400).length : 0;

  return {
    brand: 'دۅۄشے',
    engine: 'XTreNDAW — المصنع الجديد (Python)',
    cycles: status.cycles || 0,
    lastCycleAt: status.last_cycle_at || cycle.at || null,
    lastCycle: {
      publishedThisCycle: cycle.published_this_cycle,
      episodesInMemory: cycle.episodes_in_memory,
      tail: (cycle.last_lines || '').slice(-800),
    },
    published: Array.isArray(published) ? published.slice(-15).reverse() : [],
    publishedLast24h: last24,
    pendingUploads: Array.isArray(pending) ? pending.length : 0,
    episodesProduced: Object.keys(produced).length,
    eyeQueue: Array.isArray(queue) ? queue.map((t) => ({
      id: t.id, title: t.title_ar, source: t._eye?.videoId,
      sourceViews: t._eye?.sourceViews, shots: (t.shots || []).length,
      replication: !!t._replication })) : [],
    eyeConsumed: Array.isArray(consumed) ? consumed.length : 0,
    mediaMemory: Object.keys(media || {}).length,
    health: {
      allOk: health.all_ok ?? null,
      fails: health.fails ?? null,
      warns: health.warns ?? null,
      checks: (health.checks || []).map((c) => ({
        name: c.name, status: c.status, detail: c.detail })),
    },
  };
}

app.get('/api/factory/status', (_req, res) => res.json(factoryState()));

/** آخر حلقة اتولدت: اللقطات + الاستعلامات — تشوف بعينك إنها تقليد مش كلام. */
app.get('/api/factory/last-episode', (_req, res) => {
  const produced = READ('state/produced.json', {}).episodes || {};
  const ids = Object.keys(produced);
  const last = ids.length ? produced[ids[ids.length - 1]] : null;
  res.json({ episode: last || null });
});

/** سجل النشر الكامل (كل رفعة على يوتيوب — للتتبع والمراجعة). */
app.get('/api/factory/published', (_req, res) => {
  const published = READ('state/published.json', []);
  res.json({ count: published.length, items: published });
});

app.get('/api/health', (_req, res) => res.json(READ('data/health.json', {})));

// NUI: لوحة البث الحي (بتقرأ نفس الأحداث من السيرفر)
app.get('/api/events', (_req, res) => {
  res.set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache',
            Connection: 'keep-alive' });
  res.flushHeaders?.();
  emitEvent('status', factoryState());
  const ping = setInterval(() => res.write(': ping\n\n'), 20000);
  _req.on('close', () => clearInterval(ping));
});

const PORT = process.env.PORT || 3001;
attachBus(app);
app.listen(PORT, '0.0.0.0', () => {
  console.log(`[مصنع دۅۄشے] سيرفر الحالة على http://0.0.0.0:${PORT}`);
  console.log('[مصنع دۅۄشے] قراءة فقط — النشر من GitHub Actions فقط.');
});
