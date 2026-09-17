// الجهاز العصبي للمنظومة — كل حدث في أي مكان (طيار، إنتاج، عين، نشر)
// بيتبث لحظيًا على WebSocket لكل المتصلين + بيتسجل في سجل دائم
// data/events.jsonl (قابل للتدقيق، محدود بآخر 500 حدث).
//
// القاعدة: التهيئة والتسجيل ما يقطعوش البرنامج أبدًا — أي فشل هنا
// بيتبلع بصمت (الأهم: الحدث نفسه، مش السجل).

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { EventEmitter } from 'node:events';
import { WebSocketServer } from 'ws';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const EVENTS_LOG = path.join(ROOT, 'data', 'events.jsonl');
const MAX_LOG_LINES = 500;

const bus = new EventEmitter();
bus.setMaxListeners(100);

function appendLog(evt) {
  try {
    fs.mkdirSync(path.dirname(EVENTS_LOG), { recursive: true });
    fs.appendFileSync(EVENTS_LOG, JSON.stringify(evt) + '\n');
    const lines = fs.readFileSync(EVENTS_LOG, 'utf8').split('\n').filter(Boolean);
    if (lines.length > MAX_LOG_LINES) {
      fs.writeFileSync(EVENTS_LOG, lines.slice(-MAX_LOG_LINES).join('\n') + '\n');
    }
  } catch { /* التسجيل اختيارًا — ما يقطعش الشغل */ }
}

export function readRecentEvents(n = 100) {
  try {
    const lines = fs.readFileSync(EVENTS_LOG, 'utf8')
      .split('\n').filter(Boolean).slice(-n);
    return lines.map(l => { try { return JSON.parse(l); } catch { return null; } })
      .filter(Boolean);
  } catch { return []; }
}

export function emitEvent(type, data = {}) {
  const evt = { type, at: new Date().toISOString(), data };
  appendLog(evt);
  bus.emit('event', evt);
  return evt;
}

export function attachWebSocket(server) {
  const wss = new WebSocketServer({ server, path: '/ws' });
  wss.on('connection', (socket) => {
    try {
      socket.send(JSON.stringify({ kind: 'hello', at: new Date().toISOString() }));
      // آخر 50 حدث فورًا — المتصل الجديد مش بيدفع يسيب لحد يفكك
      for (const evt of readRecentEvents(50)) {
        socket.send(JSON.stringify({ kind: 'event', event: evt }));
      }
    } catch { /* ما نقفلش الاتصال بسبب ترحيب فاشل */ }
  });
  bus.on('event', (evt) => {
    const payload = JSON.stringify({ kind: 'event', event: evt });
    for (const client of wss.clients) {
      if (client.readyState === 1) {
        try { client.send(payload); } catch { /* عميل مات — نسيبه */ }
      }
    }
  });
  return wss;
}
