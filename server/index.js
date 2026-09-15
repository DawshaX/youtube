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

    const result = await publishVideo({
      videoFilePath: videoFile ? videoFile.path : null,
      thumbnailFilePath: thumbnailFile ? thumbnailFile.path : null,
      title: title.trim(),
      description: description || '',
      tags: tags ? tags.split(',') : [],
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
  const { intervalHours = 6 } = req.body;
  const status = startAutoPilot(Number(intervalHours));
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
});
