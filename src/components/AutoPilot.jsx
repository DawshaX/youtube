import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  Play, 
  Pause, 
  RefreshCw, 
  Terminal, 
  Clock, 
  CheckCircle2, 
  Zap, 
  Sparkles, 
  Layers, 
  Cpu, 
  Globe2, 
  Radio, 
  Workflow
} from 'lucide-react';

export default function AutoPilot({ isAr }) {
  const [status, setStatus] = useState({
    running: false,
    continuousTurbo: false,
    lastRun: null,
    nextRun: null,
    intervalHours: 6,
    turboDelaySeconds: 20,
    totalAutoPublished: 0,
    logs: []
  });
  const [loading, setLoading] = useState(false);
  const [selectedInterval, setSelectedInterval] = useState(6);
  const [enableTurbo, setEnableTurbo] = useState(false);
  const [turboDelay, setTurboDelay] = useState(20);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/autopilot');
      const data = await res.json();
      setStatus(data);
      if (data.intervalHours) setSelectedInterval(data.intervalHours);
      if (data.continuousTurbo !== undefined) setEnableTurbo(data.continuousTurbo);
      if (data.turboDelaySeconds) setTurboDelay(data.turboDelaySeconds);
    } catch (err) {
      console.error('Fetch autopilot status error:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleToggle = async () => {
    setLoading(true);
    try {
      const endpoint = status.running ? '/api/autopilot/stop' : '/api/autopilot/start';
      const body = status.running ? {} : { 
        intervalHours: selectedInterval,
        continuousTurbo: enableTurbo,
        turboDelaySeconds: turboDelay
      };
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (data.status) setStatus(data.status);
    } catch (err) {
      console.error('Toggle autopilot error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunNow = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/autopilot/run-now', { method: 'POST' });
      const data = await res.json();
      if (data.status) setStatus(data.status);
    } catch (err) {
      console.error('Run now error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-red-950/40 border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase mb-2">
              <Bot className="w-4 h-4 text-red-500 animate-pulse" />
              <span>{isAr ? 'الطيار الآلي الكوني المستمر (24/7 Autonomous Auto-Pilot)' : '24/7 Autonomous Bot'}</span>
            </div>
            <h2 className="text-xl sm:text-3xl font-black text-white">
              {isAr ? 'أتمتة كاملة للقناة بدون أي تدخل بشري' : 'Zero-Human-Intervention Channel Automation'}
            </h2>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl">
              {isAr 
                ? 'يقوم الروبوت بمسح ترندات يوتيوب تلقائياً، استخراج أفضل فكرة فيديو حققت أقصى مشاهدات، صياغة السيناريو وخطاف الـ 3 ثواني، ونشر الفيديو على قناتك تلقائياً وبشكل دوري ومستمر مجاناً.'
                : 'Scans top global trends, scripts viral hooks, generates SEO tags, and publishes autonomously on schedule.'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleRunNow}
              disabled={loading}
              className="px-4 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-slate-700 transition flex items-center gap-2 disabled:opacity-50"
            >
              <Zap className="w-4 h-4 text-amber-400" />
              <span>{isAr ? 'تشغيل دورة فورية الآن' : 'Run Cycle Now'}</span>
            </button>

            <button
              onClick={handleToggle}
              disabled={loading}
              className={`px-6 py-3 rounded-2xl font-black text-xs shadow-xl transition flex items-center gap-2 ${
                status.running
                  ? 'bg-red-600 hover:bg-red-700 text-white shadow-red-600/30'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/30'
              }`}
            >
              {status.running ? (
                <>
                  <Pause className="w-4 h-4" />
                  <span>{isAr ? 'إيقاف الطيار الآلي' : 'Pause Auto-Pilot'}</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>{isAr ? 'تفعيل الطيار الآلي 24/7' : 'Activate 24/7 Bot'}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Turbo Endless Stream Toggle Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-red-950/60 via-slate-900 to-purple-950/60 border-2 border-red-500/40 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-red-500/20 text-red-400 flex items-center justify-center font-black text-xl border border-red-500/40 shrink-0">
            ⚡
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm sm:text-base font-black text-white">
                {isAr ? 'الوضع التوربيني للنشر المستمر (Continuous Turbo Stream)' : 'Continuous Turbo Auto-Publisher'}
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse">
                {isAr ? 'متواصل بدون توقف' : 'Non-Stop'}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
              {isAr 
                ? 'كل ما ينتهي فيديو من النشر، يسحب الروبوت فكرة جديدة فوراً من مصفوفة الملايين وينشرها تلقائياً بدون انقطاع!' 
                : 'As soon as one video publishes, immediately generates the next viral idea & publishes non-stop!'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-bold">{isAr ? 'الفاصل الزمني:' : 'Delay:'}</span>
            <select
              value={turboDelay}
              onChange={(e) => setTurboDelay(Number(e.target.value))}
              disabled={status.running}
              className="bg-slate-950 text-white text-xs font-bold px-2.5 py-1.5 rounded-xl border border-slate-700 focus:outline-none focus:border-red-500"
            >
              <option value={10}>{isAr ? '10 ثوانٍ (سريع جداً)' : '10s (Ultra Fast)'}</option>
              <option value={20}>{isAr ? '20 ثانية (موصى به)' : '20s (Recommended)'}</option>
              <option value={60}>{isAr ? '1 دقيقة' : '1 Minute'}</option>
              <option value={300}>{isAr ? '5 دقائق' : '5 Minutes'}</option>
            </select>
          </div>

          <label className="flex items-center gap-2 cursor-pointer p-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-red-500/50 transition">
            <input
              type="checkbox"
              checked={enableTurbo}
              onChange={(e) => setEnableTurbo(e.target.checked)}
              disabled={status.running}
              className="w-4 h-4 rounded text-red-600 focus:ring-red-500 bg-slate-800 border-slate-700 cursor-pointer"
            />
            <span className="text-xs font-black text-white">{isAr ? 'تفعيل التوربيني' : 'Enable Turbo'}</span>
          </label>
        </div>
      </div>

      {/* Control Metrics & Config */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Status card */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold">{isAr ? 'حالة النظام' : 'Engine State'}</span>
            <span className={`w-2.5 h-2.5 rounded-full ${status.running ? 'bg-emerald-500 animate-ping' : 'bg-slate-600'}`}></span>
          </div>
          <div className="text-xl font-black text-white flex items-center gap-2">
            <span>{status.running ? (isAr ? 'يعمل ذاتياً 🚀' : 'Active 🚀') : (isAr ? 'متوقف مؤقتاً' : 'Paused')}</span>
          </div>
          <p className="text-[11px] text-slate-500">
            {status.running ? (isAr ? 'يراقب الترند وينشر دورياً' : 'Monitoring & Auto-Publishing') : (isAr ? 'اضغط تفعيل للبدء' : 'Click Activate to start')}
          </p>
        </div>

        {/* Total Published card */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <span className="text-xs text-slate-400 font-semibold block">{isAr ? 'الفيديوهات المنشورة ذاتياً' : 'Auto Published'}</span>
          <div className="text-xl font-black text-emerald-400">
            {status.totalAutoPublished} {isAr ? 'فيديو' : 'Videos'}
          </div>
          <p className="text-[11px] text-slate-500">
            {isAr ? 'بدون أي تدخل بشري' : 'Zero manual effort'}
          </p>
        </div>

        {/* Schedule interval */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <span className="text-xs text-slate-400 font-semibold block">{isAr ? 'تكرار النشر التلقائي' : 'Auto Interval'}</span>
          <select
            value={selectedInterval}
            onChange={(e) => setSelectedInterval(Number(e.target.value))}
            className="w-full bg-slate-950 text-white text-xs font-bold p-2 rounded-xl border border-slate-700 focus:outline-none focus:border-red-500"
          >
            <option value={1}>{isAr ? 'كل ساعة (للقنوات الكبرى)' : 'Every 1 Hour'}</option>
            <option value={3}>{isAr ? 'كل 3 ساعات' : 'Every 3 Hours'}</option>
            <option value={6}>{isAr ? 'كل 6 ساعات (موصى به)' : 'Every 6 Hours (Recommended)'}</option>
            <option value={12}>{isAr ? 'كل 12 ساعة (فيديوهين يومياً)' : 'Every 12 Hours'}</option>
            <option value={24}>{isAr ? 'كل 24 ساعة (فيديو يومياً)' : 'Every 24 Hours'}</option>
          </select>
        </div>

        {/* Next Run card */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <span className="text-xs text-slate-400 font-semibold block">{isAr ? 'الدورة القادمة' : 'Next Auto Run'}</span>
          <div className="text-sm font-black text-amber-300 font-mono">
            {status.nextRun ? new Date(status.nextRun).toLocaleTimeString() : (isAr ? 'غير مجدولة' : 'N/A')}
          </div>
          <p className="text-[11px] text-slate-500">
            {isAr ? 'الجدولة التلقائية المستمرة' : 'Continuous loop'}
          </p>
        </div>

      </div>

      {/* Live Terminal & Logs */}
      <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-black text-white font-mono">
              {isAr ? 'سجل العمليات الحية للروبوت (Live AutoPilot Terminal)' : 'AutoPilot Live Console'}
            </h3>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>LIVE STREAM</span>
          </div>
        </div>

        <div className="bg-slate-900/90 rounded-xl p-4 font-mono text-xs text-slate-300 space-y-2 max-h-72 overflow-y-auto">
          {status.logs && status.logs.length > 0 ? (
            status.logs.map((log, idx) => (
              <div key={idx} className="leading-relaxed border-b border-slate-800/40 pb-1 text-slate-300">
                {log}
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-center py-6">
              {isAr ? 'اضغط "تفعيل الطيار الآلي" أو "تشغيل دورة فورية" لبدء الأتمتة...' : 'Waiting for auto-pilot cycle...'}
            </div>
          )}
        </div>
      </div>

      {/* Free Cloud Execution (GitHub Actions) Info */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center gap-2">
          <Workflow className="w-5 h-5 text-purple-400" />
          <h3 className="text-base font-black text-white">
            {isAr ? 'الأتمتة السحابية المجانية عبر GitHub Actions' : 'Free Cloud Scheduling via GitHub Actions'}
          </h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          {isAr 
            ? 'تم إضافة ملف سير عمل (GitHub Actions Workflow) داخل المستودع `.github/workflows/cosmic-autopilot.yml` ليعمل في السحابة مجاناً على مدار الساعة بدون الحاجة لإبقاء حاسوبك مفتوحاً!'
            : 'Pre-configured GitHub Actions workflow runs continuously on GitHub cloud servers for 24/7 operation.'}
        </p>
      </div>

    </div>
  );
}
