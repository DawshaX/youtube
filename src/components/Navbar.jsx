import React from 'react';
import { 
  Sparkles, 
  Flame, 
  Video, 
  UploadCloud, 
  Hash, 
  Settings, 
  Globe, 
  CheckCircle2, 
  Radio, 
  ExternalLink,
  Bot
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, channelInfo, isConnected, mode, lang, toggleLang }) {
  const isAr = lang === 'ar';

  const navItems = [
    { id: 'trends', label: isAr ? 'الرادار والترند' : 'Viral Radar', icon: Flame },
    { id: 'player', label: isAr ? 'معاينة الفيديو الحي' : 'Video Player', icon: Play },
    { id: 'script', label: isAr ? 'استوديو السيناريو' : 'Script Studio', icon: Video },
    { id: 'publisher', label: isAr ? 'مركز النشر والرفع' : 'Smart Publisher', icon: UploadCloud },
    { id: 'seo', label: isAr ? 'سيو والهاشتاجات' : 'Tags & SEO', icon: Hash },
    { id: 'autopilot', label: isAr ? 'الطيار الآلي 24/7' : 'AutoPilot 24/7', icon: Bot },
    { id: 'connect', label: isAr ? 'ربط القناة والـ API' : 'Channel & API', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Identity */}
          <div className="flex items-center space-x-3 rtl:space-x-reverse cursor-pointer" onClick={() => setActiveTab('trends')}>
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-red-600 via-rose-500 to-amber-500 flex items-center justify-center shadow-lg shadow-red-500/25 ring-2 ring-red-500/30">
              <Sparkles className="w-6 h-6 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                  COSMIC<span className="text-red-500">TUBE</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] font-extrabold uppercase rounded-full bg-red-500/20 text-red-400 border border-red-500/30 tracking-wider">
                  #1 GLOBAL
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium">
                {isAr ? 'منظومة القناة العالمية رقم 1' : 'Universal Viral Channel System'}
              </p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="hidden lg:flex items-center gap-1.5 p-1 bg-slate-950/60 rounded-xl border border-slate-800/80">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-red-600 to-red-700 text-white shadow-md shadow-red-600/30 ring-1 ring-red-400/40'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Status & Channel Widget */}
          <div className="flex items-center gap-3">
            {/* Connected Channel Pill */}
            <div 
              onClick={() => setActiveTab('connect')}
              className="flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-slate-800/90 border border-slate-700/80 hover:border-red-500/50 transition cursor-pointer"
            >
              <img
                src={channelInfo?.thumbnails?.default?.url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop&q=80'}
                alt="Channel Avatar"
                className="w-7 h-7 rounded-full ring-2 ring-red-500/40 object-cover"
              />
              <div className="hidden sm:block text-right rtl:text-right ltr:text-left">
                <div className="text-xs font-bold text-slate-200 line-clamp-1 max-w-[120px]">
                  {channelInfo?.title || 'Cosmic One'}
                </div>
                <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                  <span>{isConnected ? (isAr ? 'متصل حي' : 'Live') : (isAr ? 'جاهز للنشر' : 'Engine Ready')}</span>
                </div>
              </div>
            </div>

            {/* Language toggle */}
            <button
              onClick={toggleLang}
              className="p-2 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-1 text-xs font-bold"
              title="تغيير اللغة"
            >
              <Globe className="w-4 h-4 text-slate-400" />
              <span>{isAr ? 'EN' : 'عربي'}</span>
            </button>
          </div>

        </div>

        {/* Mobile Navigation bar */}
        <div className="flex lg:hidden overflow-x-auto py-2.5 gap-2 border-t border-slate-800/60 no-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 whitespace-nowrap rounded-lg text-xs font-semibold ${
                  isActive
                    ? 'bg-red-600 text-white'
                    : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

      </div>
    </header>
  );
}
