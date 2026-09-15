import React, { useState, useEffect } from 'react';
import { 
  Flame, 
  Search, 
  Globe2, 
  Filter, 
  Sparkles, 
  Eye, 
  TrendingUp, 
  Play, 
  Layers, 
  RefreshCw,
  ExternalLink,
  Dice5,
  Send,
  Zap,
  CheckCircle2
} from 'lucide-react';
import ViralDnaModal from './ViralDnaModal.jsx';

export default function TrendRadar({ onRemakeVideo, isAr }) {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('US');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedVideoForDna, setSelectedVideoForDna] = useState(null);

  // Infinite Idea Vault State
  const [viewMode, setViewMode] = useState('trends'); // 'trends' | 'vault'
  const [infiniteIdeas, setInfiniteIdeas] = useState([]);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [publishingId, setPublishingId] = useState(null);
  const [quickPublishSuccess, setQuickPublishSuccess] = useState('');

  const regions = [
    { code: 'US', labelAr: '🌍 كوكب الأرض (Global - US)', labelEn: '🌍 Global (US)' },
    { code: 'EG', labelAr: '🇪🇬 الشرق الأوسط (مصر والعرب)', labelEn: '🇪🇬 Middle East (Egypt)' },
    { code: 'IN', labelAr: '🇮🇳 الهند (India)', labelEn: '🇮🇳 India' },
    { code: 'BR', labelAr: '🇧🇷 أمريكا اللاتينية (البرازيل)', labelEn: '🇧🇷 Brazil' },
    { code: 'JP', labelAr: '🇯🇵 شرق آسيا (اليابان)', labelEn: '🇯🇵 Japan' },
    { code: 'GB', labelAr: '🇬🇧 أوروبا (بريطانيا)', labelEn: '🇬🇧 UK' },
  ];

  const categories = [
    { id: 'all', labelAr: 'كل الفئات العالمية', labelEn: 'All Viral' },
    { id: 'challenges', labelAr: 'تحديات كبرى (MrBeast)', labelEn: 'High Stakes' },
    { id: 'science', labelAr: 'غرائب الكون والعلوم', labelEn: 'Cosmic & Science' },
    { id: 'magic', labelAr: 'خدع وإبهار صامت', labelEn: 'Visual Magic' },
    { id: 'experiments', labelAr: 'تجارب خارقة', labelEn: 'Experiments' },
    { id: 'shorts', labelAr: 'شورتس فيروسية', labelEn: 'Viral Shorts' },
  ];

  const fetchTrends = async (region = selectedRegion, category = selectedCategory) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/trends?region=${region}&category=${category}`);
      const data = await res.json();
      setTrends(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Fetch trends error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInfiniteIdeas = async (cat = selectedCategory) => {
    setLoadingIdeas(true);
    try {
      const res = await fetch(`/api/ideas/infinite?count=12&niche=${cat}`);
      const data = await res.json();
      setInfiniteIdeas(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Fetch ideas error:', err);
    } finally {
      setLoadingIdeas(false);
    }
  };

  const handleQuickPublish = async (idea) => {
    setPublishingId(idea.id);
    setQuickPublishSuccess('');
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: idea.titleAr,
          description: `شاهد كيف خضنا أشرس تجربة مع ${idea.titleAr}.\n\n#Viral #Trending #YouTube #Shorts`,
          tags: idea.tags.join(','),
          privacyStatus: 'public',
          categoryId: '24',
          isShort: false
        })
      });
      const data = await res.json();
      if (data.success) {
        setQuickPublishSuccess(`✅ تم نشر "${idea.titleAr.slice(0, 30)}..." تلقائياً على قناتك!`);
        setTimeout(() => setQuickPublishSuccess(''), 4000);
      }
    } catch (err) {
      alert('خطأ أثناء النشر: ' + err.message);
    } finally {
      setPublishingId(null);
    }
  };

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) {
      return fetchTrends(selectedRegion, selectedCategory);
    }

    setLoading(true);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}&region=${selectedRegion}`);
      const data = await res.json();
      setTrends(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends(selectedRegion, selectedCategory);
  }, [selectedRegion, selectedCategory]);

  useEffect(() => {
    if (viewMode === 'vault' && infiniteIdeas.length === 0) {
      fetchInfiniteIdeas(selectedCategory);
    }
  }, [viewMode]);

  return (
    <div className="space-y-8">
      
      {/* Hero Header Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-red-950/30 border border-slate-800 p-6 sm:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase tracking-wider mb-4">
            <Flame className="w-4 h-4 text-red-500 animate-bounce" />
            <span>{isAr ? 'رادار الفيديوهات الفيروسية الأكثر مشاهدة في الكون' : 'Cosmic Viral Video Radar'}</span>
          </div>
          
          <h1 className="text-2xl sm:text-4xl lg:text-5xl font-black text-white leading-tight tracking-tight">
            {isAr ? (
              <>
                اكتشف سر <span className="bg-gradient-to-r from-red-500 via-rose-400 to-amber-400 bg-clip-text text-transparent">الفيديوهات رقم 1</span> واستنسخ معادلتها لقناتك
              </>
            ) : (
              <>
                Uncover <span className="bg-gradient-to-r from-red-500 via-rose-400 to-amber-400 bg-clip-text text-transparent">World #1 Viral Formulas</span> & Clone Them
              </>
            )}
          </h1>

          <p className="mt-4 text-slate-300 text-sm sm:text-base leading-relaxed">
            {isAr 
              ? 'يبحث الرادار باستمرار في كافة أنحاء العالم ليرصد الفيديوهات التي تخطت الملايين في ساعات، يحلل سيكولوجية الـ 3 ثواني الأولى، ويفكك الهاشتاجات لتكرار نفس النجاح على قناتك.'
              : 'Our Cosmic Radar scans top global YouTube trends, deconstructs high-retention hooks, and decodes viral algorithms so your channel claims the #1 spot.'}
          </p>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="mt-6 flex flex-col sm:flex-row gap-2 max-w-2xl">
            <div className="relative flex-1">
              <Search className="absolute top-1/2 -translate-y-1/2 left-3.5 rtl:left-auto rtl:right-3.5 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={isAr ? 'ابحث عن أي فكرة أو ترند (مثل: تحدي الهروب، ثقب أسود، MrBeast)...' : 'Search any viral niche, topic, or keyword...'}
                className="w-full pl-11 rtl:pl-4 rtl:pr-11 pr-4 py-3.5 rounded-2xl bg-slate-950/80 border border-slate-700/80 text-white placeholder-slate-400 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 text-sm font-medium transition"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-sm shadow-lg shadow-red-600/30 transition flex items-center justify-center gap-2 shrink-0"
            >
              <Search className="w-4 h-4" />
              <span>{isAr ? 'بحث ورصد' : 'Scan & Spy'}</span>
            </button>
          </form>
        </div>
      </div>

      {/* Quick Success Toast */}
      {quickPublishSuccess && (
        <div className="p-3.5 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{quickPublishSuccess}</span>
        </div>
      )}

      {/* View Mode Switcher: Trends vs Infinite Vault */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-2 bg-slate-900/90 rounded-2xl border border-slate-800">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('trends')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black transition ${
              viewMode === 'trends'
                ? 'bg-red-600 text-white shadow-md shadow-red-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>{isAr ? '🔥 ترندات يوتيوب الحالية' : 'Live Global Trends'}</span>
          </button>

          <button
            onClick={() => {
              setViewMode('vault');
              if (infiniteIdeas.length === 0) fetchInfiniteIdeas(selectedCategory);
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black transition ${
              viewMode === 'vault'
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>{isAr ? '💎 خزنة ملايين الأفكار الفيروسية' : 'Infinite Million Ideas Vault'}</span>
          </button>
        </div>

        {viewMode === 'vault' && (
          <button
            onClick={() => fetchInfiniteIdeas(selectedCategory)}
            disabled={loadingIdeas}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600/30 hover:bg-purple-600 text-purple-300 hover:text-white border border-purple-500/40 text-xs font-bold transition disabled:opacity-50"
          >
            <Dice5 className={`w-4 h-4 ${loadingIdeas ? 'animate-spin' : ''}`} />
            <span>{isAr ? '🎲 توليد 12 فكرة مليارية جديدة' : 'Shuffle 12 New Ideas'}</span>
          </button>
        )}
      </div>

      {/* Filter Controls: Regions & Categories */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        
        {/* Categories Pills */}
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition ${
                selectedCategory === cat.id
                  ? 'bg-red-600 text-white shadow-md shadow-red-600/20'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700/90 border border-slate-700/60'
              }`}
            >
              {isAr ? cat.labelAr : cat.labelEn}
            </button>
          ))}
        </div>

        {/* Region Selector */}
        <div className="flex items-center gap-2 shrink-0 w-full md:w-auto justify-end">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5">
            <Globe2 className="w-4 h-4 text-red-400" />
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="bg-transparent text-xs font-bold text-slate-200 focus:outline-none cursor-pointer"
            >
              {regions.map((reg) => (
                <option key={reg.code} value={reg.code} className="bg-slate-900 text-white">
                  {isAr ? reg.labelAr : reg.labelEn}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => fetchTrends(selectedRegion, selectedCategory)}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700/60 transition"
            title={isAr ? 'تحديث الرادار' : 'Refresh'}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-red-400' : ''}`} />
          </button>
        </div>

      </div>

      {/* Content Grid: Trends or Infinite Vault */}
      {viewMode === 'vault' ? (
        loadingIdeas ? (
          <div className="py-20 text-center space-y-4">
            <div className="w-12 h-12 mx-auto border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
            <p className="text-slate-400 font-semibold text-sm">
              {isAr ? 'جاري استخراج وتوليد أفكار مليارية جديدة من مصفوفة الملايين...' : 'Generating billion-view ideas from the viral matrix...'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {infiniteIdeas.map((idea) => (
              <div
                key={idea.id}
                className="group relative flex flex-col justify-between p-5 bg-slate-900/90 rounded-2xl border border-slate-800 hover:border-purple-500/60 shadow-lg hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-300 space-y-4"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-black uppercase">
                      {idea.niche} • {idea.viralScore}% {isAr ? 'فيروسي' : 'Viral'}
                    </span>
                    <span className="text-[10px] font-bold font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      ~{idea.predictedViews} {isAr ? 'مشاهدة' : 'Views'}
                    </span>
                  </div>

                  <h3 className="text-sm font-black text-white group-hover:text-purple-300 transition leading-snug">
                    {idea.titleAr}
                  </h3>
                  <p className="text-xs text-slate-400 font-mono italic mt-1 line-clamp-1">
                    {idea.titleEn}
                  </p>

                  {/* 3s Hook Box */}
                  <div className="mt-3 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                    <span className="font-bold text-red-400 block text-[10px] uppercase mb-0.5">
                      ⚡ {isAr ? 'سر الخطاف البصري الصاعق (0-3s):' : '0-3s Hook Secret:'}
                    </span>
                    {idea.hook3s}
                  </div>

                  {/* Tags */}
                  <div className="mt-2.5 flex flex-wrap gap-1">
                    {idea.tags && Array.isArray(idea.tags) && idea.tags.slice(0, 4).map((t, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center gap-2">
                  <button
                    onClick={() => onRemakeVideo({ title: idea.titleAr })}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition flex items-center justify-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                    <span>{isAr ? 'صناعة السيناريو' : 'Full Script'}</span>
                  </button>

                  <button
                    onClick={() => handleQuickPublish(idea)}
                    disabled={publishingId === idea.id}
                    className="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs font-bold shadow-md shadow-red-600/20 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
                  >
                    <Send className={`w-3.5 h-3.5 ${publishingId === idea.id ? 'animate-bounce' : ''}`} />
                    <span>{publishingId === idea.id ? (isAr ? 'جاري النشر...' : 'Publishing...') : (isAr ? 'نشر فوري للقناة' : 'Publish')}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      ) : loading ? (
        <div className="py-20 text-center space-y-4">
          <div className="w-12 h-12 mx-auto border-4 border-red-500/20 border-t-red-500 rounded-full animate-spin"></div>
          <p className="text-slate-400 font-semibold text-sm">
            {isAr ? 'جاري مسح ترندات يوتيوب حول العالم وتحليل نسب المشاهدة...' : 'Scanning global viral trends...'}
          </p>
        </div>
      ) : trends.length === 0 ? (
        <div className="py-16 text-center bg-slate-900/60 rounded-2xl border border-slate-800 p-8">
          <Flame className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-200">
            {isAr ? 'لم يتم العثور على نتائج للبحث' : 'No viral trends found'}
          </h3>
          <p className="text-slate-400 text-xs mt-1">
            {isAr ? 'جرب البحث بكلمات أخرى أو اختر فئة مختلفة.' : 'Try another keyword or select a different category.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {trends.map((video) => (
            <div
              key={video.id}
              className="group relative flex flex-col bg-slate-900/90 rounded-2xl border border-slate-800 hover:border-red-500/50 shadow-lg hover:shadow-2xl hover:shadow-red-500/10 transition-all duration-300 overflow-hidden"
            >
              {/* Thumbnail Container */}
              <div className="relative aspect-video w-full overflow-hidden bg-slate-950">
                <img
                  src={video.thumbnail}
                  alt={video.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent"></div>

                {/* Viral Score Badge */}
                <div className="absolute top-3 left-3 rtl:left-auto rtl:right-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950/85 backdrop-blur-md border border-red-500/40 text-[11px] font-black text-red-400 shadow-md">
                  <Flame className="w-3.5 h-3.5 text-red-500" />
                  <span>{video.viralScore}% {isAr ? 'فيروسي' : 'Viral'}</span>
                </div>

                {/* Velocity Pill */}
                <div className="absolute bottom-3 right-3 rtl:right-auto rtl:left-3 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-[10px] font-bold text-amber-300 border border-amber-500/30">
                  {video.velocity}
                </div>
              </div>

              {/* Card Body */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2.5">
                    <img 
                      src={video.channelAvatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&auto=format&fit=crop&q=80'} 
                      alt="" 
                      className="w-6 h-6 rounded-full object-cover ring-1 ring-slate-700" 
                    />
                    <span className="text-xs font-bold text-slate-300 line-clamp-1">
                      {video.channelTitle}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white group-hover:text-red-400 transition line-clamp-2 leading-snug">
                    {video.title}
                  </h3>

                  {video.titleEn && video.titleEn !== video.title && (
                    <p className="mt-1 text-xs text-slate-400 line-clamp-1 italic font-mono">
                      {video.titleEn}
                    </p>
                  )}

                  {/* 3s Hook preview */}
                  <div className="mt-3 p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
                    <div className="text-[10px] font-black uppercase text-red-400 tracking-wider mb-1">
                      {isAr ? '⚡ سر خطاف البداية (0-3s)' : '⚡ 0-3s Hook'}
                    </div>
                    <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                      {video.hookBreakdown}
                    </p>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center gap-2">
                  <button
                    onClick={() => setSelectedVideoForDna(video)}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-bold border border-slate-700/60 transition flex items-center justify-center gap-1.5"
                  >
                    <Layers className="w-3.5 h-3.5 text-blue-400" />
                    <span>{isAr ? 'تحليل الـ DNA' : 'Analyze DNA'}</span>
                  </button>

                  <button
                    onClick={() => onRemakeVideo(video)}
                    className="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs font-bold shadow-md shadow-red-600/20 transition flex items-center justify-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{isAr ? 'استنساخ الفكرة' : 'Remake'}</span>
                  </button>
                </div>

              </div>
            </div>
          ))}
        </div>
      )}

      {/* DNA Modal */}
      {selectedVideoForDna && (
        <ViralDnaModal
          video={selectedVideoForDna}
          onClose={() => setSelectedVideoForDna(null)}
          onRemake={(v) => onRemakeVideo(v)}
          isAr={isAr}
        />
      )}

    </div>
  );
}
