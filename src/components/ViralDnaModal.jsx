import React, { useState } from 'react';
import { 
  X, 
  Flame, 
  TrendingUp, 
  Eye, 
  ThumbsUp, 
  MessageSquare, 
  Zap, 
  Clock, 
  Copy, 
  Check, 
  Sparkles, 
  ArrowRight,
  ShieldAlert,
  Award
} from 'lucide-react';

export default function ViralDnaModal({ video, onClose, onRemake, isAr }) {
  const [copiedTags, setCopiedTags] = useState(false);

  if (!video) return null;

  const handleCopyTags = () => {
    const text = Array.isArray(video.tags) ? video.tags.join(', ') : video.tags;
    navigator.clipboard.writeText(text);
    setCopiedTags(true);
    setTimeout(() => setCopiedTags(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-3xl my-8 bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden">
        
        {/* Header Banner */}
        <div className="relative h-44 w-full bg-slate-950 overflow-hidden">
          <img 
            src={video.thumbnail} 
            alt={video.title} 
            className="w-full h-full object-cover opacity-30 filter blur-sm scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/60 to-transparent"></div>

          <button 
            onClick={onClose}
            className="absolute top-4 left-4 rtl:left-auto rtl:right-4 p-2 rounded-full bg-black/60 hover:bg-black/90 text-slate-300 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="absolute bottom-4 left-6 right-6 flex items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/20 text-red-400 text-xs font-bold border border-red-500/40 mb-2">
                <Flame className="w-3.5 h-3.5 text-red-500" />
                <span>{isAr ? `معدل انتشار كوني: ${video.viralScore}%` : `Viral Score: ${video.viralScore}%`}</span>
              </div>
              <h2 className="text-lg md:text-xl font-black text-white line-clamp-2">
                {video.title}
              </h2>
            </div>
            
            <button
              onClick={() => {
                onRemake(video);
                onClose();
              }}
              className="hidden sm:flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-sm shadow-lg shadow-red-600/30 transition shrink-0"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isAr ? 'استنساخ الفكرة للقناة' : 'Remake This Video'}</span>
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6">

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/60">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <Eye className="w-3.5 h-3.5 text-blue-400" />
                <span>{isAr ? 'المشاهدات' : 'Views'}</span>
              </div>
              <div className="text-base font-black text-white">
                {typeof video.views === 'number' ? video.views.toLocaleString() : video.views}
              </div>
            </div>

            <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/60">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <ThumbsUp className="w-3.5 h-3.5 text-emerald-400" />
                <span>{isAr ? 'الإعجابات' : 'Likes'}</span>
              </div>
              <div className="text-base font-black text-emerald-400">
                {typeof video.likes === 'number' ? video.likes.toLocaleString() : video.likes}
              </div>
            </div>

            <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/60">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                <span>{isAr ? 'سرعة الانتشار' : 'Velocity'}</span>
              </div>
              <div className="text-base font-black text-amber-300">
                {video.velocity}
              </div>
            </div>

            <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/60">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <Clock className="w-3.5 h-3.5 text-purple-400" />
                <span>{isAr ? 'تاريخ النشر' : 'Age'}</span>
              </div>
              <div className="text-base font-black text-purple-300">
                {isAr ? `منذ ${video.publishedDaysAgo} أيام` : `${video.publishedDaysAgo} days ago`}
              </div>
            </div>
          </div>

          {/* Retention Hook Secret */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-red-950/40 via-slate-800/60 to-slate-800/40 border border-red-500/30">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1 rounded-md bg-red-500/20 text-red-400">
                <Zap className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-white text-sm">
                {isAr ? 'تشريح خطاف الـ 3 ثواني الأولى (The 3-Second Hook)' : 'The 3-Second Hook Secret'}
              </h3>
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              {video.hookBreakdown}
            </p>
          </div>

          {/* Retention Secret & Pacing */}
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1 rounded-md bg-amber-500/20 text-amber-400">
                <Award className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-white text-sm">
                {isAr ? 'سر الاحتفاظ بالمشاهد (Audience Retention Secret)' : 'Retention & Pacing Strategy'}
              </h3>
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              {video.retentionSecret}
            </p>
          </div>

          {/* Viral Tags & Keywords */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                {isAr ? 'الكلمات المفتاحية والهاشتاجات المستخدمة' : 'Viral Tags & Keywords'}
              </span>
              <button
                onClick={handleCopyTags}
                className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 font-semibold transition"
              >
                {copiedTags ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedTags ? (isAr ? 'تم النسخ!' : 'Copied!') : (isAr ? 'نسخ الوسوم' : 'Copy Tags')}</span>
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5 p-3 bg-slate-950/70 rounded-xl border border-slate-800">
              {Array.isArray(video.tags) ? video.tags.map((tag, i) => (
                <span 
                  key={i}
                  className="px-2.5 py-1 text-xs rounded-lg bg-slate-800/80 text-slate-300 border border-slate-700 hover:border-slate-500 transition"
                >
                  #{tag}
                </span>
              )) : (
                <span className="text-xs text-slate-400">{video.tags}</span>
              )}
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 text-sm font-semibold transition"
            >
              {isAr ? 'إغلاق' : 'Close'}
            </button>
            <button
              onClick={() => {
                onRemake(video);
                onClose();
              }}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-sm shadow-lg shadow-red-600/30 transition"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isAr ? 'تحويل الفكرة إلى سيناريو كامل' : 'Create Script from This'}</span>
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}
