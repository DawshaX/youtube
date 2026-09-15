import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Key, 
  ShieldCheck, 
  ExternalLink, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  HelpCircle, 
  Lock, 
  Layers, 
  Radio, 
  Sliders,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function ChannelConnect({ channelInfo, isConnected, onChannelUpdated, isAr }) {
  const [apiKey, setApiKey] = useState('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [redirectUri, setRedirectUri] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [showGuide, setShowGuide] = useState(true);
  const [guideStep, setGuideStep] = useState(1);

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings');
      const data = await res.json();
      setApiKey(data.rawApiKey || '');
      setClientId(data.rawClientId || '');
      setRedirectUri(data.redirectUri || (window.location.origin + '/api/auth/callback'));
    } catch (err) {
      console.error('Fetch settings error:', err);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey,
          clientId,
          clientSecret,
          redirectUri
        })
      });
      const data = await res.json();
      if (data.success) {
        setMessage(isAr ? 'تم حفظ الإعدادات بنجاح!' : 'Settings saved successfully!');
        if (onChannelUpdated) onChannelUpdated();
      }
    } catch (err) {
      setMessage(isAr ? 'فشل حفظ الإعدادات' : 'Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const res = await fetch('/api/auth/url');
      const data = await res.json();
      if (data.success && data.url) {
        window.location.href = data.url;
      } else {
        alert(data.error || (isAr ? 'يرجى إدخال Client ID و Client Secret أولاً في النموذج أدناه.' : 'Please configure Client ID & Secret below first.'));
      }
    } catch (err) {
      alert(err.message || 'Error generating auth url');
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm(isAr ? 'هل أنت متأكد من إلغاء ربط القناة؟' : 'Are you sure you want to disconnect?')) return;
    try {
      const res = await fetch('/api/auth/disconnect', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        if (onChannelUpdated) onChannelUpdated();
      }
    } catch (err) {
      console.error('Disconnect error:', err);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Header Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-red-950/40 border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase mb-2">
              <Key className="w-4 h-4 text-red-500" />
              <span>{isAr ? 'مركز ربط القناة والـ API' : 'YouTube Channel & API Connect Hub'}</span>
            </div>
            <h2 className="text-xl sm:text-3xl font-black text-white">
              {isAr ? 'اربط قناتك بمفاتيح Google YouTube Data API v3' : 'Connect Your Channel with YouTube Data API v3'}
            </h2>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl">
              {isAr 
                ? 'يتيح لك الربط: البحث اللحظي في ترندات العالم عبر YouTube Search API، والنشر التلقائي ورفع الفيديوهات مباشرة لقناتك عبر YouTube Upload OAuth.'
                : 'Enables live YouTube search, trends analysis, and 1-click video publishing to your channel via official Google APIs.'}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-2">
            {isConnected ? (
              <button
                onClick={handleDisconnect}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-red-950/60 text-red-400 border border-slate-700 hover:border-red-500/50 text-xs font-bold transition"
              >
                {isAr ? 'إلغاء ربط القناة' : 'Disconnect Channel'}
              </button>
            ) : (
              <button
                onClick={handleConnectGoogle}
                className="px-5 py-3 rounded-xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-xs shadow-lg shadow-red-600/30 transition flex items-center gap-2"
              >
                <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
                <span>{isAr ? 'ربط القناة بحساب Google' : 'Connect with Google'}</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Channel Status Overview Card */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div className="flex items-center gap-4">
            <img 
              src={channelInfo?.thumbnails?.high?.url || channelInfo?.thumbnails?.default?.url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&auto=format&fit=crop&q=80'} 
              alt="Channel Banner" 
              className="w-16 h-16 rounded-2xl object-cover ring-2 ring-red-500/40 shadow-lg"
            />
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-black text-white">{channelInfo?.title}</h3>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  isConnected 
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}>
                  {isConnected ? (isAr ? 'قناة حية متصلة' : 'Live Channel Connected') : (isAr ? 'محرك القناة الكونية جاهز' : 'Cosmic Ready Mode')}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-md line-clamp-1">
                {channelInfo?.description}
              </p>
            </div>
          </div>
        </div>

        {/* Channel Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-6">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
            <span className="text-xs text-slate-400 font-semibold block mb-1">
              {isAr ? 'المشتركون (Subscribers)' : 'Subscribers'}
            </span>
            <span className="text-xl font-black text-white">
              {typeof channelInfo?.statistics?.subscriberCount === 'string'
                ? parseInt(channelInfo.statistics.subscriberCount).toLocaleString()
                : channelInfo?.statistics?.subscriberCount}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
            <span className="text-xs text-slate-400 font-semibold block mb-1">
              {isAr ? 'إجمالي المشاهدات (Views)' : 'Total Views'}
            </span>
            <span className="text-xl font-black text-emerald-400">
              {typeof channelInfo?.statistics?.viewCount === 'string'
                ? parseInt(channelInfo.statistics.viewCount).toLocaleString()
                : channelInfo?.statistics?.viewCount}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
            <span className="text-xs text-slate-400 font-semibold block mb-1">
              {isAr ? 'الفيديوهات (Uploads)' : 'Total Videos'}
            </span>
            <span className="text-xl font-black text-red-400">
              {channelInfo?.statistics?.videoCount || '0'}
            </span>
          </div>
        </div>
      </div>

      {/* Step by Step Guide: How to get API Key & OAuth */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <div 
          onClick={() => setShowGuide(!showGuide)}
          className="flex items-center justify-between cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-black text-white">
              {isAr ? 'دليل إعداد المفاتيح خطوة بخطوة من Google Cloud Console' : 'Step-by-Step Google Cloud Setup Guide'}
            </h3>
          </div>
          <button className="text-slate-400 hover:text-white">
            {showGuide ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {showGuide && (
          <div className="space-y-4 pt-2 border-t border-slate-800 text-xs text-slate-300">
            
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex gap-3">
              <div className="w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center font-bold shrink-0">
                1
              </div>
              <div>
                <h4 className="font-bold text-white text-sm mb-1">
                  {isAr ? 'إنشاء مشروع في Google Cloud Console' : 'Create Google Cloud Project'}
                </h4>
                <p className="text-slate-400 leading-relaxed">
                  {isAr 
                    ? 'توجه إلى console.cloud.google.com وسجل بحساب Google الذي عليه القناة. اضغط "Select a project" ثم "New Project" وسمه باسم قناتك (مثل CosmicTube).'
                    : 'Go to console.cloud.google.com, click "Select a project" -> "New Project" and name it.'}
                </p>
                <a 
                  href="https://console.cloud.google.com" 
                  target="_blank" 
                  rel="noreferrer" 
                  className="inline-flex items-center gap-1 text-red-400 hover:text-red-300 font-semibold mt-1"
                >
                  <span>Google Cloud Console</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex gap-3">
              <div className="w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center font-bold shrink-0">
                2
              </div>
              <div>
                <h4 className="font-bold text-white text-sm mb-1">
                  {isAr ? 'تفعيل YouTube Data API v3' : 'Enable YouTube Data API v3'}
                </h4>
                <p className="text-slate-400 leading-relaxed">
                  {isAr 
                    ? 'من القائمة الجانبية: "APIs & Services" -> "Library" -> ابحث عن "YouTube Data API v3" واضغط "Enable".'
                    : 'In APIs & Services -> Library -> Search "YouTube Data API v3" -> Click Enable.'}
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex gap-3">
              <div className="w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center font-bold shrink-0">
                3
              </div>
              <div>
                <h4 className="font-bold text-white text-sm mb-1">
                  {isAr ? 'استخراج API Key (للبحث ورصد الترندات)' : 'Create API Key (For Search & Trends)'}
                </h4>
                <p className="text-slate-400 leading-relaxed">
                  {isAr 
                    ? 'اذهب إلى "Credentials" -> اضغط "Create Credentials" -> اختر "API Key". انسخ المفتاح وضعه في خانة API Key أدناه.'
                    : 'In Credentials -> Create Credentials -> API Key. Copy and paste it below.'}
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex gap-3">
              <div className="w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center font-bold shrink-0">
                4
              </div>
              <div>
                <h4 className="font-bold text-white text-sm mb-1">
                  {isAr ? 'استخراج OAuth 2.0 Client ID (للنشر ورفع الفيديوهات)' : 'Create OAuth 2.0 Credentials (For Video Upload)'}
                </h4>
                <p className="text-slate-400 leading-relaxed">
                  {isAr 
                    ? 'في "Credentials" -> "Create Credentials" -> "OAuth client ID" -> اختر نوع التطبيق "Web application". أضف في "Authorized redirect URIs" الرابط الظاهر أدناه، ثم انسخ Client ID و Client Secret وضعهما في النموذج.'
                    : 'In Credentials -> Create Credentials -> OAuth client ID -> Web application. Add the Redirect URI below and paste Client ID and Secret.'}
                </p>
              </div>
            </div>

          </div>
        )}
      </div>

      {/* Credentials Configuration Form */}
      <form onSubmit={handleSave} className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-6">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-red-500" />
          <h3 className="text-base font-black text-white">
            {isAr ? 'إدخال مفاتيح الاعتماد (API Credentials)' : 'API Credentials Configuration'}
          </h3>
        </div>

        <div className="space-y-4">
          
          {/* API Key */}
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              Google YouTube API Key ({isAr ? 'للبحث والترندات اللحظية' : 'For live trends & search'})
            </label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="AIzaSy..."
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 text-xs font-mono"
            />
          </div>

          {/* Client ID */}
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              OAuth 2.0 Client ID ({isAr ? 'مطلوب لرفع الفيديوهات' : 'Required for video uploads'})
            </label>
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="xxxxxxxxxxxx-xxxxxxxx.apps.googleusercontent.com"
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 text-xs font-mono"
            />
          </div>

          {/* Client Secret */}
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              OAuth 2.0 Client Secret ({isAr ? 'السر الخاص' : 'Secret'})
            </label>
            <input
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="GOCSPX-..."
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 text-xs font-mono"
            />
          </div>

          {/* Redirect URI */}
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              Authorized Redirect URI ({isAr ? 'ضعه في إعدادات Google Cloud Console' : 'Set this in Google Cloud Console'})
            </label>
            <input
              type="text"
              value={redirectUri}
              onChange={(e) => setRedirectUri(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700/80 text-slate-400 focus:outline-none focus:border-red-500 text-xs font-mono"
            />
          </div>

        </div>

        {message && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{message}</span>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-slate-700 transition flex items-center justify-center gap-2"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>{saving ? (isAr ? 'جاري الحفظ...' : 'Saving...') : (isAr ? 'حفظ إعدادات الـ API' : 'Save Credentials')}</span>
          </button>

          <button
            type="button"
            onClick={handleConnectGoogle}
            className="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-xs shadow-lg shadow-red-600/30 transition flex items-center justify-center gap-2"
          >
            <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
            <span>{isAr ? 'بدء تفويض القناة الآن (OAuth)' : 'Authorize Channel Now'}</span>
          </button>
        </div>

      </form>

    </div>
  );
}
