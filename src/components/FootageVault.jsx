import React, { useState, useEffect } from 'react';
import { 
  Film, 
  Play, 
  Pause, 
  Sparkles, 
  Flame, 
  DollarSign, 
  Clock, 
  Trophy, 
  Snowflake, 
  Download, 
  Layers, 
  CheckCircle2, 
  Sliders, 
  ExternalLink,
  ShieldCheck,
  Zap,
  Maximize2
} from 'lucide-react';

export default function FootageVault({ onSelectClipForFactory, isAr }) {
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('all');
  const [playingClip, setPlayingClip] = useState(null);
  const [previewModalClip, setPreviewModalClip] = useState(null);
  const [copiedNotification, setCopiedNotification] = useState('');

  const fetchFootage = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/footage');
      const data = await res.json();
      setClips(data.clips || []);
    } catch (err) {
      console.error('Failed to load footage:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFootage();
  }, []);

  const categories = [
    { id: 'all', labelAr: 'جميع المشاهد الجاهزة', labelEn: 'All Footage', icon: Layers },
    { id: 'challenges', labelAr: 'تحديات ونيران وخطر', labelEn: 'Fire & Action', icon: Flame },
    { id: 'money', labelAr: 'أموال وجوائز كاش', labelEn: 'Money & Cash', icon: DollarSign },
    { id: 'survival', labelAr: 'عواصف وبقاء قاسي', labelEn: 'Survival & Ice', icon: Snowflake },
    { id: 'countdown', labelAr: 'عدادات وإنذار طوارئ', labelEn: 'HUD & Timers', icon: Clock },
    { id: 'celebration', labelAr: 'احتفالات وتتويج الفائز', labelEn: 'Winner Celebrations', icon: Trophy },
  ];

  const filteredClips = activeCategory === 'all' 
    ? clips 
    : clips.filter(c => c.category === activeCategory);

  const handleUseInFactory = (clip) => {
    if (onSelectClipForFactory) {
      onSelectClipForFactory(clip);
    }
    setCopiedNotification(isAr ? `تم اختيار «${clip.titleAr}» للمصنع!` : `Selected ${clip.titleEn} for Factory!`);
    setTimeout(() => setCopiedNotification(''), 3000);
  };

  return (
    <div className="space-y-8 animate-fadeIn pb-16">
      
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-red-950/80 via-slate-900 to-amber-950/40 p-6 sm:p-10 border border-red-500/30 shadow-2xl shadow-red-950/50">
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-red-600/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -left-20 -bottom-20 w-80 h-80 bg-amber-600/15 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/40 text-red-400 text-xs font-bold tracking-wide">
              <Film className="w-3.5 h-3.5 animate-pulse" />
              <span>{isAr ? 'مكتبة اللقطات الحية والمشاهد الجاهزة' : 'Stock Footage & B-Roll Vault'}</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
              {isAr ? 'مشاهد فيديو سينمائية متحركة 100%' : '100% Dynamic Cinema-Grade Video Clips'}
            </h1>
            <p className="text-slate-300 text-sm sm:text-base max-w-2xl leading-relaxed">
              {isAr 
                ? 'مكتبة مدمجة من لقطات الفيديو الحقيقية والمؤثرات البصرية (نيران، أمطار أموال، عواصف ثلجية، مؤقتات خطر، كونفيتي فوز) جاهزة للتركيب الفوري ومطابقة إيقاع MrBeast العالمي بدون صور ساكنة.'
                : 'A dedicated library of ready-to-use motion video footage (fire, money rain, blizzards, countdown HUDs, winner confetti) engineered to match MrBeast-tier high-retention velocity.'}
            </p>
          </div>

          <div className="flex flex-wrap gap-2.5">
            <div className="px-3.5 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs font-semibold text-slate-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>{isAr ? 'بدون حقوق ملكية 100%' : '100% Royalty Free'}</span>
            </div>
            <div className="px-3.5 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>1080×1920 (9:16 Shorts)</span>
            </div>
            <div className="px-3.5 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs font-semibold text-slate-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-red-400" />
              <span>{isAr ? `${clips.length} مشاهد فيديو جاهزة` : `${clips.length} Ready Video Clips`}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Toast */}
      {copiedNotification && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-2xl bg-emerald-600 text-white font-bold shadow-2xl flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-5 h-5" />
          <span>{copiedNotification}</span>
        </div>
      )}

      {/* Category Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
        {categories.map((cat) => {
          const Icon = cat.icon;
          const isActive = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-lg shadow-red-600/30 ring-2 ring-red-400/40'
                  : 'bg-slate-900/90 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{isAr ? cat.labelAr : cat.labelEn}</span>
            </button>
          );
        })}
      </div>

      {/* Clips Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <div className="w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-400 text-sm font-medium">
            {isAr ? 'جاري فحص وتجهيز مكتبة المشاهد...' : 'Loading footage vault...'}
          </p>
        </div>
      ) : filteredClips.length === 0 ? (
        <div className="text-center py-20 bg-slate-900/40 rounded-3xl border border-slate-800 text-slate-400">
          <Film className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <p className="text-lg font-bold">{isAr ? 'لا توجد مشاهد في هذا التصنيف' : 'No clips found in this category'}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredClips.map((clip) => {
            const isThisPlaying = playingClip === clip.filename;
            return (
              <div
                key={clip.filename}
                className="group relative rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-red-500/60 overflow-hidden shadow-xl hover:shadow-2xl hover:shadow-red-950/40 transition-all duration-300 flex flex-col"
              >
                {/* 9:16 Video Preview Container */}
                <div className="relative aspect-[9/16] bg-black overflow-hidden flex items-center justify-center">
                  <video
                    src={clip.url}
                    loop
                    muted
                    playsInline
                    autoPlay
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />

                  {/* Badges on Video Top */}
                  <div className="absolute top-3 inset-x-3 flex items-center justify-between pointer-events-none">
                    <span className="px-2.5 py-1 rounded-lg bg-black/75 backdrop-blur-md text-[10px] font-extrabold text-amber-400 border border-amber-500/30">
                      {clip.duration} • {clip.fps} FPS
                    </span>
                    <span className="px-2.5 py-1 rounded-lg bg-red-600/90 backdrop-blur-md text-[10px] font-extrabold text-white uppercase tracking-wider">
                      {clip.categoryAr || clip.category}
                    </span>
                  </div>

                  {/* Play / Expand overlay */}
                  <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                    <button
                      onClick={() => setPreviewModalClip(clip)}
                      className="p-3 rounded-full bg-red-600/90 text-white hover:bg-red-500 hover:scale-110 transition shadow-lg"
                      title={isAr ? 'تكبير وعرض الشاشة' : 'Fullscreen Preview'}
                    >
                      <Maximize2 className="w-5 h-5" />
                    </button>
                    <a
                      href={clip.url}
                      download={clip.filename}
                      className="p-3 rounded-full bg-slate-800/90 text-white hover:bg-slate-700 hover:scale-110 transition shadow-lg"
                      title={isAr ? 'تحميل الفيديو MP4' : 'Download MP4'}
                    >
                      <Download className="w-5 h-5" />
                    </a>
                  </div>

                  {/* Bottom resolution pill */}
                  <div className="absolute bottom-3 right-3 pointer-events-none">
                    <span className="px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-md text-[9px] font-mono text-slate-300 border border-slate-700/60">
                      1080×1920 MP4
                    </span>
                  </div>
                </div>

                {/* Details Footer */}
                <div className="p-4 sm:p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div className="space-y-1.5">
                    <h3 className="font-extrabold text-base text-white group-hover:text-red-400 transition-colors line-clamp-1">
                      {isAr ? clip.titleAr : clip.titleEn}
                    </h3>
                    <p className="text-xs text-slate-400 font-medium line-clamp-2 leading-relaxed">
                      {clip.titleEn}
                    </p>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5">
                    {(clip.tags || []).slice(0, 4).map((tag, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-md bg-slate-800/80 text-[10px] font-medium text-slate-400 border border-slate-700/50"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>

                  {/* Action Buttons */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2">
                    <button
                      onClick={() => handleUseInFactory(clip)}
                      className="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-red-600/20 active:scale-95 transition"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{isAr ? 'استخدم في المونتاج' : 'Use in Factory'}</span>
                    </button>
                    <button
                      onClick={() => setPreviewModalClip(clip)}
                      className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                      title={isAr ? 'معاينة' : 'Preview'}
                    >
                      <Play className="w-4 h-4" />
                    </button>
                  </div>
                </div>

              </div>
            );
          })}
        </div>
      )}

      {/* Fullscreen Video Modal */}
      {previewModalClip && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex items-center justify-center p-4">
          <div className="relative max-w-sm w-full bg-slate-900 rounded-3xl border border-red-500/40 p-4 shadow-2xl flex flex-col items-center space-y-4 animate-scaleUp">
            
            <div className="w-full flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="text-right rtl:text-right ltr:text-left">
                <h4 className="font-bold text-sm text-white line-clamp-1">
                  {isAr ? previewModalClip.titleAr : previewModalClip.titleEn}
                </h4>
                <p className="text-[10px] text-slate-400 font-mono">
                  {previewModalClip.res} • {previewModalClip.duration}
                </p>
              </div>
              <button
                onClick={() => setPreviewModalClip(null)}
                className="px-3 py-1 rounded-xl bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 font-bold text-xs"
              >
                ✕ {isAr ? 'إغلاق' : 'Close'}
              </button>
            </div>

            <div className="w-full aspect-[9/16] rounded-2xl overflow-hidden bg-black shadow-inner border border-slate-800">
              <video
                src={previewModalClip.url}
                controls
                autoPlay
                loop
                className="w-full h-full object-cover"
              />
            </div>

            <div className="w-full flex gap-2">
              <button
                onClick={() => {
                  handleUseInFactory(previewModalClip);
                  setPreviewModalClip(null);
                }}
                className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-red-600/30"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isAr ? 'اعتماد هذا المقطع للإنتاج' : 'Select Clip for Production'}</span>
              </button>
              <a
                href={previewModalClip.url}
                download={previewModalClip.filename}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs flex items-center justify-center"
              >
                <Download className="w-4 h-4" />
              </a>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
