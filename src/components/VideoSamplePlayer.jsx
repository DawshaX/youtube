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
  RefreshCw,
  Film,
  Download,
  Zap,
  TrendingUp,
  Cpu,
  Video,
  Eye,
  Sliders,
  Copy,
  Check
} from 'lucide-react';

export default function VideoSamplePlayer({ onPublishSample, isAr }) {
  // Mode: 'simulator' (The interactive viral emulation engine) vs 'mp4' (The rendered real MP4 player)
  const [viewMode, setViewMode] = useState('simulator'); 

  // Player State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(15);
  const [isMuted, setIsMuted] = useState(false);
  const [aspectRatio, setAspectRatio] = useState('9:16'); // '16:9' | '9:16'
  
  // Samples & Topics State
  const [availableTopics, setAvailableTopics] = useState([]);
  const [selectedTopicIndex, setSelectedTopicIndex] = useState(0);
  const [producedVideos, setProducedVideos] = useState([]);
  const [selectedMp4Video, setSelectedMp4Video] = useState(null);

  // Production State
  const [producing, setProducing] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [publishing, setPublishing] = useState(false);
  const [publishMessage, setPublishMessage] = useState('');
  const [copiedScript, setCopiedScript] = useState(false);

  const realVideoRef = useRef(null);

  // Fallback initial rich viral samples (from our Radar and Matrix)
  const defaultSamples = [
    {
      id: 'trend-01',
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
      ],
      tags: ['تحديات', 'mrbeast', '100 شخص', 'viral', 'impossible', 'shorts']
    },
    {
      id: 'trend-02',
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
      ],
      tags: ['فضاء', 'ثقب اسود', 'kurzgesagt', 'فيزياء', 'ماذا لو', 'shorts']
    },
    {
      id: 'trend-03',
      title: 'وضعت 50,000 لتر نيتروجين سائل في مسبح عملاق!.. والنتيجة انفجار جليدي!',
      titleEn: 'Dropping 50,000L Liquid Nitrogen in Giant Pool!',
      category: 'experiments',
      viewsEst: '62.1M',
      ctr: '18.9%',
      themeColor: '#06b6d4',
      bgGradient: 'from-cyan-950 via-slate-950 to-blue-950',
      hookTextAr: 'في ثانية 0، شاحنة النيتروجين تسكب حمولتها والمسبح ينفجر بسحابة جليد عملاقة!',
      hookTextEn: 'At second zero, 50,000 liters hit the pool causing a massive sub-zero eruption!',
      timeline: [
        { start: 0, end: 3, text: '❄️ صب النيتروجين السائل فوراً عند -196°C' },
        { start: 3, end: 8, text: '💨 تصاعد سحابة ضبابية بيضاء تغطي الموقع' },
        { start: 8, end: 12, text: '🧊 تحول سطح الماء لطبقة جليد سميكة' },
        { start: 12, end: 15, text: '🎉 قفز الفريق بملابس الحماية على الجليد' }
      ],
      tags: ['تجارب', 'نيتروجين', 'انفجار', 'experiment', 'liquid nitrogen', 'shorts']
    },
    {
      id: 'trend-04',
      title: 'الخدعة البصرية المستحيلة التي حيرت 100 مليون شخص (بدون كلام)',
      titleEn: 'The Impossible Optical Illusion That Fooled 100M People',
      category: 'magic',
      viewsEst: '89.4M',
      ctr: '19.2%',
      themeColor: '#f59e0b',
      bgGradient: 'from-amber-950 via-slate-950 to-emerald-950',
      hookTextAr: 'الكرة تتدحرج إلى أعلى الدرج ضد الجاذبية في أول ثانية بدون أي صوت!',
      hookTextEn: 'The metal ball rolls UP the stairs defying physics in the first second!',
      timeline: [
        { start: 0, end: 3, text: '🌀 دوران الكرة السحرية عكس اتجاه الجاذبية' },
        { start: 3, end: 8, text: '📐 تغيير زاوية الكاميرا لكشف الخدعة البصرية' },
        { start: 8, end: 12, text: '🪄 الخدعة الثانية: اختفاء المكعب الخشبي' },
        { start: 12, end: 15, text: '🔄 الحلقة اللانهائية الساحرة (Infinite Loop)' }
      ],
      tags: ['خدع', 'سحر', 'optical illusion', 'zach king', 'viral', 'shorts']
    }
  ];

  // Fetch topics from backend
  const fetchTopics = async () => {
    try {
      const res = await fetch('/api/factory/topics');
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        // Map backend topics to simulator format
        const mapped = data.map((t, idx) => ({
          id: t.id || `topic-${idx}`,
          title: t.title_ar || t.title || t.angle,
          titleEn: t.title_en || t.titleEn || 'Viral Sensation',
          category: t.category || 'challenges',
          viewsEst: t.viewsEst || `${(Math.random() * 30 + 15).toFixed(1)}M`,
          ctr: t.ctr || `${(15 + Math.random() * 4).toFixed(1)}%`,
          themeColor: t.themeColor || (idx % 3 === 0 ? '#ef4444' : idx % 3 === 1 ? '#8b5cf6' : '#06b6d4'),
          bgGradient: t.bgGradient || 'from-red-950 via-slate-950 to-slate-900',
          hookTextAr: t.hook_ar || t.hook || 'في أول ثانية، يحدث الحدث الصاعق الذي لا يصدقه عقل!',
          hookTextEn: t.hook_en || 'In the first second, the unbelievable moment happens!',
          timeline: [
            { start: 0, end: 3, text: '⚡ خطاف الـ 3 ثواني الأولى وحبس الأنفاس' },
            { start: 3, end: 8, text: '💰 رفع الرهان واستعراض القواعد المستحيلة' },
            { start: 8, end: 12, text: '⏱️ العد التنازلي واشتعال المنافسة الكبرى' },
            { start: 12, end: 15, text: '🚨 الصدمة والمنعطف غير المتوقع كلياً' }
          ],
          tags: (t.tags && typeof t.tags === 'string') ? t.tags.split(',') : ['viral', 'shorts', 'mrbeast']
        }));
        setAvailableTopics(mapped);
      } else {
        setAvailableTopics(defaultSamples);
      }
    } catch (e) {
      setAvailableTopics(defaultSamples);
    }
  };

  // Fetch produced MP4 videos
  const fetchProducedVideos = async () => {
    try {
      const res = await fetch('/api/factory/videos');
      const data = await res.json();
      if (Array.isArray(data)) {
        setProducedVideos(data);
        if (data.length > 0 && !selectedMp4Video) {
          setSelectedMp4Video(data[0]);
        }
      }
    } catch (err) {
      console.error('Fetch factory videos error:', err);
    }
  };

  useEffect(() => {
    fetchTopics();
    fetchProducedVideos();
  }, []);

  const activeSamples = availableTopics.length > 0 ? availableTopics : defaultSamples;
  const currentSample = activeSamples[selectedTopicIndex] || activeSamples[0];

  // Simulation Timer
  useEffect(() => {
    let interval = null;
    if (isPlaying && viewMode === 'simulator') {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= duration) {
            setIsPlaying(false);
            return 0;
          }
          return Number((prev + 0.1).toFixed(1));
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying, duration, viewMode]);

  const togglePlay = () => setIsPlaying(!isPlaying);
  const restart = () => {
    setCurrentTime(0);
    setIsPlaying(true);
  };

  // Generate a brand new viral idea dynamically from the matrix
  const handleGenerateFreshIdea = async () => {
    try {
      const res = await fetch('/api/factory/topics');
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        // Shuffle or pick random
        const randomIndex = Math.floor(Math.random() * data.length);
        fetchTopics();
        setSelectedTopicIndex(randomIndex);
        setCurrentTime(0);
        setIsPlaying(true);
      }
    } catch (_) {}
  };

  // Publish Selected Video to YouTube (One-Click)
  const handlePublishToYouTube = async () => {
    setPublishing(true);
    setPublishMessage('');
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: currentSample.title,
          description: `${currentSample.hookTextAr}\n\nProduced with CosmicTube Universal Viral Engine.\n#CosmicTube #Shorts #Viral #Trending #MrBeast`,
          tags: currentSample.tags || ['viral', 'shorts', 'challenge', 'cosmictube'],
          privacyStatus: 'public',
          categoryId: '24',
          isShort: aspectRatio === '9:16'
        })
      });
      const data = await res.json();
      if (data.success) {
        setPublishMessage(isAr ? '🎉 تم نشر هذا الفيديو بنجاح على قناتك الرسمية على يوتيوب!' : 'Published video to channel successfully!');
        if (onPublishSample) onPublishSample(data);
      }
    } catch (err) {
      alert('خطأ أثناء النشر: ' + err.message);
    } finally {
      setPublishing(false);
    }
  };

  // Trigger Real FFmpeg Render Job
  const handleTriggerRender = async () => {
    setProducing(true);
    setCurrentJob(null);
    try {
      const res = await fetch('/api/factory/produce', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topicId: currentSample.id,
          topic: currentSample
        })
      });
      const data = await res.json();
      if (data.job) {
        setCurrentJob(data.job);
        pollJob(data.job.jobId);
      }
    } catch (err) {
      alert('خطأ أثناء بدء الريندر: ' + err.message);
      setProducing(false);
    }
  };

  const pollJob = (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/factory/job/${jobId}`);
        const data = await res.json();
        if (data) {
          setCurrentJob(data);
          if (data.status === 'completed' || data.status === 'error') {
            clearInterval(pollInterval);
            setProducing(false);
            if (data.status === 'completed') {
              fetchProducedVideos();
              setViewMode('mp4');
            }
          }
        }
      } catch (err) {
        clearInterval(pollInterval);
        setProducing(false);
      }
    }, 2500);
  };

  const copyScript = () => {
    const text = `عنوان الفيديو: ${currentSample.title}\nالخطاف (0-3 ثواني): ${currentSample.hookTextAr}\nالأقسام:\n${currentSample.timeline.map(t => `${t.start}-${t.end}s: ${t.text}`).join('\n')}`;
    navigator.clipboard.writeText(text);
    setCopiedScript(true);
    setTimeout(() => setCopiedScript(false), 2000);
  };

  const currentTimelineItem = currentSample.timeline?.find(
    (item) => currentTime >= item.start && currentTime <= item.end
  ) || currentSample.timeline?.[0];

  return (
    <div className="space-y-6">
      
      {/* Top Banner: Mode & Strategy Overview */}
      <div className="p-6 rounded-3xl bg-slate-900/95 border border-slate-800 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-black uppercase flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                {isAr ? 'برنامجنا ورادارنا الفيروسي رقم 1 عالمياً' : 'Universal Viral Radar & Studio'}
              </span>
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-black flex items-center gap-1">
                <Flame className="w-3.5 h-3.5" />
                {isAr ? 'مليارات المشاهد الجاهزة للنشر' : 'Billions of Ready-to-Publish Scenes'}
              </span>
            </div>
            <h2 className="text-xl sm:text-3xl font-black text-white">
              {isAr ? 'استوديو ومحاكي الفيديوهات الفيروسية المليارية' : 'The Billion-View Viral Video Studio'}
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
              {isAr 
                ? 'استنساخ معادلة أكبر قنوات العالم (MrBeast، Kurzgesagt، Zach King) مع خطاف الـ 3 ثواني الصاعق، الترجمة الحركية الصفراء، والمونتاج الملياري الجاهز للنشر المباشر!' 
                : 'Emulating top global channels with 3-second visual hooks, kinetic yellow subtitles, and ready-to-publish viral formulas!'}
            </p>
          </div>

          {/* Mode Switcher: Viral Simulator vs Exported MP4 Gallery */}
          <div className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 shrink-0">
            <button
              onClick={() => setViewMode('simulator')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-black transition ${
                viewMode === 'simulator'
                  ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-lg shadow-red-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>{isAr ? 'محاكي الفيديوهات الحية' : 'Live Viral Simulator'}</span>
            </button>
            <button
              onClick={() => setViewMode('mp4')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-black transition ${
                viewMode === 'mp4'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Film className="w-4 h-4" />
              <span>{isAr ? `معرض الـ MP4 المصدر (${producedVideos.length})` : `MP4 Library (${producedVideos.length})`}</span>
            </button>
          </div>
        </div>

        {/* Idea Navigation & Matrix Shuffler */}
        {viewMode === 'simulator' && (
          <div className="mt-6 pt-5 border-t border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
              {activeSamples.slice(0, 6).map((s, idx) => (
                <button
                  key={s.id || idx}
                  onClick={() => {
                    setSelectedTopicIndex(idx);
                    setCurrentTime(0);
                    setIsPlaying(false);
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-black transition flex items-center gap-2 shrink-0 ${
                    selectedTopicIndex === idx
                      ? 'bg-slate-800 text-white border-2 border-red-500 shadow-md shadow-red-500/20'
                      : 'bg-slate-950/80 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.themeColor }}></span>
                  <span className="truncate max-w-[150px] sm:max-w-[220px]">{s.title}</span>
                </button>
              ))}
            </div>

            <button
              onClick={handleGenerateFreshIdea}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/30 text-xs font-black transition flex items-center justify-center gap-2 shrink-0 shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>{isAr ? 'سحب فكرة جديدة من مصفوفة الملايير ⚡' : 'Generate Fresh Viral Idea ⚡'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Main View Area */}
      {viewMode === 'simulator' ? (
        /* ================= VIRAL VIDEO SIMULATOR ================= */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left/Main Column: The High-Energy Video Stage */}
          <div className="lg:col-span-8 flex flex-col items-center">
            
            {/* Aspect Ratio Switcher */}
            <div className="flex items-center gap-2 mb-3 bg-slate-900 px-3 py-1.5 rounded-2xl border border-slate-800">
              <button
                onClick={() => setAspectRatio('9:16')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition ${
                  aspectRatio === '9:16' ? 'bg-red-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                <span>9:16 Shorts (المفضل فيروسياً)</span>
              </button>
              <button
                onClick={() => setAspectRatio('16:9')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition ${
                  aspectRatio === '16:9' ? 'bg-red-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Monitor className="w-3.5 h-3.5" />
                <span>16:9 أفقي كامل</span>
              </button>
            </div>

            {/* The Simulation Screen Container */}
            <div 
              className={`relative rounded-3xl overflow-hidden border-2 border-slate-700/80 shadow-[0_0_50px_rgba(0,0,0,0.8)] bg-black transition-all duration-300 w-full select-none ${
                aspectRatio === '9:16' ? 'max-w-xs sm:max-w-sm aspect-[9/16]' : 'max-w-3xl aspect-video'
              }`}
            >
              {/* Dynamic Animated Motion Backdrop */}
              <div className={`absolute inset-0 bg-gradient-to-br ${currentSample.bgGradient} opacity-95`}>
                
                {/* Speed Lines & Particle Grid */}
                <div className="absolute inset-0 opacity-25 bg-[radial-gradient(#fff_1.5px,transparent_1.5px)] [background-size:20px_20px] animate-pulse"></div>
                
                {/* Dynamic Pulsing Radial Core */}
                <div 
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 rounded-full blur-3xl opacity-50 transition-all duration-700 animate-ping"
                  style={{ backgroundColor: currentSample.themeColor, animationDuration: '4s' }}
                ></div>

                {/* Top Hazard Warning Stripes */}
                <div className="absolute top-0 inset-x-0 h-3 bg-[repeating-linear-gradient(45deg,#000,#000_10px,#f59e0b_10px,#f59e0b_20px)] opacity-80"></div>
              </div>

              {/* Top Bar Overlays: CTR & Est Views */}
              <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-20 pointer-events-none">
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-black/80 backdrop-blur-md border border-red-500/40 text-[11px] font-black text-red-400 shadow-xl">
                  <Flame className="w-3.5 h-3.5 text-red-500 animate-bounce" />
                  <span>{currentSample.ctr} CTR • {currentSample.viewsEst} {isAr ? 'مشاهدة' : 'Views'}</span>
                </div>

                <div className="px-2.5 py-1 rounded-lg bg-black/80 backdrop-blur-md text-[11px] font-mono font-bold text-amber-300 border border-amber-500/40 shadow-lg">
                  00:{currentTime < 10 ? `0${Math.floor(currentTime)}` : Math.floor(currentTime)}.{Math.floor((currentTime % 1) * 10)}
                </div>
              </div>

              {/* Center Stage: The 3-Second Hook & Explosive Subtitles */}
              <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center z-10 pointer-events-none">
                
                {/* Massive Glowing Countdown Timer (MrBeast Formula) */}
                <div className="text-4xl sm:text-6xl font-black font-mono tracking-wider text-white drop-shadow-[0_0_25px_rgba(239,68,68,0.9)] mb-3 animate-pulse">
                  00:{String(Math.floor(currentTime)).padStart(2, '0')}.{Math.floor((currentTime % 1) * 10)}
                </div>

                {/* Current Action / Retention Beat Pill */}
                {currentTimelineItem && (
                  <div className="px-4 py-1.5 rounded-full bg-black/85 backdrop-blur-md border border-slate-600 text-xs font-black text-emerald-400 mb-4 shadow-xl animate-bounce">
                    {currentTimelineItem.text}
                  </div>
                )}

                {/* Kinetic Animated Subtitle (MrBeast Bouncing Yellow Font) */}
                <div className="max-w-md mx-auto p-4 rounded-2xl bg-black/85 backdrop-blur-lg border-2 border-yellow-500/40 shadow-2xl transform transition-transform">
                  <div className="text-sm sm:text-lg font-black text-yellow-300 leading-snug drop-shadow-[0_2px_10px_rgba(0,0,0,0.9)]">
                    "{currentSample.hookTextAr}"
                  </div>
                  <div className="text-[11px] sm:text-xs text-slate-300 font-mono italic mt-1.5 opacity-90">
                    "{currentSample.hookTextEn}"
                  </div>
                </div>

                {/* Sound wave simulation */}
                <div className="flex items-center gap-1 mt-4">
                  {[40, 70, 100, 60, 90, 45, 80, 50, 95, 30].map((h, i) => (
                    <div 
                      key={i} 
                      className="w-1 bg-gradient-to-t from-red-500 to-yellow-400 rounded-full transition-all duration-150"
                      style={{ height: isPlaying ? `${(h * (0.4 + Math.random() * 0.6))}px` : '6px' }}
                    ></div>
                  ))}
                </div>
              </div>

              {/* Bottom Player Controls */}
              <div className="absolute bottom-0 inset-x-0 p-4 bg-gradient-to-t from-black via-black/80 to-transparent z-20 space-y-3">
                {/* Timeline Scrubber */}
                <div 
                  onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const pos = (e.clientX - rect.left) / rect.width;
                    setCurrentTime(Number((pos * duration).toFixed(1)));
                  }}
                  className="w-full h-2 bg-slate-800 rounded-full overflow-hidden cursor-pointer relative"
                >
                  <div 
                    className="h-full bg-gradient-to-r from-red-600 via-yellow-400 to-emerald-400 transition-all duration-100"
                    style={{ width: `${(currentTime / duration) * 100}%` }}
                  ></div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={togglePlay}
                      className="w-9 h-9 rounded-full bg-red-600 hover:bg-red-500 text-white flex items-center justify-center shadow-lg shadow-red-600/40 transition"
                    >
                      {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                    </button>

                    <button
                      onClick={restart}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      title="إعادة التشغيل"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => setIsMuted(!isMuted)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                    >
                      {isMuted ? <VolumeX className="w-3.5 h-3.5 text-red-400" /> : <Volume2 className="w-3.5 h-3.5 text-emerald-400" />}
                    </button>

                    <span className="text-[11px] font-mono text-slate-400">
                      {currentTime.toFixed(1)}s / {duration}s
                    </span>
                  </div>

                  {/* 1-Click Publish Button directly from simulator */}
                  <button
                    onClick={handlePublishToYouTube}
                    disabled={publishing}
                    className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs font-black shadow-lg shadow-red-600/30 transition flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <Send className={`w-3 h-3 ${publishing ? 'animate-bounce' : ''}`} />
                    <span>{publishing ? (isAr ? 'جاري النشر...' : 'Publishing...') : (isAr ? 'نشر هذا الفيديو الآن' : 'Publish This Video')}</span>
                  </button>
                </div>
              </div>
            </div>

            {publishMessage && (
              <div className="mt-4 p-3.5 rounded-2xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs font-black flex items-center gap-2 animate-fadeIn max-w-md w-full">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{publishMessage}</span>
              </div>
            )}
          </div>

          {/* Right Column: Video DNA Breakdown & Real Render Actions */}
          <div className="lg:col-span-4 space-y-4">
            
            {/* Video DNA Card */}
            <div className="p-5 rounded-3xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-red-500" />
                  <h3 className="text-sm font-black text-white">
                    {isAr ? 'تشريح الـ DNA الفيروسي' : 'Viral DNA Breakdown'}
                  </h3>
                </div>
                <button
                  onClick={copyScript}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-bold flex items-center gap-1 transition"
                >
                  {copiedScript ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedScript ? (isAr ? 'تم النسخ' : 'Copied') : (isAr ? 'نسخ السيناريو' : 'Copy Script')}</span>
                </button>
              </div>

              <div>
                <span className="text-[11px] font-bold text-slate-400">{isAr ? 'العنوان الفيروسي:' : 'Viral Title:'}</span>
                <p className="text-xs sm:text-sm font-black text-slate-100 mt-0.5 leading-snug">
                  {currentSample.title}
                </p>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 font-bold">{isAr ? 'سرعة الانتشار:' : 'Velocity:'}</span>
                  <span className="text-emerald-400 font-mono font-bold">9.7M {isAr ? 'مشاهدة/يوم' : 'views/day'}</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 font-bold">{isAr ? 'نسبة النقر CTR:' : 'Est. CTR:'}</span>
                  <span className="text-red-400 font-mono font-bold">{currentSample.ctr}</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 font-bold">{isAr ? 'الصيغة الأساسية:' : 'Format:'}</span>
                  <span className="text-amber-400 font-bold">{isAr ? 'تحديات كبرى وجوائز (MrBeast)' : 'High Stakes Challenges'}</span>
                </div>
              </div>

              {/* Timeline Steps */}
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-slate-400">{isAr ? 'مراحل الاحتفاظ بالجمهور:' : 'Retention Timeline:'}</span>
                <div className="space-y-1.5">
                  {currentSample.timeline?.map((step, i) => (
                    <div 
                      key={i}
                      className={`p-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                        currentTime >= step.start && currentTime <= step.end
                          ? 'bg-red-500/20 border border-red-500/50 text-red-200'
                          : 'bg-slate-950/60 border border-slate-800 text-slate-400'
                      }`}
                    >
                      <span className="font-mono text-[10px] text-amber-400 shrink-0">{step.start}-{step.end}s</span>
                      <span className="truncate">{step.text}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Render Trigger Box (Using the factory as underlying engine) */}
              <div className="pt-3 border-t border-slate-800 space-y-3">
                <button
                  onClick={handleTriggerRender}
                  disabled={producing}
                  className="w-full py-3 rounded-2xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-black text-xs sm:text-sm shadow-xl shadow-purple-600/30 transition flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Cpu className={`w-4 h-4 ${producing ? 'animate-spin' : ''}`} />
                  <span>{producing ? (isAr ? 'جاري الريندر والمونتاج بـ FFmpeg...' : 'Rendering with FFmpeg...') : (isAr ? 'ريندر وتصدير MP4 سينمائي حقيقي ⚡' : 'Render Real MP4 Video ⚡')}</span>
                </button>

                {currentJob && (
                  <div className="p-3.5 rounded-2xl bg-slate-950 border border-purple-500/40 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-purple-300 truncate max-w-[200px]">{currentJob.stage}</span>
                      <span className="font-mono font-black text-white">{currentJob.progress}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-purple-500 to-indigo-400 transition-all duration-300"
                        style={{ width: `${currentJob.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>

            </div>

          </div>
        </div>
      ) : (
        /* ================= EXPORTED MP4 GALLERY & PLAYER ================= */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Main MP4 Player */}
          <div className="lg:col-span-8 flex flex-col items-center">
            {selectedMp4Video ? (
              <div className="w-full max-w-sm aspect-[9/16] rounded-3xl overflow-hidden border-2 border-purple-500/50 shadow-2xl bg-black relative">
                <video
                  ref={realVideoRef}
                  src={selectedMp4Video.url}
                  controls
                  playsInline
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="p-12 text-center rounded-3xl bg-slate-900 border border-slate-800 w-full max-w-md">
                <Film className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-sm font-bold text-slate-400">
                  {isAr ? 'لم يتم تصدير أي فيديو MP4 بعد. ارجع للمحاكي واضغط "ريندر وتصدير MP4"!' : 'No MP4 videos exported yet. Return to simulator and click Render!'}
                </p>
              </div>
            )}

            {selectedMp4Video && (
              <div className="mt-4 flex items-center gap-3">
                <a
                  href={selectedMp4Video.url}
                  download={selectedMp4Video.filename}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-black transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{isAr ? 'تحميل ملف MP4' : 'Download MP4'}</span>
                </a>

                <button
                  onClick={() => {
                    handlePublishToYouTube();
                  }}
                  disabled={publishing}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 text-white text-xs font-black transition flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{isAr ? 'نشر هذا الـ MP4 لقناتي' : 'Publish MP4 to YouTube'}</span>
                </button>
              </div>
            )}
          </div>

          {/* Exported List */}
          <div className="lg:col-span-4 space-y-3">
            <h3 className="text-sm font-black text-white flex items-center gap-2">
              <Film className="w-4 h-4 text-purple-400" />
              <span>{isAr ? 'الفيديوهات المنتجة والمصدرة' : 'Exported MP4 List'}</span>
            </h3>

            <div className="space-y-2">
              {producedVideos.map((vid) => (
                <div
                  key={vid.id}
                  onClick={() => setSelectedMp4Video(vid)}
                  className={`p-3 rounded-2xl border transition cursor-pointer flex items-center justify-between ${
                    selectedMp4Video?.id === vid.id
                      ? 'bg-purple-950/40 border-purple-500 text-white'
                      : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="space-y-1 min-w-0 pr-2">
                    <p className="text-xs font-black truncate">{vid.title}</p>
                    <p className="text-[10px] text-slate-400 font-mono">{vid.sizeMB} MB • {vid.id}.mp4</p>
                  </div>
                  <Play className="w-4 h-4 text-purple-400 shrink-0" />
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
