// لوحة حالة مصنع دۅۄشے — قراءة فقط من /api/factory/status
// (المصنع القديم اتشال؛ الإنتاج والنشر في GitHub Actions فقط)
import { useEffect, useState } from 'react';

const Badge = ({ ok, children }) => (
  <span style={{
    background: ok ? '#0f5132' : '#5c1d24', color: ok ? '#8ef0b4' : '#ffb3bd',
    borderRadius: 999, padding: '2px 10px', fontSize: 12, marginInline: 4,
  }}>{children}</span>
);

export default function App() {
  const [s, setS] = useState(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch('/api/factory/status');
        setS(await r.json());
      } catch (e) { setErr(String(e)); }
    };
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  if (err) return <div style={S.wrap}>الواجهة مش لاقية سيرفر الحالة ({err})</div>;
  if (!s) return <div style={S.wrap}>بنجيب حالة المصنع…</div>;

  return (
    <div style={S.wrap}>
      <h1 style={S.h1}>🏭 {s.brand} — لوحة المصنع</h1>
      <p style={S.sub}>{s.engine}</p>

      <div style={S.grid}>
        <Card title="الدورات" value={s.cycles} sub={s.lastCycleAt} />
        <Card title="حلقات اتعملت" value={s.episodesProduced} />
        <Card title="منشور آخر 24س" value={s.publishedLast24h}
              sub={`في الطابور: ${s.pendingUploads}`} />
        <Card title="ذاكرة الوسائط" value={s.mediaMemory} sub="لقطة مستخدمة" />
        <Card title="طابور العين" value={s.eyeQueue.length}
              sub={`اتنفذ: ${s.eyeConsumed}`} />
        <Card title="صحة الخدمات"
              value={s.health.allOk ? 'سليمة' : `فشل ${s.health.fails ?? '?'}`}
              sub={`تنبيهات: ${s.health.warns ?? '?'}`} />
      </div>

      <h2 style={S.h2}>🎬 طابور العين (تقليد فيديو ترند لحظة-بلحظة)</h2>
      {s.eyeQueue.length === 0
        ? <p style={S.sub}>الطابور فاضي — الرادار بيملاه كل 6 ساعات.</p>
        : s.eyeQueue.map((t) => (
          <div key={t.id} style={S.row}>
            <b>{t.title || t.id}</b>
            <div style={S.sub}>
              {t.shots ? `${t.shots} لقطة` : 'بدون لقطات'} ·
              المصدر: {t.source || '—'} · مشاهدات: {t.sourceViews || '—'}
              {t.replication ? <Badge ok>تقليد حرفي</Badge> : null}
            </div>
          </div>
        ))}

      <h2 style={S.h2}>📺 آخر المنشور</h2>
      {s.published.map((p) => (
        <div key={p.id} style={S.row}>
          <a style={S.a} href={`https://youtu.be/${p.id}`} target="_blank"
             rel="noreferrer">{p.title}</a>
          <div style={S.sub}>{p.id} · {new Date((p.ts || 0) * 1000).toLocaleString('ar-EG')}</div>
        </div>
      ))}

      <h2 style={S.h2}>🩺 فحص الخدمات</h2>
      <div>{s.health.checks.map((c, i) => (
        <div key={i} style={S.sub}>
          <Badge ok={c.status === 'ok'}>{c.status}</Badge>
          {c.name} — {String(c.detail || '').slice(0, 90)}
        </div>
      ))}</div>

      <details style={{ marginTop: 24 }}>
        <summary style={S.sub}>آخر سطور لوج الدورة</summary>
        <pre style={S.pre}>{s.lastCycle.tail}</pre>
      </details>
    </div>
  );
}

const Card = ({ title, value, sub }) => (
  <div style={S.card}>
    <div style={S.sub}>{title}</div>
    <div style={S.value}>{value}</div>
    {sub ? <div style={S.sub}>{sub}</div> : null}
  </div>
);

const S = {
  wrap: { background: '#0b0b12', color: '#eaeaf2', minHeight: '100vh',
          padding: 24, fontFamily: 'system-ui, sans-serif', direction: 'rtl' },
  h1: { fontSize: 26, margin: '0 0 4px' },
  h2: { fontSize: 18, marginTop: 28, borderBottom: '1px solid #23233a',
        paddingBottom: 6 },
  sub: { color: '#9a9ab4', fontSize: 13, margin: '4px 0' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(180px,1fr))',
          gap: 12, marginTop: 16 },
  card: { background: '#141424', border: '1px solid #23233a', borderRadius: 12,
          padding: 14 },
  value: { fontSize: 24, fontWeight: 700, margin: '4px 0' },
  row: { padding: '10px 0', borderBottom: '1px solid #1b1b2c' },
  a: { color: '#8ab4ff', textDecoration: 'none' },
  pre: { background: '#0f0f1c', padding: 12, borderRadius: 8, fontSize: 11,
         overflowX: 'auto', whiteSpace: 'pre-wrap', maxHeight: 320 },
};
