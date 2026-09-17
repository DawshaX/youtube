import { useEffect, useRef, useState } from 'react';

// البث المباشر للمصنع — كل حدث (عين، إنتاج، نشر، طيار) يوصل لحظيًا
// من /ws ويعرض في شريط حي. الإعادة من /api/events لو الـ socket انقطع.

const LABELS = {
  'server:started':      { icon: '🌌', text: 'المنصة اشتغلت' },
  'autopilot:started':   { icon: '🤖', text: 'الطيار الآلي اشتغل' },
  'cycle:scheduled':     { icon: '⏱️', text: d => d.mode === 'publish' ? 'دورة مجدولة (نشر)' : 'دورة مجدولة (إنتاج فقط)' },
  'cycle:produce-start': { icon: '🎬', text: d => `إنتاج: «${d.title || d.topicId || ''}»` },
  'cycle:produce-done':  { icon: '📦', text: d => `خلص فيديو حقيقي: «${d.title || ''}» ${d.durationSeconds ? `(${Math.round(d.durationSeconds)}ث)` : ''} — لم يُنشر` },
  'cycle:error':         { icon: '⚠️', text: d => `خطأ في ${d.stage === 'publish' ? 'النشر' : 'الإنتاج'}: ${d.error || ''}` },
  'produce:job-start':   { icon: '🛠️', text: d => `عملية إنتاج: «${d.title || d.topicId || ''}» (${d.source === 'eye' ? 'من العين' : 'من الكتالوج'})` },
  'produce:job-done':    { icon: '✅', text: d => `تم إنتاج: «${d.title || ''}»` },
  'produce:job-error':   { icon: '❌', text: d => `فشل إنتاج: ${d.error || d.topicId || ''}` },
  'eye:queue':           { icon: '👁️', text: d => `طابور العين: ${d.count} موضوع من مشاهدات حقيقية` },
  'publish:done':        { icon: '🚀', text: d => `تم النشر على يوتيوب: «${d.title || ''}»` },
};

function fmtTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch { return ''; }
}

function shortText(evt) {
  const def = LABELS[evt.type];
  if (!def) return evt.type;
  return typeof def.text === 'function' ? def.text(evt.data || {}) : def.text;
}

export default function LiveFeed() {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const [open, setOpen] = useState(true);
  const scrollRef = useRef(null);

  useEffect(() => {
    let ws = null;
    let timer = null;
    let closed = false;

    const addEvent = (evt) =>
      setEvents(prev => (prev[0]?.type === evt.type && prev[0]?.at === evt.at)
        ? prev
        : [evt, ...prev].slice(0, 100));

    const connect = () => {
      if (closed) return;
      try {
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        ws = new WebSocket(`${proto}://${window.location.host}/ws`);
        ws.onopen = () => setConnected(true);
        ws.onmessage = (m) => {
          try {
            const msg = JSON.parse(m.data);
            if (msg.kind === 'event') addEvent(msg.event);
          } catch { /* رسالة مش JSON — نتجاهلها */ }
        };
        ws.onclose = () => {
          setConnected(false);
          if (!closed) timer = setTimeout(connect, 2000);
        };
        ws.onerror = () => { try { ws.close(); } catch { /* ignore */ } };
      } catch {
        timer = setTimeout(connect, 3000);
      }
    };

    // بذرة من السجل (آخر 50) — اللوحة تبان حتى قبل أول حدث حي
    fetch('/api/events')
      .then(r => r.json())
      .then(list => { if (Array.isArray(list) && list.length) setEvents(list.slice().reverse()); })
      .catch(() => { /* بلا سجل بعد — طبيعي */ });

    connect();
    return () => {
      closed = true;
      if (timer) clearTimeout(timer);
      if (ws) { try { ws.close(); } catch { /* ignore */ } }
    };
  }, []);

  return (
    <div dir="rtl" className="fixed bottom-4 left-4 z-40 w-80 max-w-[85vw] font-sans">
      <div className="rounded-xl border border-white/15 bg-[#0b0f1e]/95 backdrop-blur shadow-2xl shadow-black/60 overflow-hidden">
        <button
          onClick={() => setOpen(o => !o)}
          className="w-full flex items-center justify-between px-3 py-2 bg-white/5 hover:bg-white/10 cursor-pointer"
        >
          <span className="flex items-center gap-2 text-sm font-bold text-white">
            <span className="relative flex h-2.5 w-2.5">
              {connected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${connected ? 'bg-emerald-400' : 'bg-rose-500'}`} />
            </span>
            بث المصنع المباشر
            <span className="text-xs text-white/50 font-normal">{events.length} حدث</span>
          </span>
          <span className="text-white/60 text-xs">{open ? '▼' : '▲'}</span>
        </button>
        {open && (
          <div ref={scrollRef} className="max-h-56 overflow-y-auto divide-y divide-white/5">
            {events.length === 0 && (
              <div className="px-3 py-4 text-xs text-white/40 text-center">
                مفيش أحداث لسه — أول دورة هتظهر هنا لحظيًا…
              </div>
            )}
            {events.map((evt, i) => {
              const def = LABELS[evt.type] || { icon: '•' };
              return (
                <div key={`${evt.at}-${i}`} className="px-3 py-2 flex items-start gap-2 text-xs"
                     title={`${evt.type} — ${evt.at}`}>
                  <span className="text-sm leading-4">{def.icon}</span>
                  <div className="min-w-0">
                    <div className="text-white/90 break-words leading-5">{shortText(evt)}</div>
                    <div className="text-white/35 mt-0.5 tabular-nums">{fmtTime(evt.at)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
