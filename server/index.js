import express from 'express';
import cors from 'cors';
import path from 'path';
import fs from 'fs';
import multer from 'multer';
import { fileURLToPath } from 'url';
import { 
  loadConfig, 
  saveConfig, 
  generateAuthUrl, 
  handleOAuthCallback, 
  disconnectChannel,
  getTrendingVideos,
  searchVideos,
  publishVideo,
  loadSavedVideos
} from './youtubeService.js';
import { 
  VIRAL_CATEGORIES, 
  generateViralBlueprint, 
  extractViralTags,
  generateInfiniteViralIdeas
} from './viralEngine.js';
import {
  getAutoPilotStatus,
  startAutoPilot,
  stopAutoPilot,
  runAutoPilotCycle
} from './autoPilot.js';
import {
  getGitHubStatus,
  syncToGitHub
} from './githubSync.js';
import {
  listProducedVideos,
  listAvailableTopics,
  startProduceJob,
  getJobStatus
} from './videoFactoryBridge.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.join(__dirname, '..');
const UPLOADS_DIR = path.join(ROOT_DIR, 'uploads');

// Ensure uploads folder exists
if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

const app = express();
const PORT = process.env.PORT || 3000;

// Allow e2b.app and any preview host origin
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static uploads
app.use('/uploads', express.static(UPLOADS_DIR));
app.use('/content/vids', express.static(path.join(ROOT_DIR, 'content', 'vids')));
app.use('/assets/footage', express.static(path.join(ROOT_DIR, 'assets', 'footage')));

// Configure multer for video & thumbnail uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, UPLOADS_DIR);
  },
  filename: function (req, file, cb) {
    const ext = path.extname(file.originalname);
    const uniqueName = `${Date.now()}-${Math.round(Math.random() * 1E9)}${ext}`;
    cb(null, uniqueName);
  }
});
const upload = multer({ 
  storage,
  limits: { fileSize: 500 * 1024 * 1024 } // 500MB max
});

// API Routes
// 1. Get Status & Channel Info
app.get('/api/status', (req, res) => {
  const config = loadConfig();
  res.json({
    connected: Boolean(config.connected),
    mode: config.mode || 'demo',
    hasApiKey: Boolean(config.apiKey),
    hasOAuth: Boolean(config.clientId && config.clientSecret),
    channel: config.channel
  });
});

// 2. Get Settings
app.get('/api/settings', (req, res) => {
  const config = loadConfig();
  res.json({
    apiKey: config.apiKey ? '••••••••' + config.apiKey.slice(-4) : '',
    rawApiKey: config.apiKey || '',
    clientId: config.clientId ? '••••••••' + config.clientId.slice(-6) : '',
    rawClientId: config.clientId || '',
    clientSecret: config.clientSecret ? '••••••••' : '',
    redirectUri: config.redirectUri || 'http://localhost:3000/api/auth/callback',
    connected: Boolean(config.connected),
    mode: config.mode,
    channel: config.channel
  });
});

// 3. Save Settings
app.post('/api/settings', (req, res) => {
  const { apiKey, clientId, clientSecret, redirectUri, mode } = req.body;
  const current = loadConfig();

  if (apiKey !== undefined) current.apiKey = apiKey.trim();
  if (clientId !== undefined) current.clientId = clientId.trim();
  if (clientSecret !== undefined && !clientSecret.startsWith('••••')) {
    current.clientSecret = clientSecret.trim();
  }
  if (redirectUri !== undefined) current.redirectUri = redirectUri.trim();
  if (mode !== undefined) current.mode = mode;

  saveConfig(current);
  res.json({ success: true, message: 'تم حفظ الإعدادات بنجاح!' });
});

// 4. Generate Google Auth URL
app.get('/api/auth/url', (req, res) => {
  try {
    const url = generateAuthUrl();
    res.json({ success: true, url });
  } catch (err) {
    res.status(400).json({ success: false, error: err.message });
  }
});

// 5. OAuth Callback
app.get('/api/auth/callback', async (req, res) => {
  const { code } = req.query;
  if (!code) {
    return res.redirect('/?auth=error&msg=NoCode');
  }

  try {
    await handleOAuthCallback(code);
    return res.redirect('/?auth=success');
  } catch (err) {
    console.error('OAuth callback failed:', err);
    return res.redirect(`/?auth=error&msg=${encodeURIComponent(err.message)}`);
  }
});

