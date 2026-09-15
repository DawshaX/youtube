import React, { useState } from 'react';
import { 
  Hash, 
  Copy, 
  Check, 
  Sparkles, 
  Search, 
  TrendingUp, 
  ShieldCheck, 
  Award,
  ListOrdered
} from 'lucide-react';

export default function SeoDominator({ isAr }) {
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [seoResult, setSeoResult] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);

  const defaultPresets = [
    'تحديات',
    'mrbeast challenge',
    'غرائب الكون والفيزياء',
    'خدع بصرية',
    'تجارب علمية كبرى',
    'shorts'
  ];

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleGenerate = async (k = keyword) => {
    if (!k || !k.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/extract-tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: k })
      });
      const data = await res.json();
      setSeoResult(data);
    } catch (err) {
      console.error('Failed to extract tags:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Header Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-red-950/40 border border-slate-800 shadow-xl">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase mb-2">
            <Hash className="w-4 h-4 text-red-500" />
            <span>{isAr ? 'مولد الهاشتاجات وسيو تصدر اليوتيوب' : 'YouTube SEO & Hashtag Dominator'}</span>
          </div>
          <h2 className="text-xl sm:text-3xl font-black text-white">
            {isAr ? 'هيمن على نتائج البحث وخوارزمية يوتيوب باحترافية' : 'Dominate YouTube Search & Recommendation Feeds'}
          </h2>
          <p className="text-slate-300 text-sm mt-2">
            {isAr 
              ? 'استخرج أقوى 30 كلمة مفتاحية تنافسية وهاشتاجات الترند لأي موضوع أو نيتش، جاهزة للنسخ المباشر إلى YouTube Studio.'
              : 'Extract top 30 viral tags & hashtags optimized for maximum algorithmic distribution.'}
          </p>

          {/* Presets */}
          <div className="mt-4 flex flex-wrap gap-2 items-center">
            <span className="text-xs text-slate-400 font-semibold">{isAr ? 'أمثلة شائعة:' : 'Quick Niches:'}</span>
            {defaultPresets.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setKeyword(preset);
                  handleGenerate(preset);
                }}
                className="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition"
              >
                {preset}
              </button>
            ))}
          </div>

          {/* Search Bar */}
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute top-1/2 -translate-y-1/2 left-3.5 rtl:left-auto rtl:right-3.5 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder={isAr ? 'اكتب الكلمة المفتاحية أو مجال الفيديو...' : 'Type niche or keyword (e.g., survival challenge, space, ai)...'}
                className="w-full pl-11 rtl:pl-4 rtl:pr-11 pr-4 py-3.5 rounded-2xl bg-slate-950 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-red-500 text-sm font-medium"
              />
            </div>
            <button
              onClick={() => handleGenerate(keyword)}
              disabled={loading || !keyword.trim()}
              className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-sm shadow-lg shadow-red-600/30 transition flex items-center justify-center gap-2 shrink-0 disabled:opacity-50"
            >
              <Sparkles className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? (isAr ? 'جاري الاستخراج...' : 'Extracting...') : (isAr ? 'استخراج أقوى الكلمات' : 'Generate Tags')}</span>
            </button>
          </div>
        </div>
      </div>

      {seoResult && (
        <div className="space-y-6">
          
          {/* Top Score Banner */}
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-black text-lg border border-emerald-500/30">
                {seoResult.seoScore}%
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">
                  {isAr ? 'قوة الـ SEO والانتشار الخوارزمي' : 'Algorithmic Optimization Score'}
                </h4>
                <p className="text-xs text-slate-400">
                  {isAr ? 'مزيج مثالي بين الكلمات العريضة وشديدة التحديد لتحفيز محرك الاقتراحات' : 'Optimized mix of broad search tags & algorithmic trigger hooks'}
                </p>
              </div>
            </div>

            <button
              onClick={() => handleCopy(seoResult.tagsString, 'all-tags')}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-xs shadow-lg shadow-red-600/20 transition flex items-center gap-2 shrink-0"
            >
              {copiedKey === 'all-tags' ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
              <span>{copiedKey === 'all-tags' ? (isAr ? 'تم نسخ جميع الوسوم!' : 'Copied All!') : (isAr ? 'نسخ كافة الوسوم لـ YouTube Studio' : 'Copy All for YouTube Studio')}</span>
            </button>
          </div>

          {/* Hashtags Section */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-red-500" />
                <h3 className="text-sm font-bold text-white">
                  {isAr ? 'الهاشتاجات الترند (ضع أول 3 في سطر الوصف الأول)' : 'Trending Hashtags'}
                </h3>
              </div>
              <button
                onClick={() => handleCopy(seoResult.hashtagsString, 'hashtags')}
                className="text-xs text-red-400 hover:text-red-300 font-semibold flex items-center gap-1"
              >
                {copiedKey === 'hashtags' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedKey === 'hashtags' ? (isAr ? 'تم النسخ' : 'Copied') : (isAr ? 'نسخ الهاشتاجات' : 'Copy Hashtags')}</span>
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {seoResult.hashtags.map((ht, idx) => (
                <span
                  key={idx}
                  onClick={() => handleCopy(ht, `ht-${idx}`)}
                  className="px-3 py-1.5 rounded-xl bg-slate-950 text-red-400 border border-red-500/20 hover:border-red-500/60 font-mono text-xs font-bold cursor-pointer transition"
                >
                  {ht}
                </span>
              ))}
            </div>
          </div>

          {/* Tags Cloud */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-white">
                  {isAr ? 'سحابة الكلمات المفتاحية (30 Tag عالي الأداء)' : 'Top 30 High-Ranking Tags'}
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {seoResult.tags.length} / 30 {isAr ? 'كلمة' : 'tags'}
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {seoResult.tags.map((tag, idx) => (
                <span
                  key={idx}
                  onClick={() => handleCopy(tag, `tag-${idx}`)}
                  className="px-3 py-1.5 rounded-xl bg-slate-950 text-slate-200 border border-slate-800 hover:border-slate-600 text-xs font-semibold cursor-pointer transition flex items-center gap-1.5"
                >
                  <span>{tag}</span>
                  {copiedKey === `tag-${idx}` && <Check className="w-3 h-3 text-emerald-400" />}
                </span>
              ))}
            </div>

            {/* Quick Box with raw comma separated text */}
            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono text-slate-400 select-all leading-relaxed">
              {seoResult.tagsString}
            </div>
          </div>

          {/* Actionable YouTube Algorithm Rules */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-bold text-white">
                {isAr ? 'نصائح خوارزمية يوتيوب لضمان تصدر الفيديو' : 'YouTube Algorithm Golden Rules'}
              </h3>
            </div>
            <div className="space-y-2">
              {seoResult.recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                  <div className="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <p>{rec}</p>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
