import React, { useState, useEffect, useRef } from 'react';
import { 
  UploadCloud, 
  Video, 
  ImageIcon, 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink, 
  Clock, 
  Globe, 
  Lock, 
  Link2, 
  Eye, 
  ThumbsUp, 
  Sparkles,
  PlaySquare,
  FileVideo,
  Layers,
  Download,
  Copy,
  Check
} from 'lucide-react';

export default function Publisher({ prefillData, channelInfo, isConnected, isAr }) {
  const [videoFile, setVideoFile] = useState(null);
  const [thumbnailFile, setThumbnailFile] = useState(null);
  const [thumbnailPreview, setThumbnailPreview] = useState(null);
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [privacyStatus, setPrivacyStatus] = useState('public');
  const [categoryId, setCategoryId] = useState('24'); // Entertainment
  const [isShort, setIsShort] = useState(false);

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const [publishedVideos, setPublishedVideos] = useState([]);
  const [latestProducedVideo, setLatestProducedVideo] = useState(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const fileInputRef = useRef(null);
  const thumbInputRef = useRef(null);

  // Apply prefilled data if passed from Script Studio
  useEffect(() => {
    if (prefillData) {
      if (prefillData.title) setTitle(prefillData.title);
      if (prefillData.description) setDescription(prefillData.description);
      if (prefillData.tags) setTags(prefillData.tags);
    }
  }, [prefillData]);

  // Load uploaded channel videos & factory videos
  const fetchUploadedVideos = async () => {
    try {
      const res = await fetch('/api/videos');
      const data = await res.json();
      if (Array.isArray(data)) {
        setPublishedVideos(data);
      }
    } catch (err) {
      console.error('Fetch videos error:', err);
    }
  };

  const fetchFactoryVideos = async () => {
    try {
      const res = await fetch('/api/factory/videos');
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        setLatestProducedVideo(data[0]);
      }
    } catch (err) {
      console.error('Fetch factory vids err:', err);
    }
  };

  useEffect(() => {
    fetchUploadedVideos();
    fetchFactoryVideos();
  }, []);

  const handleVideoSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      if (!title) {
        // Strip extension as default title
        const cleanName = file.name.replace(/\.[^/.]+$/, '');
        setTitle(cleanName);
      }
    }
  };

  const handleThumbSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setThumbnailFile(file);
      const url = URL.createObjectURL(file);
      setThumbnailPreview(url);
    }
  };

  const handlePublish = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setErrorMsg(isAr ? 'يرجى كتابة عنوان الفيديو أولاً' : 'Title is required');
      return;
    }

    setUploading(true);
    setUploadProgress(15);
    setErrorMsg('');
    setUploadResult(null);

    const formData = new FormData();
    if (videoFile) formData.append('video', videoFile);
    if (thumbnailFile) formData.append('thumbnail', thumbnailFile);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('tags', tags);
    formData.append('privacyStatus', privacyStatus);
    formData.append('categoryId', categoryId);
    formData.append('isShort', isShort);

    // Simulate progress while uploading
    const timer = setInterval(() => {
      setUploadProgress(prev => (prev < 90 ? prev + 15 : prev));
    }, 400);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      clearInterval(timer);
      setUploadProgress(100);

      if (data.success) {
        setUploadResult(data);
        fetchUploadedVideos();
        // Clear files
        setVideoFile(null);
        setThumbnailFile(null);
      } else {
        setErrorMsg(data.error || 'حدث خطأ أثناء محاولة الرفع');
      }
    } catch (err) {
      clearInterval(timer);
      setErrorMsg(err.message || 'فشل الاتصال بالخادم');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Top Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-red-950/40 border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase mb-2">
              <UploadCloud className="w-4 h-4 text-red-500" />
              <span>{isAr ? 'مركز النشر والرفع الآلي المباشر' : 'Smart YouTube Publisher'}</span>
            </div>
            <h2 className="text-xl sm:text-3xl font-black text-white">
              {isAr ? 'انشر فيديوهاتك على يوتيوب بأعلى مقاييس السيو' : 'Publish to Your Channel with Maximum SEO Optimization'}
            </h2>
            <p className="text-slate-400 text-xs sm:text-sm mt-1">
              {isConnected 
                ? (isAr ? 'متصل حالياً بقناتك الرسمية عبر YouTube API. النشر سيكون مباشراً وحقيقياً على القناة!' : 'Connected live to your official YouTube channel!')
                : (isAr ? 'النظام جاهز ومربوط في وضع التجهيز السريع. يمكنك رفع وحفظ الفيديوهات أو إدخال مفاتيح OAuth للرفع الحي المباشر.' : 'Ready mode active. Supports live publishing once OAuth keys are configured.')}
            </p>
          </div>

          <div className="flex items-center gap-2 p-2 bg-slate-950/80 rounded-2xl border border-slate-800 shrink-0">
            <img 
              src={channelInfo?.thumbnails?.default?.url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop&q=80'} 
              alt="Avatar" 
              className="w-10 h-10 rounded-xl object-cover ring-2 ring-red-500/40"
            />
            <div className="pr-2 rtl:pr-2 rtl:pl-0 ltr:pl-2 ltr:pr-0">
              <div className="text-xs font-bold text-white">{channelInfo?.title}</div>
              <div className="text-[10px] text-slate-400 font-mono">
                {typeof channelInfo?.statistics?.subscriberCount === 'string'
                  ? parseInt(channelInfo.statistics.subscriberCount).toLocaleString()
                  : channelInfo?.statistics?.subscriberCount} {isAr ? 'مشترك' : 'Subscribers'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Featured Ready-to-Upload Episode (e.g. MrBeast Challenge) */}
      {latestProducedVideo && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-red-950/60 via-slate-900 to-amber-950/30 border-2 border-red-500/40 shadow-2xl flex flex-col md:flex-row items-center gap-6">
          <div className="w-full md:w-48 aspect-[9/16] rounded-2xl overflow-hidden bg-black shrink-0 border border-red-500/30 shadow-lg relative group">
            <video
              src={latestProducedVideo.url}
              loop
              muted
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
            <div className="absolute top-2 right-2 px-2 py-0.5 rounded-md bg-red-600/90 text-white font-extrabold text-[9px]">
              MP4 1080×1920
            </div>
            <div className="absolute bottom-2 inset-x-2 text-center">
              <span className="px-2 py-0.5 rounded-md bg-black/80 text-amber-300 font-mono text-[10px]">
                {latestProducedVideo.sizeMB} MB
              </span>
            </div>
          </div>

          <div className="flex-1 space-y-3 text-right rtl:text-right ltr:text-left">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-xs font-bold">
              <CheckCircle2 className="w-4 h-4" />
              <span>{isAr ? 'حلقة التحدي الفيروسي جاهزة بالكامل بأعلى جودة' : 'Viral Challenge Episode Ready'}</span>
            </div>

            <h3 className="text-xl sm:text-2xl font-black text-white leading-tight">
              {latestProducedVideo.title}
            </h3>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {isAr 
                ? 'فيديو كامل بمشاهد فيديو حقيقية (نيران، أمطار أموال، عواصف، رادار طوارئ، كونفيتي فوز) + تعليق صوتي بشري حماسي + ساوند ديزاين احترافي وكابشنز حركية.'
                : 'Rendered with 100% fluid motion video clips, human voiceover, hype audio design, and kinetic ASS subtitles.'}
            </p>

            {/* Quick Actions Bar */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <a
                href={latestProducedVideo.url}
                download={latestProducedVideo.filename}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-xs sm:text-sm flex items-center gap-2 shadow-lg shadow-red-600/30 transition active:scale-95"
              >
                <Download className="w-4 h-4" />
                <span>{isAr ? 'تحميل الفيديو MP4 لجهازك' : 'Download MP4 File'}</span>
              </a>

              <button
                type="button"
                onClick={() => {
                  const metaText = `العنوان:\n${latestProducedVideo.title} #Shorts\n\nالوصف:\nتحدي مستر بيست الأسطوري: 4 متسابقين يتنافسون على 250,000 دولار كاش وسط عواصف ثلجية ونيران مشتعلة وإنذار طوارئ متسارع! من يصمد للنهاية؟\n\n#Viral #Trending #CosmicTube #Shorts #MrBeast\n\nالتاجات:\nShorts, MrBeast, تحدي_النقود, تحديات, BeastGames, كاش, CosmicTube, Viral`;
                  navigator.clipboard.writeText(metaText);
                  setCopiedAll(true);
                  setTimeout(() => setCopiedAll(false), 3000);
                }}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs sm:text-sm flex items-center gap-2 border border-slate-700 transition"
              >
                {copiedAll ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-slate-400" />}
                <span>{copiedAll ? (isAr ? 'تم نسخ كل البيانات!' : 'Copied!') : (isAr ? 'نسخ العنوان والوصف والتاجات' : 'Copy Title, Desc & Tags')}</span>
              </button>

              <a
                href="https://studio.youtube.com/channel/upload"
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2.5 rounded-xl bg-red-950/60 hover:bg-red-900/60 text-red-300 font-bold text-xs sm:text-sm flex items-center gap-2 border border-red-800/60 transition"
              >
                <ExternalLink className="w-4 h-4" />
                <span>{isAr ? 'فتح YouTube Studio للرفع فوراً' : 'Open YouTube Studio'}</span>
              </a>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
              💡 <strong className="text-slate-200">{isAr ? 'توضيح مهم للرفع الحي:' : 'Live Upload Note:'}</strong> {isAr 
                ? 'نظراً لأن بيئة السحاب مؤمنة وتمنع الاتصال المباشر بالإنترنت الخارجي لسيرفرات جوجل، يمكنك تحميل ملف الـ MP4 بنقرة واحدة ورفعه مباشرة على قناتك، أو تشغيل الكود محلياً على حاسوبك/سيرفرك الخاص (المربوط بـ GitHub) حيث سيعمل الرفع التلقائي المباشر عبر YouTube Data API v3 فوراً.'
                : 'Because the sandbox environment enforces strict outbound security firewalls, you can download the ready MP4 file and upload it via YouTube Studio, or run the project locally on your machine where YouTube API uploads stream live.'}
            </div>
          </div>
        </div>
      )}

      {/* Main Publishing Form Grid */}
      <form onSubmit={handlePublish} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Columns: Video & Metadata */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* File Upload Zone */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <h3 className="text-sm font-black text-white flex items-center gap-2">
              <FileVideo className="w-4 h-4 text-red-500" />
              <span>{isAr ? '1. ملف الفيديو (Video File)' : '1. Video File'}</span>
            </h3>

            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleVideoSelect} 
              accept="video/mp4,video/quicktime,video/webm,video/mkv" 
              className="hidden" 
            />

            <div 
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition ${
                videoFile 
                  ? 'border-emerald-500/60 bg-emerald-950/20' 
                  : 'border-slate-700 hover:border-red-500/60 hover:bg-slate-950/60'
              }`}
            >
              {videoFile ? (
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-bold text-white">{videoFile.name}</div>
                  <div className="text-xs text-slate-400">
                    {(videoFile.size / (1024 * 1024)).toFixed(2)} MB • {isAr ? 'انقر للتغيير' : 'Click to change'}
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center mx-auto">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-bold text-slate-200">
                    {isAr ? 'اسحب وأفلت ملف الفيديو هنا أو اضغط للاختيار' : 'Drag & drop video here or browse'}
                  </div>
                  <div className="text-xs text-slate-400">
                    MP4, WebM, MOV, MKV (حتى 500MB في بيئة العمل)
                  </div>
                </div>
              )}
            </div>

            {/* Shorts Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <PlaySquare className="w-4 h-4 text-red-400" />
                <span className="text-xs font-bold text-slate-200">
                  {isAr ? 'نشر كفيديو قصير (YouTube Shorts #Shorts)' : 'Publish as YouTube Shorts'}
                </span>
              </div>
              <input 
                type="checkbox"
                checked={isShort}
                onChange={(e) => setIsShort(e.target.checked)}
                className="w-4 h-4 rounded text-red-600 focus:ring-red-500 bg-slate-800 border-slate-700 cursor-pointer"
              />
            </div>
          </div>

          {/* Metadata Form */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <h3 className="text-sm font-black text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>{isAr ? '2. تفاصيل الفيديو والـ SEO' : '2. Video Metadata & SEO'}</span>
            </h3>

            {/* Title */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold text-slate-300">
                  {isAr ? 'عنوان الفيديو (Title)' : 'Video Title'}
                </label>
                <span className={`text-[10px] font-mono ${title.length > 100 ? 'text-red-400' : 'text-slate-400'}`}>
                  {title.length}/100
                </span>
              </div>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={isAr ? 'اكتب عنواناً جذاباً يخطف المشاهدين...' : 'Enter an irresistible high-CTR title...'}
                maxLength={100}
                required
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 text-sm font-bold"
              />
            </div>

            {/* Description */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold text-slate-300">
                  {isAr ? 'الوصف وسيو خوارزميات يوتيوب (Description)' : 'SEO Description'}
                </label>
                <span className="text-[10px] text-slate-400 font-mono">
                  {description.length}/5000
                </span>
              </div>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={isAr ? 'ضع تفاصيل الفيديو، الروابط، وأول 3 وسوم (#)...' : 'Include your video hook, chapter markers, and #hashtags...'}
                rows={4}
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 text-xs leading-relaxed"
              ></textarea>
            </div>

            {/* Tags */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold text-slate-300">
                  {isAr ? 'الكلمات المفتاحية مفصولة بفواصل (Tags)' : 'Tags (comma separated)'}
                </label>
                <span className="text-[10px] text-slate-400 font-mono">
                  {tags ? tags.split(',').filter(Boolean).length : 0} {isAr ? 'وسم' : 'tags'}
                </span>
              </div>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder={isAr ? 'تحديات, mrbeast, viral, غرائب, shorts...' : 'viral, challenge, experiment, explore...'}
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 text-xs"
              />
            </div>

            {/* Category & Privacy Settings */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  {isAr ? 'فئة الفيديو (Category)' : 'Category'}
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 text-xs font-semibold focus:outline-none focus:border-red-500 cursor-pointer"
                >
                  <option value="24">{isAr ? 'ترفيه وتحديات (Entertainment)' : 'Entertainment (24)'}</option>
                  <option value="28">{isAr ? 'علوم وتكنولوجيا (Science & Tech)' : 'Science & Tech (28)'}</option>
                  <option value="26">{isAr ? 'إرشادات وحيل (Howto & Style)' : 'Howto & Style (26)'}</option>
                  <option value="20">{isAr ? 'ألعاب (Gaming)' : 'Gaming (20)'}</option>
                  <option value="27">{isAr ? 'تعليم ومعرفة (Education)' : 'Education (27)'}</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  {isAr ? 'حالة الخصوصية (Visibility)' : 'Visibility'}
                </label>
                <select
                  value={privacyStatus}
                  onChange={(e) => setPrivacyStatus(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 text-xs font-semibold focus:outline-none focus:border-red-500 cursor-pointer"
                >
                  <option value="public">{isAr ? '🌍 علني للجميع (Public)' : 'Public'}</option>
                  <option value="unlisted">{isAr ? '🔗 غير مدرج (Unlisted)' : 'Unlisted'}</option>
                  <option value="private">{isAr ? '🔒 خاص للقناة (Private)' : 'Private'}</option>
                </select>
              </div>
            </div>

          </div>

        </div>

        {/* Right 1 Column: Thumbnail & YouTube Preview */}
        <div className="space-y-6">
          
          {/* Custom Thumbnail */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <h3 className="text-sm font-black text-white flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-purple-400" />
              <span>{isAr ? 'الصورة المصغرة (Thumbnail)' : 'Custom Thumbnail'}</span>
            </h3>

            <input 
              type="file" 
              ref={thumbInputRef} 
              onChange={handleThumbSelect} 
              accept="image/png,image/jpeg,image/webp" 
              className="hidden" 
            />

            <div 
              onClick={() => thumbInputRef.current?.click()}
              className="relative aspect-video rounded-xl overflow-hidden bg-slate-950 border-2 border-dashed border-slate-700 hover:border-purple-500 cursor-pointer flex items-center justify-center transition"
            >
              {thumbnailPreview ? (
                <img 
                  src={thumbnailPreview} 
                  alt="Thumbnail Preview" 
                  className="w-full h-full object-cover" 
                />
              ) : (
                <div className="text-center p-4">
                  <ImageIcon className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                  <span className="text-xs font-bold text-slate-300 block">
                    {isAr ? 'اضغط لاختيار صورة مصغرة' : 'Upload custom thumbnail'}
                  </span>
                  <span className="text-[10px] text-slate-500">1280x720 (16:9)</span>
                </div>
              )}
            </div>
          </div>

          {/* YouTube Card Simulation */}
          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="text-[10px] font-black uppercase tracking-wider text-slate-400">
              {isAr ? 'معاينة كيف سيظهر الفيديو للمشاهدين' : 'YouTube Feed Preview'}
            </div>

            <div className="rounded-xl overflow-hidden bg-slate-900 border border-slate-800 shadow-md">
              <div className="aspect-video w-full bg-slate-950 relative">
                {thumbnailPreview ? (
                  <img src={thumbnailPreview} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-slate-900 text-slate-600">
                    <Video className="w-10 h-10" />
                  </div>
                )}
                <span className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/80 text-[10px] font-bold text-white">
                  {isShort ? '0:45' : '10:15'}
                </span>
              </div>

              <div className="p-3">
                <h4 className="text-xs font-bold text-white line-clamp-2 leading-tight">
                  {title || (isAr ? 'عنوان الفيديو سيظهر هنا...' : 'Video title goes here...')}
                </h4>
                <div className="flex items-center gap-1.5 mt-2 text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300">{channelInfo?.title}</span>
                  <span>•</span>
                  <span>{isAr ? 'الآن' : 'Just now'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Submit Action */}
          <div className="space-y-3">
            {errorMsg && (
              <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {uploading && (
              <div className="space-y-1.5 p-3 rounded-xl bg-slate-900 border border-slate-800">
                <div className="flex justify-between text-xs font-bold text-slate-300">
                  <span>{isAr ? 'جاري الرفع والنشر عبر API...' : 'Uploading & Publishing...'}</span>
                  <span className="font-mono">{uploadProgress}%</span>
                </div>
                <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-red-600 to-rose-500 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {uploadResult && (
              <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{uploadResult.message}</span>
                </div>
                {uploadResult.video?.url && (
                  <a
                    href={uploadResult.video.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300 underline font-semibold mt-1"
                  >
                    <span>{isAr ? 'رابط الفيديو المنشور' : 'Video Link'}: {uploadResult.video.url}</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={uploading}
              className="w-full py-4 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-sm shadow-xl shadow-red-600/30 transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <UploadCloud className="w-5 h-5" />
              <span>{uploading ? (isAr ? 'جاري الرفع...' : 'Publishing...') : (isAr ? 'نشر الفيديو الآن على القناة' : 'Publish Video to YouTube')}</span>
            </button>
          </div>

        </div>

      </form>

      {/* Published Videos On The Channel */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PlaySquare className="w-5 h-5 text-red-500" />
            <h3 className="text-base font-black text-white">
              {isAr ? 'الفيديوهات المنشورة في القناة الكونية' : 'Uploaded Videos on Cosmic Channel'}
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {publishedVideos.length} {isAr ? 'فيديو' : 'videos'}
          </span>
        </div>

        {publishedVideos.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            {isAr ? 'لم يتم نشر أي فيديوهات بعد. استخدم النموذج أعلاه لرفع أول فيديو لقناتك العالمية!' : 'No videos published yet.'}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {publishedVideos.map((v) => (
              <div 
                key={v.id}
                className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition flex gap-3 items-center"
              >
                <div className="w-24 aspect-video rounded-lg overflow-hidden bg-slate-900 shrink-0">
                  <img src={v.thumbnailUrl} alt="" className="w-full h-full object-cover" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-white line-clamp-1">{v.title}</h4>
                  <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-2">
                    <span className="capitalize text-emerald-400 font-semibold">{v.privacyStatus}</span>
                    <span>•</span>
                    <span>{new Date(v.publishedAt).toLocaleDateString()}</span>
                  </div>
                  <a
                    href={v.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[10px] text-red-400 hover:text-red-300 font-mono mt-1"
                  >
                    <span>{v.url}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
