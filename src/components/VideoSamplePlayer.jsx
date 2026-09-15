import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  VolumeX, 
  Send, 
  Sparkles, 
  Flame, 
  Clock, 
  Maximize2, 
  Layers, 
  CheckCircle2, 
  Smartphone, 
  Monitor,
  Share2
} from 'lucide-react';

export default function VideoSamplePlayer({ onPublishSample, isAr }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(15);
  const [isMuted, setIsMuted] = useState(false);
  const [aspectRatio, setAspectRatio] = useState('16:9'); // '16:9' | '9:16'
  const [selectedSampleIndex, setSelectedSampleIndex] = useState(0);
  const [publishing, setPublishing] = useState(false);
  const [publishMessage, setPublishMessage] = useState('');

  const samples = [
    {
      id: 'sample-1',
      title: 'حبست 100 شخص في أغرب غرفة تحت الأرض.. الرابح يأخذ 500,000$!',
      titleEn: 'I Trapped 100 People in an Underground Cube - Last to Leave Wins $500,000!',
      category: 'challenges',
      viewsEst: '48.5M',
      ctr: '17.8%',
      themeColor: '#ef4444',
      bgGradient: 'from-red-950 via-slate-950 to-slate-900',
      hookTextAr: 'في هذه اللحظة، 100 شخص داخل هذه الغرفة.. والرابح يأخذ نصف مليون دولار نقداً!',
      hookTextEn: 'Right now, 100 people are inside this silent cube.. Winner takes $500,000 in cash!',
      timeline: [
        { start: 0, end: 3, text: '🚪 إغلاق الأبواب الحديدية وصدمة البداية' },
        { start: 3, end: 8, text: '💰 استعراض جبل الأموال النقدية وسط الغرفة' },
        { start: 8, end: 12, text: '⏱️ انطلاق ساعة العد التنازلي التنافسية' },
        { start: 12, end: 15, text: '🚨 الصدمة الأولى: انقطاع الكهرباء المفاجئ!' }
      ]
    },
    {
      id: 'sample-2',
      title: 'ماذا لو ابتلع ثقب أسود حجمه حبة رمل كوكب الأرض في 5 ثوانٍ؟',
      titleEn: 'What If a Micro Black Hole Collided with Earth?',
      category: 'science',
      viewsEst: '34.2M',
      ctr: '16.4%',
      themeColor: '#8b5cf6',
      bgGradient: 'from-purple-950 via-slate-950 to-blue-950',
      hookTextAr: 'لو سقطت حبة الرمل هذه الآن، فستبتلع الغلاف الجوي بالكامل خلال 4 ثوانٍ!',
      hookTextEn: 'If this grain of sand collides right now, it consumes our entire atmosphere in 4 seconds!',
      timeline: [
        { start: 0, end: 3, text: '🌌 سقوط حبة الرمل المشعة في الفضاء' },
        { start: 3, end: 8, text: '💥 بدء انهيار الجاذبية وسحب الأجسام' },
        { start: 8, end: 12, text: '⚛️ المحاكاة الكونية الفيزيائية ثلاثية الأبعاد' },
        { start: 12, end: 15, text: '🌍 النتيجة الصادمة التي أذهلت علماء الفلك' }
      ]
    },
    {
      id: 'sample-3',
      title: 'الخدعة البصرية المستحيلة التي حيرت 100 مليون شخص (بدون كلام)',
      titleEn: 'The Impossible Optical Illusion That Fooled 100,000,000 People',
      category: 'magic',
      viewsEst: '89.4M',
      ctr: '18.2%',
      themeColor: '#f59e0b',
      bgGradient: 'from-amber-950 via-slate-950 to-emerald-950',
      hookTextAr: 'الكرة تتدحرج إلى أعلى الدرج ضد الجاذبية في أول ثانية بدون أي صوت!',
      hookTextEn: 'The metal ball rolls UP the stairs defying physics in the first second!',
      timeline: [
        { start: 0, end: 3, text: '🌀 دوران الكرة السحرية عكس اتجاه الجاذبية' },
        { start: 3, end: 8, text: '📐 تغيير زاوية الكاميرا لكشف الخدعة البصرية' },
        { start: 8, end: 12, text: '🪄 الخدعة الثانية: اختفاء المكعب الخشبي' },
        { start: 12, end: 15, text: '🔄 الحلقة اللانهائية الساحرة (Infinite Loop)' }
      ]
    }
  ];

  const currentSample = samples[selectedSampleIndex];

  // Animation Timer
  useEffect(() => {
    let interval = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= duration) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 0.1;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying, duration]);

  const togglePlay = () => setIsPlaying(!isPlaying);
  const restart = () => {
    setCurrentTime(0);
    setIsPlaying(true);
  };

  const handlePublishThis = async () => {
    setPublishing(true);
    setPublishMessage('');
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: currentSample.title,
          description: `${currentSample.hookTextAr}\n\n#Viral #Trending #MrBeast #CosmicTube`,
          tags: ['viral', 'challenge', 'shorts', currentSample.category, 'youtube'],
          privacyStatus: 'public',
          categoryId: '24',
          isShort: aspectRatio === '9:16'
        })
      });
      const data = await res.json();
      if (data.success) {
        setPublishMessage(isAr ? '🎉 تم نشر هذا الفيديو بنجاح على قناتك الرسمية!' : 'Published video to channel successfully!');
        if (onPublishSample) onPublishSample(data);
      }
    } catch (e) {
      alert('فشل النشر: ' + e.message);
    } finally {
      setPublishing(false);
    }
  };

  const currentTimelineItem = currentSample?.timeline?.find(
    (item) => currentTime >= item.start && currentTime <= item.end
  );

  return (
    <div className="space-y-6">
      
      {/* Top Controls: Choose Sample */}
      <div className="p-4 sm:p-6 rounded-3xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase mb-2">
              <Play className="w-3.5 h-3.5 text-red-500" />
              <span>{isAr ? 'معاينة عينات الفيديوهات الحية' : 'Live Video Sample Player'}</span>
            </div>
            <h3 className="text-lg sm:text-2xl font-black text-white">
              {isAr ? 'شاهد كيف يبدو الفيديو رقم 1 في الواقع قبل النشر' : 'Experience the #1 Viral Video Format in Real-Time'}
            </h3>
          </div>

          {/* Aspect Ratio Switcher */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-950 rounded-xl border border-slate-800 self-start sm:self-auto">
            <button
              onClick={() => setAspectRatio('16:9')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                aspectRatio === '16:9' ? 'bg-red-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Monitor className="w-3.5 h-3.5" />
              <span>16:9 أفقي</span>
            </button>
            <button
              onClick={() => setAspectRatio('9:16')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                aspectRatio === '9:16' ? 'bg-red-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span>9:16 Shorts</span>
            </button>
          </div>
        </div>

        {/* Sample Tabs */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
          {samples.map((s, idx) => (
            <button
              key={s.id}
              onClick={() => {
                setSelectedSampleIndex(idx);
                setCurrentTime(0);
                setIsPlaying(false);
              }}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                selectedSampleIndex === idx
                  ? 'bg-slate-800 text-white border-2 border-red-500/70 shadow-lg'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.themeColor }}></span>
              <span className="truncate max-w-[200px]">{s.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Video Simulation Screen Container */}
      <div className="flex justify-center">
        <div 
          className={`relative rounded-3xl overflow-hidden border-2 border-slate-700/80 shadow-2xl bg-black transition-all duration-500 w-full ${
            aspectRatio === '9:16' ? 'max-w-sm aspect-[9/16]' : 'max-w-4xl aspect-video'
          }`}
        >
          {/* Animated Background Motion */}
          <div className={`absolute inset-0 bg-gradient-to-br ${currentSample.bgGradient} opacity-90`}>
            {/* Dynamic Animated Particles / Waves */}
            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px] animate-pulse"></div>
            
            {/* Pulsing Light Glow */}
            <div 
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full blur-3xl opacity-40 transition-all duration-700"
              style={{ backgroundColor: currentSample.themeColor }}
            ></div>
          </div>

          {/* Top Overlays: CTR & Viral Metrics */}
          <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-20 pointer-events-none">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-black/70 backdrop-blur-md border border-red-500/40 text-[11px] font-black text-red-400 shadow-lg">
              <Flame className="w-3.5 h-3.5 text-red-500 animate-bounce" />
              <span>{currentSample.ctr} CTR • {currentSample.viewsEst} {isAr ? 'مشاهدة متوقعة' : 'Est. Views'}</span>
            </div>

            <div className="px-2.5 py-1 rounded-md bg-black/70 backdrop-blur-md text-[11px] font-mono font-bold text-amber-300 border border-amber-500/30">
              00:{currentTime < 10 ? `0${Math.floor(currentTime)}` : Math.floor(currentTime)}:00
            </div>
          </div>

          {/* Middle Stage: The 3-Second Hook & Dynamic Subtitles */}
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center z-10">
            {/* Glowing Big Timer */}
            <div className="text-4xl sm:text-6xl font-black font-mono tracking-wider text-white drop-shadow-[0_0_20px_rgba(239,68,68,0.8)] mb-4">
              00:{String(Math.floor(currentTime)).padStart(2, '0')}.{Math.floor((currentTime % 1) * 10)}
            </div>

            {/* Current Action Pill */}
            {currentTimelineItem && (
              <div className="px-4 py-1.5 rounded-full bg-slate-900/90 border border-slate-700 text-xs font-bold text-emerald-400 mb-4 shadow-lg animate-fadeIn">
                {currentTimelineItem.text}
              </div>
            )}

            {/* Kinetic Animated Subtitle (Just like MrBeast shorts) */}
            <div className="max-w-xl mx-auto p-4 rounded-2xl bg-black/80 backdrop-blur-md border border-white/10 shadow-2xl">
              <div className="text-sm sm:text-xl font-black text-yellow-300 leading-snug drop-shadow-md">
                "{currentSample?.hookTextAr || ''}"
              </div>
              <div className="text-xs sm:text-sm text-slate-300 font-mono italic mt-1.5">
                "{currentSample?.hookTextEn || ''}"
              </div>
            </div>
          </div>

          {/* Bottom Player Controls */}
          <div className="absolute bottom-0 inset-x-0 p-4 bg-gradient-to-t from-black via-black/80 to-transparent z-20 space-y-3">
            {/* Progress Bar */}
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden cursor-pointer">
              <div 
                className="h-full bg-gradient-to-r from-red-600 via-rose-500 to-amber-400 transition-all duration-100"
                style={{ width: `${(currentTime / duration) * 100}%` }}
              ></div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={togglePlay}
                  className="w-10 h-10 rounded-full bg-red-600 hover:bg-red-500 text-white flex items-center justify-center shadow-lg shadow-red-600/40 transition"
                >
                  {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
                </button>

                <button
                  onClick={restart}
                  className="p-2 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition"
                  title="إعادة التشغيل"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>

                <span className="text-xs font-mono text-slate-400">
                  {currentTime.toFixed(1)}s / {duration}s
                </span>
              </div>

              {/* Instant Publish Button from inside the player */}
              <button
                onClick={handlePublishThis}
                disabled={publishing}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs font-black shadow-lg shadow-red-600/30 transition flex items-center gap-1.5 disabled:opacity-50"
              >
                <Send className={`w-3.5 h-3.5 ${publishing ? 'animate-bounce' : ''}`} />
                <span>{publishing ? (isAr ? 'جاري النشر...' : 'Publishing...') : (isAr ? 'نشر هذا الفيديو الآن للقناة' : 'Publish This Video')}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {publishMessage && (
        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center gap-2 animate-fadeIn max-w-xl mx-auto">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{publishMessage}</span>
        </div>
      )}

    </div>
  );
}
