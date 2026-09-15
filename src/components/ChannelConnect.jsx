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
  ChevronUp,
  Database,
  Cloud,
  GitBranch
} from 'lucide-react';

export default function ChannelConnect({ channelInfo, isConnected, onChannelUpdated, isAr }) {
  const [apiKey, setApiKey] = useState('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [redirectUri, setRedirectUri] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [showGuide, setShowGuide] = useState(true);
  const [gitStatus, setGitStatus] = useState(null);
  const [syncingGit, setSyncingGit] = useState(false);
  const [gitSyncMsg, setGitSyncMsg] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [exchangingCode, setExchangingCode] = useState(false);
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [authUrl, setAuthUrl] = useState('');

  const fetchGitStatus = async () => {
    try {
      const res = await fetch('/api/github/status');
      const data = await res.json();
      setGitStatus(data);
    } catch (e) {
      console.error('Fetch git status error:', e);
    }
  };

  const handleSyncGit = async () => {
    setSyncingGit(true);
    setGitSyncMsg('');
    try {
      const res = await fetch('/api/github/sync', { method: 'POST' });
      const data = await res.json();
      setGitSyncMsg(data.message || (isAr ? 'تمت المزامنة بنجاح!' : 'Synced successfully!'));
      fetchGitStatus();
    } catch (err) {
      setGitSyncMsg(isAr ? 'فشلت المزامنة' : 'Sync failed');
    } finally {
      setSyncingGit(false);
    }
  };

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

  const [copiedLink, setCopiedLink] = useState(false);

  const fetchAuthUrl = async () => {
    try {
      const res = await fetch('/api/auth/url');
      const data = await res.json();
      if (data.success && data.url) {
        setAuthUrl(data.url);
      }
    } catch (e) {
      // not ready yet
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchGitStatus();
    fetchAuthUrl();
  }, []);

  const handleCopyAuthUrl = () => {
    if (!authUrl) return;
    navigator.clipboard.writeText(authUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleJsonUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        const creds = parsed.web || parsed.installed;
        if (creds) {
          if (creds.client_id) setClientId(creds.client_id);
          if (creds.client_secret) setClientSecret(creds.client_secret);
          
          const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              apiKey,
              clientId: creds.client_id,
              clientSecret: creds.client_secret,
              redirectUri
            })
          });
          const data = await res.json();
          if (data.success) {
            setMessage(isAr ? '🎉 تم استخراج وحفظ بيانات OAuth من ملف JSON بنجاح!' : 'OAuth credentials extracted and saved!');
            if (onChannelUpdated) onChannelUpdated();
          }
        } else {
          alert(isAr ? 'الملف ليس بتنسيق Google OAuth JSON المعروف' : 'Invalid Google OAuth JSON format');
        }
      } catch (err) {
        alert(isAr ? 'تعذر قراءة ملف JSON' : 'Failed to parse JSON file');
      }
    };
    reader.readAsText(file);
  };

  const handleSave = async (e) => {
    if (e) e.preventDefault();
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
        setAuthUrl(data.url);
        setShowCodeInput(true);
        window.open(data.url, '_blank');
      } else {
        alert(data.error || (isAr ? 'يرجى إدخال Client ID و Client Secret أولاً في النموذج أدناه أو استيراد ملف JSON.' : 'Please configure Client ID & Secret below first.'));
      }
    } catch (err) {
      alert(err.message || 'Error generating auth url');
    }
  };

  const handleManualCodeSubmit = async (e) => {
    e.preventDefault();
    if (!manualCode.trim()) return;
    setExchangingCode(true);
    setMessage('');
    try {
      const res = await fetch('/api/auth/exchange-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: manualCode.trim() })
      });
      const data = await res.json();
      if (data.success) {
        setMessage(isAr ? '🎉 مبروك! تم تفعيل وتفويض القناة رسمياً وربطها بنجاح مدى الحياة!' : 'Channel connected and authorized for lifetime!');
        setShowCodeInput(false);
        setManualCode('');
        if (onChannelUpdated) onChannelUpdated();
      } else {
        alert(data.error || (isAr ? 'فشل تبادل الكود، تأكد من صحة الرابط أو الكود' : 'Invalid authorization code'));
      }
    } catch (err) {
      alert(err.message || 'Error exchanging code');
    } finally {
      setExchangingCode(false);
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

      {/* GitHub Cloud Storage & Persistence Engine */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/20 text-purple-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-black text-white">
                  {isAr ? 'نظام التخزين السحابي الدائم عبر GitHub (Cloud Storage)' : 'GitHub Permanent Cloud Storage'}
                </h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  {isAr ? 'متصل مدى الحياة ♾️' : 'Lifetime Active'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {isAr 
                  ? 'يتم حفظ كافة سيناريوهات الفيديوهات، التحليلات، وإعدادات القناة تلقائياً وبشكل دائم في مستودع GitHub.'
                  : 'Channel archives, scripts, and production logs are synced permanently to GitHub storage.'}
              </p>
            </div>
          </div>

          <button
            onClick={handleSyncGit}
            disabled={syncingGit}
            className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-600/30 transition flex items-center gap-2 shrink-0 disabled:opacity-50"
          >
            <Cloud className={`w-4 h-4 ${syncingGit ? 'animate-bounce' : ''}`} />
            <span>{syncingGit ? (isAr ? 'جاري المزامنة...' : 'Syncing...') : (isAr ? 'مزامنة التخزين السحابي الآن' : 'Sync to GitHub Cloud')}</span>
          </button>
        </div>

        {gitStatus && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono">
              <span className="text-slate-500 block text-[10px]">{isAr ? 'المستودع (Repository)' : 'Repository'}</span>
              <span className="text-purple-300 font-bold">{gitStatus.repository}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono">
              <span className="text-slate-500 block text-[10px]">{isAr ? 'الفرع السحابي (Branch)' : 'Active Branch'}</span>
              <span className="text-emerald-400 font-bold">{gitStatus.branch}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono">
              <span className="text-slate-500 block text-[10px]">{isAr ? 'آخر مزامنة (Last Commit)' : 'Last Sync'}</span>
              <span className="text-slate-300 truncate block">{gitStatus.lastCommit}</span>
            </div>
          </div>
        )}

        {gitSyncMsg && (
          <div className="p-3 rounded-xl bg-purple-950/40 border border-purple-500/40 text-purple-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{gitSyncMsg}</span>
          </div>
        )}
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
              <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold shrink-0">
                ♾️
              </div>
              <div>
                <h4 className="font-bold text-emerald-300 text-sm mb-1">
                  {isAr ? 'كيف يعمل الاتصال مدى الحياة ويتجدد تلقائياً؟ (Refresh Token)' : 'How Permanent Auto-Renewal Works'}
                </h4>
                <p className="text-slate-400 leading-relaxed">
                  {isAr 
                    ? 'عند الضغط على "ربط القناة بحساب Google"، يطلب النظام تصريح (Offline Access)، وهذا يمنحه مفتاح تجديد دائم (Refresh Token). خادمنا يقوم بتجديد الاتصال تلقائياً كل ساعة في الخلفية بدون الحاجة لتدخل منك مدى الحياة!'
                    : 'System requests offline access which yields a permanent Refresh Token that automatically refreshes every hour in the background.'}
                </p>
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
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-red-500" />
            <h3 className="text-base font-black text-white">
              {isAr ? 'إدخال مفاتيح الاعتماد (API Credentials)' : 'API Credentials Configuration'}
            </h3>
          </div>

          <label className="cursor-pointer px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-red-400 border border-slate-700 flex items-center gap-1.5 transition">
            <input 
              type="file" 
              accept=".json" 
              onChange={handleJsonUpload} 
              className="hidden" 
            />
            <Database className="w-3.5 h-3.5" />
            <span>{isAr ? 'استيراد ملف client_secret.json' : 'Import JSON File'}</span>
          </label>
        </div>

        {/* Quick Drop Notice */}
        <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between gap-4">
          <div className="text-xs text-slate-300">
            <span className="font-bold text-white block mb-0.5">
              {isAr ? '⚡ استيراد فوري بضغطة زر:' : '⚡ 1-Click Fast Import:'}
            </span>
            <span>
              {isAr 
                ? 'إذا كان لديك ملف client_secret_....json الذي حملته من Google Cloud، اضغط على زر "استيراد ملف" فوق ليتم ملء Client ID والـ Secret تلقائياً!' 
                : 'Upload your downloaded client_secret JSON file to auto-populate Client ID & Secret.'}
            </span>
          </div>
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

        {/* Verification Helper Modal/Box */}
        {(showCodeInput || authUrl) && (
          <div className="mt-4 p-5 rounded-2xl bg-slate-950 border-2 border-red-500/50 space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h4 className="text-sm font-black text-white">
                  {isAr ? '🔗 رابط تفويض القناة المباشر من Google' : 'Direct Google Authorization Link'}
                </h4>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {isAr 
                ? 'اضغط على الزر الأخضر أدناه لفتح صفحة تسجيل الدخول بجوجل، أو انسخ الرابط وافتحه في المتصفح. بعد تسجيل الدخول واختيار حساب القناة، انسخ الرابط الذي سيظهر لك في شريط العنوان وضعه في الخانة لتأكيد الربط مدى الحياة:'
                : 'Click the green button below to open Google Login, or copy the URL. After approving, paste the redirected URL here:'}
            </p>

            {/* Direct Open & Copy Link Row */}
            {authUrl && (
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                  <a
                    href={authUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs text-center shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>{isAr ? 'اضغط هنا لفتح رابط تسجيل الدخول الآن 🚀' : 'Open Google Auth Link Now 🚀'}</span>
                  </a>

                  <button
                    type="button"
                    onClick={handleCopyAuthUrl}
                    className="py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs border border-slate-700 transition flex items-center justify-center gap-1.5 shrink-0"
                  >
                    <span>{copiedLink ? (isAr ? 'تم نسخ الرابط! ✅' : 'Copied! ✅') : (isAr ? 'نسخ الرابط 📋' : 'Copy Link 📋')}</span>
                  </button>
                </div>

                <div className="text-[11px] font-mono text-slate-500 truncate select-all px-1">
                  {authUrl}
                </div>
              </div>
            )}

            {/* Code / URL Input */}
            <div className="space-y-2 pt-1">
              <label className="block text-xs font-bold text-slate-300">
                {isAr ? 'ضع رابط التوجيه (أو كود التفويض code=) هنا لتأكيد التفعيل:' : 'Paste redirect URL or code here:'}
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  placeholder="http://localhost:3000/api/auth/callback?code=4/0A..."
                  className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder-slate-500 focus:outline-none focus:border-red-500"
                />
                <button
                  type="button"
                  onClick={handleManualCodeSubmit}
                  disabled={exchangingCode || !manualCode.trim()}
                  className="px-6 py-3 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-xs shadow-lg shadow-red-600/30 transition disabled:opacity-50 flex items-center justify-center gap-2 shrink-0"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{exchangingCode ? (isAr ? 'جاري التحقق...' : 'Verifying...') : (isAr ? 'تأكيد التفعيل والربط ⚡' : 'Confirm Authorization ⚡')}</span>
                </button>
              </div>
            </div>

          </div>
        )}

      </form>

    </div>
  );
}