// 5b. Manual OAuth Code Exchange (Fallback for cloud preview proxies)
app.post('/api/auth/exchange-code', async (req, res) => {
  try {
    let { code } = req.body;
    if (!code || !code.trim()) {
      return res.status(400).json({ success: false, error: 'كود التفويض مطلوب' });
    }
    code = code.trim();
    if (code.includes('code=')) {
      const match = code.match(/code=([^&]+)/);
      if (match) code = decodeURIComponent(match[1]);
    }
    const result = await handleOAuthCallback(code);
    res.json({ success: true, channel: result.channel });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 5c. Save Exchanged Tokens Directly
app.post('/api/auth/save-tokens', async (req, res) => {
  try {
    const { tokens, channel } = req.body;
    const config = loadConfig();
    config.tokens = tokens;
    config.connected = true;
    config.mode = 'live';
    if (channel) {
      config.channel = channel;
    }
    saveConfig(config);
    res.json({ success: true, message: 'تم حفظ وتفعيل توكنات القناة بنجاح!' });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 6. Disconnect Channel
app.post('/api/auth/disconnect', (req, res) => {
  disconnectChannel();
  res.json({ success: true, message: 'تم إلغاء ربط القناة بنجاح' });
});

// 7. Trending & Viral Categories
app.get('/api/categories', (req, res) => {
  res.json(VIRAL_CATEGORIES);
});

app.get('/api/trends', async (req, res) => {
  try {
    const { region = 'US', category = 'all' } = req.query;
    const trends = await getTrendingVideos(region, category);
    res.json(trends);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 8. Search Videos
app.get('/api/search', async (req, res) => {
  try {
    const { q = '', region = 'US' } = req.query;
    const results = await searchVideos(q, region);
    res.json(results);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 9. Generate Viral Blueprint & Script
app.post('/api/generate-blueprint', (req, res) => {
  try {
    const { topic, category } = req.body;
    if (!topic || !topic.trim()) {
      return res.status(400).json({ error: 'يرجى كتابة فكرة أو عنوان الفيديو' });
    }
    const blueprint = generateViralBlueprint(topic, category);
    res.json(blueprint);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 10. Extract Tags & SEO
app.post('/api/extract-tags', (req, res) => {
  try {
    const { keyword } = req.body;
    if (!keyword) {
      return res.status(400).json({ error: 'يرجى كتابة الكلمة المفتاحية' });
    }
    const tagsData = extractViralTags(keyword);
    res.json(tagsData);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 10b. Infinite Million-Ideas Vault
app.get('/api/ideas/infinite', (req, res) => {
  try {
    const { count = 12, niche = 'all' } = req.query;
    const ideas = generateInfiniteViralIdeas(Number(count), niche);
    res.json(ideas);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 11. Upload & Publish Video
app.post('/api/upload', upload.fields([
  { name: 'video', maxCount: 1 },
  { name: 'thumbnail', maxCount: 1 }
]), async (req, res) => {
  try {
    const { title, description, tags, privacyStatus, categoryId, isShort } = req.body;

    if (!title || !title.trim()) {
      return res.status(400).json({ error: 'العنوان مطلوب لنشر الفيديو' });
    }

    const videoFile = req.files?.['video']?.[0];
    const thumbnailFile = req.files?.['thumbnail']?.[0];

    const parsedTags = Array.isArray(tags)
      ? tags
      : (typeof tags === 'string' ? tags.split(',').map(t => t.trim()).filter(Boolean) : []);

    const result = await publishVideo({
      videoFilePath: videoFile ? videoFile.path : null,
      thumbnailFilePath: thumbnailFile ? thumbnailFile.path : null,
      title: title.trim(),
      description: description || '',
      tags: parsedTags,
      privacyStatus: privacyStatus || 'public',
      categoryId: categoryId || '24',
      isShort: isShort === 'true' || isShort === true
    });

    res.json(result);
  } catch (err) {
    console.error('Publish endpoint error:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

// 11b. Publish directly from Factory Library
app.post('/api/publish-factory', express.json(), async (req, res) => {
  try {
    const { videoId, title, description, tags, privacyStatus, categoryId, isShort } = req.body;
    if (!videoId) {
      return res.status(400).json({ error: 'videoId is required' });
    }

    const videoFilePath = path.resolve('content/vids', `${videoId}.mp4`);
    if (!fs.existsSync(videoFilePath)) {
      return res.status(404).json({ error: `Video file ${videoId}.mp4 not found` });
    }

    const coverPath = path.resolve('content/vids', `${videoId}-cover.png`);
    const thumbnailFilePath = fs.existsSync(coverPath) ? coverPath : null;

    const parsedTags = Array.isArray(tags)
      ? tags
      : (typeof tags === 'string' ? tags.split(',').map(t => t.trim()).filter(Boolean) : []);

    const result = await publishVideo({
      videoFilePath,
      thumbnailFilePath,
      title: (title || `Cosmic Short #${videoId}`).trim(),
      description: description || 'Generated autonomously with CosmicTube 2099 Engine.',
      tags: parsedTags.length > 0 ? parsedTags : ['Shorts', 'CosmicTube', 'Viral', 'Science'],
      privacyStatus: privacyStatus || 'public',
      categoryId: categoryId || '28',
      isShort: isShort !== false
    });

    res.json(result);
  } catch (err) {
    console.error('Publish factory error:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

// 12. Get Channel Uploaded Videos
app.get('/api/videos', (req, res) => {
  const videos = loadSavedVideos();
  res.json(videos);
});

// 13. Autonomous Auto-Pilot System
app.get('/api/autopilot', (req, res) => {
  res.json(getAutoPilotStatus());
});

app.post('/api/autopilot/start', (req, res) => {
  const { intervalHours = 6, continuousTurbo = false, turboDelaySeconds = 20 } = req.body;
  const status = startAutoPilot(Number(intervalHours), continuousTurbo, Number(turboDelaySeconds));
  res.json({ success: true, status });
});

app.post('/api/autopilot/stop', (req, res) => {
  const status = stopAutoPilot();
  res.json({ success: true, status });
});

app.post('/api/autopilot/run-now', async (req, res) => {
  await runAutoPilotCycle();
  res.json({ success: true, status: getAutoPilotStatus() });
});

// 14. GitHub Cloud Storage & Sync Engine
app.get('/api/github/status', async (req, res) => {
  const status = await getGitHubStatus();
  res.json(status);
});

app.post('/api/github/sync', async (req, res) => {
  try {
    const result = await syncToGitHub(req.body.message);
    res.json(result);
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 15. Real Video Factory & 2099 Montage Engine
app.get('/api/factory/videos', (req, res) => {
  res.json(listProducedVideos());
});

app.get('/api/footage', (req, res) => {
  const footageDir = path.join(ROOT_DIR, 'assets', 'footage');
  if (!fs.existsSync(footageDir)) {
    return res.json({ clips: [], total: 0 });
  }
  const meta = {
    '01_fire_hook_motion.mp4': {
      titleAr: 'خطاف الصدمة الناري — ألسنة لهب وشظايا متطايرة',
      titleEn: 'Fire Hook Shockwave — Roaring Flames & Flying Embers',
      category: 'challenges',
      categoryAr: 'تحديات خطيرة',
      tags: ['fire', 'flames', 'hook', 'mrbeast', 'action', 'danger'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '02_cash_rain_motion.mp4': {
      titleAr: 'أمطار أوراق النقد 3D — ملايين الدولارات تتساقط',
      titleEn: '3D Cash Rain Motion — Millions Raining Down',
      category: 'money',
      categoryAr: 'أموال وجوائز',
      tags: ['money', 'cash', 'dollars', 'jackpot', 'mrbeast', 'luxury'],
      duration: '6.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '03_blizzard_freeze_motion.mp4': {
      titleAr: 'عاصفة ثلجية جليدية — رياح عاتية وصقيع متجمد',
      titleEn: 'Arctic Blizzard Gale — Freezing Wind & Lens Frost',
      category: 'survival',
      categoryAr: 'بقاء وتحمل',
      tags: ['ice', 'blizzard', 'snow', 'freeze', 'survival', 'arctic'],
      duration: '6.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '04_countdown_hud_motion.mp4': {
      titleAr: 'مؤقت الخطر وإنذار الطوارئ — رادار وعداد ثوانٍ رقمي',
      titleEn: 'Emergency Danger HUD — Radar & Digital Countdown Timer',
      category: 'countdown',
      categoryAr: 'عدادات وإنذار',
      tags: ['timer', 'countdown', 'alarm', 'siren', 'hud', 'danger'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '05_confetti_winner_motion.mp4': {
      titleAr: 'احتفال الفوز الأسطوري — انفجار كونفيتي وأشعة ذهبية',
      titleEn: 'Epic Winner Celebration — Golden Confetti Cannon Explosion',
      category: 'celebration',
      categoryAr: 'فوز وتتويج',
      tags: ['winner', 'trophy', 'confetti', 'celebration', 'victory'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '06_cash_struggle_close.mp4': {
      titleAr: 'صراع الأيدي على الكاش — شبكة ليزر أمني وترقب حاسم',
      titleEn: 'Cash Hands Tension — Security Laser Grid & Lock-In',
      category: 'money',
      categoryAr: 'تحدي الصمود',
      tags: ['hands', 'cash', 'laser', 'contestants', 'tension'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '07_space_warp_cosmic.mp4': {
      titleAr: 'قفزة فضاء كونية — سرعة الضوء وسديم مجري',
      titleEn: 'Cosmic Hyperspace Warp — Light Speed & Galactic Nebula',
      category: 'science',
      categoryAr: 'فضاء وعلوم',
      tags: ['space', 'cosmic', 'warp', 'stars', 'galaxy', 'universe'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '08_neon_cyber_grid.mp4': {
      titleAr: 'شبكة نيون سايبر — أفق مستقبلي وشمس رقمية',
      titleEn: 'Neon Cyber Grid — Retro Horizon & Pulsing Digital Sun',
      category: 'countdown',
      categoryAr: 'سايبر ومستقبل',
      tags: ['cyber', 'neon', 'grid', 'synthwave', 'futuristic'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    },
    '09_lightning_storm_danger.mp4': {
      titleAr: 'عاصفة برق ورعد — ومضات صاعقة وأمطار غزيرة',
      titleEn: 'Violent Lightning Storm — Strobe Flashes & Heavy Rain',
      category: 'survival',
      categoryAr: 'عواصف وخطر',
      tags: ['lightning', 'storm', 'thunder', 'rain', 'extreme'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920 (9:16 Shorts)'
    }
  };

  const files = fs.readdirSync(footageDir).filter(f => f.endsWith('.mp4')).sort();
  const clips = files.map(file => {
    const fpath = path.join(footageDir, file);
    const stat = fs.statSync(fpath);
    const m = meta[file] || {
      titleAr: `لقطة فيديو ${file}`,
      titleEn: `Footage Clip ${file}`,
      category: 'general',
      categoryAr: 'عام',
      tags: ['footage', 'viral'],
      duration: '5.0s',
      fps: 30,
      res: '1080x1920'
    };
    return {
      filename: file,
      url: `/assets/footage/${file}`,
      sizeMB: (stat.size / (1024 * 1024)).toFixed(2),
      ...m
    };
  });
  res.json({ clips, total: clips.length });
});

// 15b. Curated Royalty-Free Video Sources Hub
app.get('/api/footage/sources', (req, res) => {
  res.json({
    sources: [
      {
        id: 'pexels',
        name: 'Pexels Videos',
        badge: 'الأفضل للفيديوهات العمودية 9:16',
        descriptionAr: 'أكثر من 50,000+ فيديو مجاني 4K وبدون أي حقوق ملكية أو علامة مائية، مع فلتر مخصص للفيديوهات العمودية Portrait لـ Shorts و TikTok.',
        descriptionEn: '50,000+ free 4K/HD clips with dedicated vertical 9:16 filter. Zero copyright, no watermark, commercial use allowed.',
        url: 'https://www.pexels.com/videos/',
        verticalSearchUrl: 'https://www.pexels.com/search/videos/%D8%AA%D8%AD%D8%AF%D9%8A%D8%A7%D8%AA/?orientation=portrait',
        license: 'Pexels License (Free Commercial Use, No Attribution Required)',
        apiSupported: true,
        apiDocs: 'https://www.pexels.com/api/'
      },
      {
        id: 'pixabay',
        name: 'Pixabay Videos',
        badge: 'أكبر تنوع للمؤثرات والأنيميشن',
        descriptionAr: 'مكتبة ضخمة تضم أكثر من 40,000 فيديو ومؤثر بصري وانفجارات وكروما جاهزة للاستخدام الحر المباشر.',
        descriptionEn: 'Over 40,000 high-quality video clips, visual effects, motion backgrounds, and green screens.',
        url: 'https://pixabay.com/videos/',
        verticalSearchUrl: 'https://pixabay.com/videos/search/challenge/',
        license: 'Pixabay Content License (Commercial Use Allowed, No Attribution Required)',
        apiSupported: true,
        apiDocs: 'https://pixabay.com/api/docs/#api_videos'
      },
      {
        id: 'mixkit',
        name: 'Mixkit (Envato)',
        badge: 'جودة سينمائية منتقاة',
        descriptionAr: 'مكتبة سينمائية منتقاة بعناية فائقة من مصوري ومحرري هوليوود بدون أي تسجيل دخول وبتحميل مباشر وفوري.',
        descriptionEn: 'High-end curated cinematic stock video clips and transitions with instant direct download.',
        url: 'https://mixkit.co/free-stock-video/',
        verticalSearchUrl: 'https://mixkit.co/free-stock-video/vertical/',
        license: 'Mixkit Free License (Free for Commercial YouTube & Social Media)',
        apiSupported: false
      },
      {
        id: 'coverr',
        name: 'Coverr.co',
        badge: 'فيديوهات خلفيات وترندات',
        descriptionAr: 'منصة متخصصة في المشاهد الجمالية السريعة واللقطات العمودية المخصصة لصناع المحتوى ومنصات التواصل.',
        descriptionEn: 'Beautiful free stock video footage curated specifically for modern creators and vertical formats.',
        url: 'https://coverr.co/',
        verticalSearchUrl: 'https://coverr.co/vertical-videos',
        license: 'Coverr License (100% Free Commercial Use)',
        apiSupported: false
      },
      {
        id: 'nasa',
        name: 'NASA Image & Video Library',
        badge: 'فضاء وثقوب سوداء ملك عام (Public Domain)',
        descriptionAr: 'الأرشيف الرسمي المفتوح لوكالة ناسا يضم آلاف الساعات من لقطات الفضاء الحقيقية والمكوك والانفجارات النجمية بدقة 4K مجاناً.',
        descriptionEn: 'Official NASA media repository with public domain space, planetary, and cosmic footage.',
        url: 'https://images.nasa.gov/',
        verticalSearchUrl: 'https://images.nasa.gov/search-results?q=black%20hole&media=video',
        license: 'Public Domain / Free for Public Education & Creation',
        apiSupported: true
      },
      {
        id: 'wikimedia',
        name: 'Wikimedia Commons Video',
        badge: 'أرشيف عالمي حر (CC0 / CC-BY)',
        descriptionAr: 'ملايين مقاطع الفيديو المفتوحة والموثقة لطبيعة وتاريخ وأحداث وتجارب علمية من مختلف أنحاء العالم.',
        descriptionEn: 'Global open repository of educational, nature, and scientific motion videos.',
        url: 'https://commons.wikimedia.org/wiki/Category:Videos',
        verticalSearchUrl: 'https://commons.wikimedia.org/w/index.php?search=motion+video',
        license: 'Creative Commons (CC0 & CC-BY)',
        apiSupported: true
      }
    ]
  });
});

// 15c. Dynamic Footage Ingestion & Generation for Factory
app.post('/api/footage/fetch', express.json(), async (req, res) => {
  try {
    const { query = 'space', duration = 5.0 } = req.body;
    const { exec } = await import('child_process');
    const util = await import('util');
    const execAsync = util.promisify(exec);

    const pyCmd = `python3 -c "from xtrendaw.generate_footage_vault import generate_clip_on_demand; print(generate_clip_on_demand('${query.replace(/'/g, "")}', ${duration}))"`;
    const { stdout, stderr } = await execAsync(pyCmd, { cwd: ROOT_DIR });

    const filename = stdout.trim().split('\n').pop().trim();
    const clipUrl = `/assets/footage/${filename}`;

    res.json({
      success: true,
      message: `تم جلب وتجهيز مشهد «${query}» بنجاح في مكتبة المصنع!`,
      clip: {
        filename,
        url: clipUrl,
        query,
        duration: `${duration}s`,
        res: '1080x1920 (9:16 Shorts)'
      }
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.get('/api/factory/topics', (req, res) => {
  res.json(listAvailableTopics());
});

app.post('/api/factory/produce', async (req, res) => {
  try {
    const { topicId = 'ep1' } = req.body;
    const job = await startProduceJob(topicId);
    res.json({ success: true, job });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.get('/api/factory/job/:jobId', (req, res) => {
  const job = getJobStatus(req.params.jobId);
  if (!job) return res.status(404).json({ error: 'Job not found' });
  res.json(job);
});

// Serve frontend build in production
const DIST_DIR = path.join(ROOT_DIR, 'dist');
if (fs.existsSync(DIST_DIR)) {
  app.use(express.static(DIST_DIR));
  app.use((req, res, next) => {
    if (req.path.startsWith('/api') || req.path.startsWith('/uploads')) {
      return next();
    }
    res.sendFile(path.join(DIST_DIR, 'index.html'));
  });
}

// Start Server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌌 Cosmic YouTube Engine running on http://0.0.0.0:${PORT}`);
  // Start 30-minute AutoPilot automatically 24/7
  try {
    startAutoPilot(0.5);
    console.log('🤖 AutoPilot 24/7 initialized: Scheduled every 30 minutes continuous publishing.');
  } catch (err) {
    console.error('Failed to init AutoPilot:', err.message);
  }
});
