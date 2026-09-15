import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Send, 
  Copy, 
  Check, 
  Clock, 
  Languages, 
  ImageIcon, 
  Zap, 
  Flame, 
  ChevronRight, 
  Share2,
  FileText,
  Target
} from 'lucide-react';

export default function ScriptStudio({ initialTopic, onSendToPublisher, isAr }) {
  const [topic, setTopic] = useState(initialTopic || '');
  const [category, setCategory] = useState('challenges');
  const [loading, setLoading] = useState(false);
  const [blueprint, setBlueprint] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);
  const [selectedLangTab, setSelectedLangTab] = useState('english');

  const presetTopics = [
    { labelAr: 'تحدي البقاء 7 أيام في غرفة مغلقة', labelEn: '7 Days in a White Room', cat: 'challenges' },
    { labelAr: 'ماذا لو اصطدم كويكب ذهبي بالأرض؟', labelEn: 'What if Gold Asteroid hit Earth?', cat: 'science' },
    { labelAr: 'بنيت ملجأ سري خارق بمليون دولار', labelEn: 'Built $1M Secret Bunker', cat: 'challenges' },
    { labelAr: 'أقوى خدعة بصرية بدون أي كلام', labelEn: 'Optical Illusion with No Words', cat: 'magic' },
  ];

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const generateBlueprint = async (topicToUse = topic, catToUse = category) => {
    if (!topicToUse || !topicToUse.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/generate-blueprint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topicToUse, category: catToUse })
      });
      const data = await res.json();
      setBlueprint(data);
    } catch (err) {
      console.error('Failed to generate blueprint:', err);
    } finally {
      setLoading(false);
    }
  };

  // If initialTopic changes from parent (e.g. clicking Remake from radar)
  useEffect(() => {
    if (initialTopic) {
      setTopic(initialTopic);
      generateBlueprint(initialTopic, category);
    }
  }, [initialTopic]);

  // Initial generation on first mount if empty
  useEffect(() => {
    if (!blueprint && !topic) {
      const defaultTopic = 'أشرس تحدي بقاء في العالم مع جوائز ضخمة';
      setTopic(defaultTopic);
      generateBlueprint(defaultTopic, 'challenges');
    }
  }, []);

  return (
    <div className="space-y-8">
      
      {/* Studio Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-red-950/40 border border-slate-800 shadow-xl">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase mb-3">
            <Sparkles className="w-4 h-4 text-red-500" />
            <span>{isAr ? 'استوديو صياغة المحتوى الكوني رقم 1' : 'Universal Viral Script & Storyboard Studio'}</span>
          </div>
          <h2 className="text-xl sm:text-3xl font-black text-white">
            {isAr 
              ? 'حوّل أي فكرة إلى سيناريو متفجر بنسبة احتفاظ خرافية' 
              : 'Turn Any Idea into a High-Retention Viral Production Package'}
          </h2>
          <p className="mt-2 text-slate-300 text-sm">
            {isAr 
              ? 'يقوم المحرك بصياغة خطاف الـ 3 ثواني الأولى، تسلسل الأحداث السريع، 5 عناوين خارقة للـ CTR، وأفكار الثمبنيل وحزم اللغات العالمية.' 
              : 'Our system drafts opening hooks, rapid-paced storyboards, 5 high-CTR titles, thumbnail concepts, and multi-lingual global metadata.'}
          </p>

          {/* Quick Presets */}
          <div className="mt-4 flex flex-wrap gap-2 items-center">
            <span className="text-xs text-slate-400 font-semibold">{isAr ? 'أفكار سريعة:' : 'Quick Ideas:'}</span>
            {presetTopics.map((p, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setTopic(isAr ? p.labelAr : p.labelEn);
                  setCategory(p.cat);
                  generateBlueprint(isAr ? p.labelAr : p.labelEn, p.cat);
                }}
                className="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition"
              >
                {isAr ? p.labelAr : p.labelEn}
              </button>
            ))}
          </div>

          {/* Input & Form */}
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={isAr ? 'اكتب فكرة الفيديو أو موضوعه بالتفصيل...' : 'Type your video topic or challenge...'}
              className="flex-1 px-4 py-3.5 rounded-2xl bg-slate-950 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-red-500 text-sm font-medium"
            />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-4 py-3.5 rounded-2xl bg-slate-950 border border-slate-700 text-slate-200 text-sm font-bold focus:outline-none focus:border-red-500 cursor-pointer"
            >
              <option value="challenges">{isAr ? 'أسلوب MrBeast (تحديات وجوائز)' : 'MrBeast Style'}</option>
              <option value="science">{isAr ? 'أسلوب Kurzgesagt (علوم وغرائب)' : 'Kurzgesagt Style'}</option>
              <option value="magic">{isAr ? 'أسلوب صامت ومبهر (Zach King)' : 'Silent Visual Magic'}</option>
              <option value="experiments">{isAr ? 'تجارب وحرف خارقة' : 'Extreme Experiments'}</option>
              <option value="shorts">{isAr ? 'شورتس وسوشيال ميديا' : 'Viral Shorts'}</option>
            </select>
            <button
              onClick={() => generateBlueprint(topic, category)}
              disabled={loading || !topic.trim()}
              className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-sm shadow-lg shadow-red-600/30 transition flex items-center justify-center gap-2 shrink-0 disabled:opacity-50"
            >
              <Sparkles className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? (isAr ? 'جاري الهندسة...' : 'Generating...') : (isAr ? 'توليد المخطط الكوني' : 'Generate Blueprint')}</span>
            </button>
          </div>
        </div>
      </div>

      {blueprint && (
        <div className="space-y-8 animate-fadeIn">
          
          {/* Section 1: High CTR Titles */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
                  <Flame className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-white">
                    {isAr ? 'أقوى 5 عناوين خارقة لمعدل النقر (CTR Formulas)' : 'Top 5 High-CTR Title Formulas'}
                  </h3>
                  <p className="text-xs text-slate-400">
                    {isAr ? 'مصممة وفق دراسات سيكولوجية الفضول لإجبار المشاهد على النقر' : 'Engineered to maximize CTR & trigger high YouTube browse impressions'}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {blueprint.titles.map((t, idx) => (
                <div 
                  key={idx}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-amber-500/40 transition gap-3"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 rounded text-[10px] font-black bg-amber-500/20 text-amber-400 border border-amber-500/30">
                        {t.predictedCtr} متوقع CTR
                      </span>
                      <span className="text-xs text-slate-400 font-medium">
                        {t.style}
                      </span>
                    </div>
                    <div className="text-sm font-bold text-white leading-snug">
                      {isAr ? t.titleAr : t.titleEn}
                    </div>
                    {t.titleEn && isAr && (
                      <div className="text-xs text-slate-400 italic mt-0.5 font-mono">
                        {t.titleEn}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleCopy(isAr ? t.titleAr : t.titleEn, `title-${idx}`)}
                      className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 text-xs font-semibold flex items-center gap-1 transition"
                      title="نسخ العنوان"
                    >
                      {copiedKey === `title-${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={() => onSendToPublisher({
                        title: isAr ? t.titleAr : t.titleEn,
                        description: blueprint.multiLanguagePack?.arabic?.description || '',
                        tags: blueprint.tagsString
                      })}
                      className="px-3 py-1.5 rounded-lg bg-red-600/30 hover:bg-red-600 text-red-300 hover:text-white border border-red-500/40 text-xs font-bold transition flex items-center gap-1"
                    >
                      <Send className="w-3 h-3" />
                      <span>{isAr ? 'إرسال للنشر' : 'To Publisher'}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Retention Storyboard */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl">
            <div className="flex items-center gap-2 mb-6">
              <div className="p-2 rounded-xl bg-red-500/20 text-red-400">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-black text-white">
                  {isAr ? 'مخطط الاحتفاظ بالجمهور الزمني (Audience Retention Storyboard)' : 'Audience Retention Storyboard'}
                </h3>
                <p className="text-xs text-slate-400">
                  {isAr ? 'هندسة زمنية مقسمة بالثواني تضمن بقاء المشاهد حتى اللحظة الأخيرة' : 'Engineered second-by-second pacing to destroy the 30-second drop-off'}
                </p>
              </div>
            </div>

            <div className="relative border-r-2 rtl:border-r-2 rtl:border-l-0 ltr:border-l-2 ltr:border-r-0 border-red-500/40 pr-6 rtl:pr-6 rtl:pl-0 ltr:pl-6 ltr:pr-0 space-y-6">
              {blueprint.storyboard.map((item, idx) => (
                <div key={idx} className="relative group">
                  {/* Timeline Node */}
                  <div className="absolute -right-[31px] rtl:-right-[31px] rtl:left-auto ltr:-left-[31px] ltr:right-auto top-1.5 w-4 h-4 rounded-full bg-red-500 ring-4 ring-slate-900 shadow-lg shadow-red-500/50"></div>

                  <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 group-hover:border-slate-700 transition space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-1 rounded-md text-xs font-black bg-red-500/20 text-red-400 border border-red-500/30">
                          {item.timestamp}
                        </span>
                        <h4 className="font-black text-white text-sm">
                          {item.stage}
                        </h4>
                      </div>
                      <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        {item.retentionGoal}
                      </span>
                    </div>

                    <div className="space-y-2 text-xs">
                      <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                        <span className="font-bold text-slate-400 block mb-0.5">{isAr ? '🎬 التوجيه البصري (Visual Direction):' : '🎬 Visual:'}</span>
                        <p className="text-slate-200 leading-relaxed">{item.visual}</p>
                      </div>

                      <div className="p-2.5 rounded-lg bg-red-950/30 border border-red-500/20">
                        <span className="font-bold text-red-400 block mb-0.5">{isAr ? '🎙️ الكلام والتعليق الصوتي (Voiceover / Script):' : '🎙️ Dialogue:'}</span>
                        <p className="text-slate-100 font-semibold leading-relaxed">"{isAr ? item.speechAr : item.speechEn}"</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Thumbnail Concepts */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
                <ImageIcon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-black text-white">
                  {isAr ? 'مفاهيم الصور المصغرة الخارقة (Thumbnail Blueprints)' : 'Viral Thumbnail Concepts'}
                </h3>
                <p className="text-xs text-slate-400">
                  {isAr ? '3 أفكار لتصميم صورة مصغرة لا يمكن تجاوزها في الصفحة الرئيسية' : '3 High-CTR Thumbnail Compositions to boost impressions'}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {blueprint.thumbnailConcepts.map((thumb) => (
                <div 
                  key={thumb.conceptNumber}
                  className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-purple-500/40 transition flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-black bg-purple-500/20 text-purple-400 border border-purple-500/30">
                        مفهوم {thumb.conceptNumber}
                      </span>
                      <span className="text-[10px] text-amber-400 font-mono font-bold bg-amber-500/10 px-1.5 py-0.5 rounded">
                        {thumb.textOnThumb}
                      </span>
                    </div>

                    <h4 className="font-bold text-white text-xs mb-2">
                      {thumb.title}
                    </h4>

                    <p className="text-xs text-slate-300 leading-relaxed mb-3">
                      {thumb.layout}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 italic">
                    💡 {thumb.whyItWorks}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Multi-Language Global Pack */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                  <Languages className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-white">
                    {isAr ? 'حزمة اللغات العالمية (Global Multi-Language Audio & Metadata)' : 'Global Multi-Language Pack'}
                  </h3>
                  <p className="text-xs text-slate-400">
                    {isAr ? 'عناوين وأوصاف مترجمة فوراً لـ 8 لغات كبرى لغزو كوكب الأرض بالكامل' : 'Instant localization for the world\'s largest viewing markets'}
                  </p>
                </div>
              </div>
            </div>

            {/* Language tabs */}
            <div className="flex flex-wrap gap-1.5 mb-4 p-1.5 bg-slate-950 rounded-xl border border-slate-800">
              {Object.keys(blueprint.multiLanguagePack).map((langKey) => (
                <button
                  key={langKey}
                  onClick={() => setSelectedLangTab(langKey)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition ${
                    selectedLangTab === langKey
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  {langKey}
                </button>
              ))}
            </div>

            {/* Selected Language Content */}
            {blueprint.multiLanguagePack[selectedLangTab] && (
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-400 uppercase">
                      {isAr ? 'العنوان المترجم' : 'Localized Title'}
                    </span>
                    <button
                      onClick={() => handleCopy(blueprint.multiLanguagePack[selectedLangTab].title, `lang-title-${selectedLangTab}`)}
                      className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-semibold"
                    >
                      {copiedKey === `lang-title-${selectedLangTab}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedKey === `lang-title-${selectedLangTab}` ? (isAr ? 'تم النسخ' : 'Copied') : (isAr ? 'نسخ' : 'Copy')}</span>
                    </button>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-bold text-sm">
                    {blueprint.multiLanguagePack[selectedLangTab].title}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-400 uppercase">
                      {isAr ? 'الوصف المترجم' : 'Localized Description'}
                    </span>
                    <button
                      onClick={() => handleCopy(blueprint.multiLanguagePack[selectedLangTab].description, `lang-desc-${selectedLangTab}`)}
                      className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-semibold"
                    >
                      {copiedKey === `lang-desc-${selectedLangTab}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedKey === `lang-desc-${selectedLangTab}` ? (isAr ? 'تم النسخ' : 'Copied') : (isAr ? 'نسخ' : 'Copy')}</span>
                    </button>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs leading-relaxed">
                    {blueprint.multiLanguagePack[selectedLangTab].description}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Quick Launch to Publisher Action Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 text-white flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
            <div>
              <h3 className="text-lg font-black">
                {isAr ? 'جاهز لرفع ونشر هذا الفيديو على القناة؟' : 'Ready to Publish & Upload This Video?'}
              </h3>
              <p className="text-xs text-red-100 mt-1">
                {isAr 
                  ? 'انقر لنقل العنوان، الوصف والهاشتاجات مباشرة إلى مركز النشر والرفع التلقائي.' 
                  : 'Transfer this title, optimized description, and viral tags straight to the Publisher.'}
              </p>
            </div>
            <button
              onClick={() => onSendToPublisher({
                title: blueprint.titles[0] ? (isAr ? blueprint.titles[0].titleAr : blueprint.titles[0].titleEn) : topic,
                description: `${blueprint.multiLanguagePack?.arabic?.description || ''}\n\n${blueprint.hashtagsString}`,
                tags: blueprint.tagsString
              })}
              className="px-6 py-3 rounded-xl bg-white text-red-600 hover:bg-slate-100 font-black text-sm shadow-lg transition flex items-center gap-2 shrink-0"
            >
              <Send className="w-4 h-4" />
              <span>{isAr ? 'الانتقال لمركز النشر فوراً' : 'Go to Smart Publisher'}</span>
            </button>
          </div>

        </div>
      )}

    </div>
  );
}
