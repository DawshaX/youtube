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
  Video,
  Cpu,
  RefreshCw,
  Film,
  Download,
  FlameKindling
} from 'lucide-react';

export default function VideoSamplePlayer({ onPublishSample, isAr }) {
  const [producedVideos, setProducedVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [availableTopics, setAvailableTopics] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState('ep1');

  // Production State
  const [producing, setProducing] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [publishMessage, setPublishMessage] = useState('');
  const [publishing, setPublishing] = useState(false);

  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const fetchProducedVideos = async () => {
    try {
      const res = await fetch('/api/factory/videos');
      const data = await res.json();
      if (Array.isArray(data)) {
        setProducedVideos(data);
        if (data.length > 0 && !selectedVideo) {
          setSelectedVideo(data[0]);
        }
      }
    } catch (err) {
      console.error('Fetch factory videos error:', err);
    }
  };

  const fetchTopics = async () => {
    try {
      const res = await fetch('/api/factory/topics');
      const data = await res.json();
      if (Array.isArray(data)) {
        setAvailableTopics(data);
      }
    } catch (err) {
      console.error('Fetch factory topics error:', err);
    }
  };

  useEffect(() => {
    fetchProducedVideos();
    fetchTopics();
  }, []);

  const handleStartProduce = async () => {
    setProducing(true);
    setCurrentJob({ progress: 10, stage: 'جاري تشغيل مصنع المونتاج 2099...' });
    setPublishMessage('');

    try {
      const res = await fetch('/api/factory/produce', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topicId: selectedTopicId })
      });
      const data = await res.json();
      if (data.success && data.job) {
        const jobId = data.job.jobId;
        // Poll for progress
        const poll = setInterval(async () => {
          try {
            const jRes = await fetch(`/api/factory/job/${jobId}`);
            const jData = await jRes.json();
            setCurrentJob(jData);

            if (jData.status === 'completed') {
              clearInterval(poll);
              setProducing(false);
              fetchProducedVideos();
              if (jData.outputVideo) {
                setSelectedVideo(jData.outputVideo);
              }
            } else if (jData.status === 'error') {
              clearInterval(poll);
              setProducing(false);
              alert('حدث خطأ أثناء الإنتاج: ' + jData.error);
            }
          } catch (e) {
            clearInterval(poll);
            setProducing(false);
          }
        }, 2000);
      }
    } catch (err) {
      setProducing(false);
      alert('فشل تشغيل المصنع: ' + err.message);
    }
  };

  const handlePublishToYouTube = async () => {
    if (!selectedVideo) return;
    setPublishing(true);
    setPublishMessage('');
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: selectedVideo.title || 'حلقة إنتاجية كوني 2099',
          description: `شاهد أحدث إنتاجات استوديو 2099 بدقة 1080×1920 وبمؤثرات بصرية وصوتية متطورة.\n\n#Viral #Shorts #YouTube #2099 #XDAWNOVA`,
          tags: 'shorts, viral, 2099, مونتاج, حقائق, علوم, فضاء',
          privacyStatus: 'public',
          categoryId: '28',
          isShort: true
        })
      });
      const data = await res.json();
      if (data.success) {
        setPublishMessage(isAr ? '🎉 تم رفع ونشر الفيديو الحقيقي على قناتك بنجاح!' : 'Published real video to YouTube channel!');
        if (onPublishSample) onPublishSample(data);
      }
    } catch (err) {
      alert('فشل النشر: ' + err.message);
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Studio Header Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-red-950 via-slate-900 to-purple-950 border border-slate-800 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/40 text-red-400 text-xs font-black uppercase mb-3">
              <Cpu className="w-4 h-4 text-red-500 animate-pulse" />
              <span>{isAr ? 'مصنع إنتاج ومونتاج الفيديوهات الكوني 2099 (Autonomous Video Factory)' : 'Cosmic 2099 Video Factory'}</span>
            </div>
            <h2 className="text-xl sm:text-3xl font-black text-white leading-tight">
              {isAr ? 'مصنع حقيقي متكامل لتوليد ومونتاج ونشر فيديوهات MP4 احترافية' : 'Full Autonomous Video Synthesis & 2099 Montage Factory'}
            </h2>
            <p className="text-slate-300 text-xs sm:text-sm mt-2 max-w-2xl leading-relaxed">
              {isAr 
                ? 'مدمج ومطور من مستودعاتك (XTreNDAW و daousha): يكتب السيناريو، يولد الصوت والمؤثرات، يرسم المشاهد النيونية، يدمج كينيتيك كابشنز كاريوكي، ويجمع فيديو MP4 حقيقي بأبعاد 1080×1920 جاهز للرفع على يوتيوب!'
                : 'Directly synthesizes H.264 1080x1920 MP4 clips with kinetic karaoke captions, brand neon masks, neural audio, and FFmpeg assembly.'}
            </p>
          </div>

          {/* Quick Produce Action Card */}
          <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-3 shrink-0 lg:max-w-xs w-full">
            <span className="text-xs font-bold text-slate-300 block">{isAr ? 'اختر الموضوع للإنتاج:' : 'Select Topic to Produce:'}</span>
            <select
              value={selectedTopicId}
              onChange={(e) => setSelectedTopicId(e.target.value)}
              className="w-full bg-slate-900 text-white text-xs font-bold p-2.5 rounded-xl border border-slate-700 focus:outline-none focus:border-red-500"
            >
              {availableTopics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id}: {t.title_ar}
                </option>
              ))}
            </select>

            <button
              onClick={handleStartProduce}
              disabled={producing}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-xs shadow-lg shadow-red-600/30 transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Sparkles className={`w-4 h-4 ${producing ? 'animate-spin' : ''}`} />
              <span>{producing ? (isAr ? 'المصنع قيد التشغيل...' : 'Rendering 2099 Video...') : (isAr ? 'إنتاج حلقة MP4 جديدة الآن 🎬' : 'Produce New Video Now 🎬')}</span>
            </button>
          </div>
        </div>

        {/* Live Job Progress Bar */}
        {producing && currentJob && (
          <div className="mt-6 p-4 rounded-2xl bg-slate-950/80 border border-red-500/40 space-y-2 animate-fadeIn">
            <div className="flex justify-between items-center text-xs font-bold text-white">
              <span className="flex items-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-red-500" />
                <span>{currentJob.stage}</span>
              </span>
              <span className="font-mono text-amber-400">{currentJob.progress}%</span>
            </div>
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-red-600 via-rose-500 to-amber-400 transition-all duration-300"
                style={{ width: `${currentJob.progress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {/* Main Video Screen & Gallery Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Columns: Video Player */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-4 sm:p-6 rounded-3xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Video className="w-5 h-5 text-red-500" />
                <h3 className="text-base font-black text-white">
                  {selectedVideo?.title || 'معاينة الفيديو الناتج'}
                </h3>
              </div>

              {selectedVideo?.sizeMB && (
                <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                  {selectedVideo.sizeMB} MB • 1080×1920 (9:16)
                </span>
              )}
            </div>

            {/* Real Video Player Container */}
            <div className="relative aspect-[9/16] max-w-sm mx-auto rounded-3xl overflow-hidden bg-black border-2 border-slate-700 shadow-2xl flex items-center justify-center">
              {selectedVideo?.url ? (
                <video
                  ref={videoRef}
                  src={selectedVideo.url}
                  controls
                  autoPlay
                  loop
                  playsInline
                  className="w-full h-full object-cover"
                ></video>
              ) : (
                <div className="text-center p-8 text-slate-500 space-y-2">
                  <Video className="w-12 h-12 mx-auto text-slate-600" />
                  <p className="text-xs">{isAr ? 'لا يوجد فيديو محدد حالياً' : 'No video selected'}</p>
                </div>
              )}
            </div>

            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-800">
              {selectedVideo?.url && (
                <a
                  href={selectedVideo.url}
                  download={selectedVideo.filename}
                  className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4 text-blue-400" />
                  <span>{isAr ? 'تحميل ملف MP4' : 'Download MP4'}</span>
                </a>
              )}

              <button
                onClick={handlePublishToYouTube}
                disabled={publishing || !selectedVideo}
                className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-xs shadow-lg shadow-red-600/30 transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Send className={`w-4 h-4 ${publishing ? 'animate-bounce' : ''}`} />
                <span>{publishing ? (isAr ? 'جاري الرفع والنشر...' : 'Publishing...') : (isAr ? 'نشر هذا الفيديو الآن على YouTube' : 'Publish to YouTube')}</span>
              </button>
            </div>

            {publishMessage && (
              <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{publishMessage}</span>
              </div>
            )}

          </div>
        </div>

        {/* Right 1 Column: Produced Videos Archive */}
        <div className="space-y-4">
          <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Film className="w-5 h-5 text-purple-400" />
                <h3 className="text-sm font-black text-white">
                  {isAr ? 'مكتبة الفيديوهات المنتجة (MP4 Factory)' : 'Factory Output Gallery'}
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {producedVideos.length} {isAr ? 'فيديو' : 'videos'}
              </span>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {producedVideos.map((v) => (
                <div
                  key={v.id}
                  onClick={() => setSelectedVideo(v)}
                  className={`p-3 rounded-2xl border transition cursor-pointer flex gap-3 items-center ${
                    selectedVideo?.id === v.id
                      ? 'bg-slate-800 border-red-500/70 shadow-md ring-1 ring-red-500/40'
                      : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="w-16 aspect-[9/16] rounded-xl overflow-hidden bg-black border border-slate-800 flex items-center justify-center shrink-0">
                    <Video className="w-6 h-6 text-red-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-bold text-white line-clamp-1">{v.title}</h4>
                    <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-2 font-mono">
                      <span>{v.sizeMB} MB</span>
                      <span>•</span>
                      <span>{new Date(v.createdAt).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
