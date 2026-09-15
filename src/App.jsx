import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import TrendRadar from './components/TrendRadar.jsx';
import ScriptStudio from './components/ScriptStudio.jsx';
import Publisher from './components/Publisher.jsx';
import SeoDominator from './components/SeoDominator.jsx';
import ChannelConnect from './components/ChannelConnect.jsx';
import AutoPilot from './components/AutoPilot.jsx';
import VideoSamplePlayer from './components/VideoSamplePlayer.jsx';
import FootageVault from './components/FootageVault.jsx';
import { 
  Flame, 
  Sparkles, 
  Video, 
  UploadCloud, 
  Hash, 
  Settings, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('trends');
  const [lang, setLang] = useState('ar');
  const [status, setStatus] = useState({
    connected: false,
    mode: 'demo',
    channel: null,
    hasApiKey: false,
    hasOAuth: false
  });

  const [scriptTopic, setScriptTopic] = useState('');
  const [publisherPrefill, setPublisherPrefill] = useState(null);
  const [notification, setNotification] = useState(null);

  const isAr = lang === 'ar';

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();

    // Check URL query for oauth callback message
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth') === 'success') {
      setNotification({
        type: 'success',
        text: isAr ? '🎉 تم ربط قناة اليوتيوب الرسمية بنجاح!' : 'Channel connected successfully!'
      });
      window.history.replaceState({}, document.title, window.location.pathname);
      fetchStatus();
    } else if (params.get('auth') === 'error') {
      setNotification({
        type: 'error',
        text: isAr ? `فشل الربط: ${params.get('msg') || ''}` : `Auth Error: ${params.get('msg') || ''}`
      });
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const toggleLang = () => {
    const nextLang = lang === 'ar' ? 'en' : 'ar';
    setLang(nextLang);
    document.documentElement.dir = nextLang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = nextLang;
  };

  const handleRemakeVideo = (video) => {
    setScriptTopic(video.title);
    setActiveTab('script');
  };

  const handleSendToPublisher = (data) => {
    setPublisherPrefill(data);
    setActiveTab('publisher');
  };

  return (
    <div className={`min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-red-500 selection:text-white ${isAr ? 'rtl' : 'ltr'}`}>
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        channelInfo={status.channel}
        isConnected={status.connected}
        mode={status.mode}
        lang={lang}
        toggleLang={toggleLang}
      />

      {/* Global Notification Banner */}
      {notification && (
        <div className={`p-3 text-center text-xs font-bold flex items-center justify-center gap-2 ${
          notification.type === 'success' 
            ? 'bg-emerald-600 text-white shadow-lg' 
            : 'bg-red-600 text-white shadow-lg'
        }`}>
          {notification.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{notification.text}</span>
          <button 
            onClick={() => setNotification(null)}
            className="mr-3 ml-3 text-white/80 hover:text-white underline cursor-pointer"
          >
            {isAr ? 'إغلاق' : 'Dismiss'}
          </button>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Dynamic Content by Tab */}
        {activeTab === 'trends' && (
          <TrendRadar 
            onRemakeVideo={handleRemakeVideo} 
            isAr={isAr} 
          />
        )}

        {activeTab === 'player' && (
          <VideoSamplePlayer 
            onPublishSample={(v) => fetchStatus()}
            isAr={isAr}
          />
        )}

        {activeTab === 'footage' && (
          <FootageVault 
            onSelectClipForFactory={(clip) => setActiveTab('player')}
            isAr={isAr}
          />
        )}

        {activeTab === 'script' && (
          <ScriptStudio 
            initialTopic={scriptTopic} 
            onSendToPublisher={handleSendToPublisher} 
            isAr={isAr} 
          />
        )}

        {activeTab === 'publisher' && (
          <Publisher 
            prefillData={publisherPrefill} 
            channelInfo={status.channel} 
            isConnected={status.connected} 
            isAr={isAr} 
          />
        )}

        {activeTab === 'seo' && (
          <SeoDominator 
            isAr={isAr} 
          />
        )}

        {activeTab === 'autopilot' && (
          <AutoPilot 
            isAr={isAr} 
          />
        )}

        {activeTab === 'connect' && (
          <ChannelConnect 
            channelInfo={status.channel} 
            isConnected={status.connected} 
            onChannelUpdated={fetchStatus} 
            isAr={isAr} 
          />
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-400">CosmicTube Engine</span>
            <span>•</span>
            <span>{isAr ? 'منظومة الذكاء الاصطناعي لاحتلال المركز رقم 1 في يوتيوب عالمياً' : 'Universal AI Engine for YouTube Domination'}</span>
          </div>
          <div className="flex items-center gap-4">
            <button onClick={() => setActiveTab('connect')} className="hover:text-red-400 transition">
              {isAr ? 'إعدادات الـ API' : 'API Settings'}
            </button>
            <span>•</span>
            <button onClick={() => setActiveTab('trends')} className="hover:text-red-400 transition">
              {isAr ? 'رادار الترند' : 'Trending Radar'}
            </button>
          </div>
        </div>
      </footer>

    </div>
  );
}
