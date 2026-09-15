import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { TOP_GLOBAL_TRENDS } from './viralEngine.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CONFIG_PATH = path.join(__dirname, '../data/config.json');
const VIDEOS_PATH = path.join(__dirname, '../data/saved_videos.json');

// Ensure data files exist
export function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const data = fs.readFileSync(CONFIG_PATH, 'utf-8');
      return JSON.parse(data);
    }
  } catch (err) {
    console.error('Error reading config:', err);
  }
  return {
    apiKey: '',
    clientId: '',
    clientSecret: '',
    redirectUri: 'http://localhost:3000/api/auth/callback',
    tokens: null,
    connected: false,
    mode: 'demo',
    channel: null
  };
}

export function saveConfig(newConfig) {
  try {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(newConfig, null, 2), 'utf-8');
    return true;
  } catch (err) {
    console.error('Error saving config:', err);
    return false;
  }
}

export function loadSavedVideos() {
  try {
    if (fs.existsSync(VIDEOS_PATH)) {
      const data = fs.readFileSync(VIDEOS_PATH, 'utf-8');
      return JSON.parse(data);
    }
  } catch (err) {
    console.error('Error reading saved videos:', err);
  }
  return [];
}

export function saveVideoRecord(videoRecord) {
  try {
    const list = loadSavedVideos();
    list.unshift(videoRecord);
    fs.writeFileSync(VIDEOS_PATH, JSON.stringify(list, null, 2), 'utf-8');
    return true;
  } catch (err) {
    console.error('Error saving video record:', err);
    return false;
  }
}

// OAuth Client setup
export function getOAuthClient() {
  const config = loadConfig();
  if (!config.clientId || !config.clientSecret) {
    return null;
  }
  return new google.auth.OAuth2(
    config.clientId,
    config.clientSecret,
    config.redirectUri || 'http://localhost:3000/api/auth/callback'
  );
}

// Generate Google Auth URL
export function generateAuthUrl() {
  const oauth2Client = getOAuthClient();
  if (!oauth2Client) {
    throw new Error('يرجى أولاً إدخال Client ID و Client Secret في الإعدادات لتوليد رابط الربط.');
  }

  const scopes = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/userinfo.profile'
  ];

  return oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: scopes,
    prompt: 'consent'
  });
}

// Handle OAuth callback
export async function handleOAuthCallback(code) {
  const oauth2Client = getOAuthClient();
  if (!oauth2Client) {
    throw new Error('OAuth2 client not configured.');
  }

  const { tokens } = await oauth2Client.getToken(code);
  oauth2Client.setCredentials(tokens);

  // Fetch channel info
  const youtube = google.youtube({ version: 'v3', auth: oauth2Client });
  const response = await youtube.channels.list({
    part: ['snippet', 'statistics', 'brandingSettings'],
    mine: true
  });

  const channelItem = response.data.items?.[0];
  const channelData = channelItem ? {
    id: channelItem.id,
    title: channelItem.snippet.title,
    description: channelItem.snippet.description,
    customUrl: channelItem.snippet.customUrl || '',
    publishedAt: channelItem.snippet.publishedAt,
    thumbnails: channelItem.snippet.thumbnails,
    statistics: channelItem.statistics
  } : null;

  const currentConfig = loadConfig();
  currentConfig.tokens = tokens;
  currentConfig.connected = true;
  currentConfig.mode = 'live';
  if (channelData) {
    currentConfig.channel = channelData;
  }
  saveConfig(currentConfig);

  return { success: true, channel: channelData };
}

// Disconnect Channel
export function disconnectChannel() {
  const currentConfig = loadConfig();
  currentConfig.tokens = null;
  currentConfig.connected = false;
  currentConfig.mode = 'demo';
  saveConfig(currentConfig);
  return { success: true };
}

// Get YouTube Client (with OAuth or API key)
export function getYouTubeClient() {
  const config = loadConfig();
  if (config.tokens && (config.tokens.access_token || config.tokens.refresh_token) && config.clientId && config.clientSecret) {
    const oauth2Client = getOAuthClient();
    oauth2Client.setCredentials(config.tokens);
    return { client: google.youtube({ version: 'v3', auth: oauth2Client }), isOAuth: true };
  }
  if (config.apiKey) {
    return { client: google.youtube({ version: 'v3', auth: config.apiKey }), isOAuth: false };
  }
  return { client: null, isOAuth: false };
}

// Search & Trend Explorer
export async function getTrendingVideos(regionCode = 'US', category = 'all') {
  const { client } = getYouTubeClient();

  if (client) {
    try {
      const response = await client.videos.list({
        part: ['snippet', 'statistics', 'contentDetails'],
        chart: 'mostPopular',
        regionCode: regionCode || 'US',
        maxResults: 20
      });

      if (response.data.items && response.data.items.length > 0) {
        return response.data.items.map((item, idx) => {
          const views = parseInt(item.statistics?.viewCount || '0', 10);
          const likes = parseInt(item.statistics?.likeCount || '0', 10);
          const comments = parseInt(item.statistics?.commentCount || '0', 10);
          const velocity = views > 1000000 ? `${(views / 1000000).toFixed(1)}M مشاهدة` : `${views.toLocaleString()} مشاهدة`;

          return {
            id: item.id || `yt-${idx}`,
            title: item.snippet?.title || 'فيديو متصدر',
            titleEn: item.snippet?.title || 'Trending Video',
            channelTitle: item.snippet?.channelTitle || 'قناة عالمية',
            channelAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&auto=format&fit=crop&q=80',
            views,
            likes,
            comments,
            publishedDaysAgo: 2,
            category: 'challenges',
            thumbnail: item.snippet?.thumbnails?.high?.url || item.snippet?.thumbnails?.default?.url,
            velocity: `${velocity} إجمالي`,
            viralScore: Math.min(99, Math.floor(80 + Math.random() * 20)),
            hookBreakdown: 'عنصر المفاجأة السريعة في أول 3 ثوانٍ مع وتيرة بصرية صاعدة.',
            tags: item.snippet?.tags || ['viral', 'trending', 'youtube'],
            retentionSecret: 'محتوى سريع، عناوين واضحة، وصورة مصغرة عالية التباين والجاذبية.'
          };
        });
      }
    } catch (err) {
      console.warn('Live YouTube API error, falling back to curated trends:', err.message);
    }
  }

  // Fallback to top curated global trends
  let filtered = [...TOP_GLOBAL_TRENDS];
  if (category && category !== 'all') {
    filtered = filtered.filter(item => item.category === category);
    if (filtered.length === 0) filtered = TOP_GLOBAL_TRENDS;
  }
  return filtered;
}

// Search Videos Live or Curated
export async function searchVideos(query = '', regionCode = 'US') {
  if (!query || !query.trim()) {
    return getTrendingVideos(regionCode, 'all');
  }

  const { client } = getYouTubeClient();
  if (client) {
    try {
      const searchRes = await client.search.list({
        part: ['snippet'],
        q: query,
        type: ['video'],
        order: 'viewCount',
        maxResults: 15,
        regionCode: regionCode || 'US'
      });

      const videoIds = searchRes.data.items?.map(i => i.id?.videoId).filter(Boolean);
      if (videoIds && videoIds.length > 0) {
        const statsRes = await client.videos.list({
          part: ['snippet', 'statistics'],
          id: videoIds
        });

        return statsRes.data.items.map(item => {
          const views = parseInt(item.statistics?.viewCount || '0', 10);
          const likes = parseInt(item.statistics?.likeCount || '0', 10);
          const comments = parseInt(item.statistics?.commentCount || '0', 10);

          return {
            id: item.id,
            title: item.snippet?.title || query,
            titleEn: item.snippet?.title || query,
            channelTitle: item.snippet?.channelTitle || 'قناة رائدة',
            channelAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&auto=format&fit=crop&q=80',
            views,
            likes,
            comments,
            publishedDaysAgo: 7,
            category: 'challenges',
            thumbnail: item.snippet?.thumbnails?.high?.url || item.snippet?.thumbnails?.default?.url,
            velocity: views > 1000000 ? `${(views / 1000000).toFixed(1)}M مشاهدة` : `${views.toLocaleString()} مشاهدة`,
            viralScore: Math.min(99, Math.max(70, Math.floor(views / 100000))),
            hookBreakdown: `الفيديو يبدأ فوراً بحل لغز ${query} دون أي مقدمة بطيئة لجذب انتباه المشاهدين في أول ثانيتين.`,
            tags: item.snippet?.tags || [query, 'viral', 'explore'],
            retentionSecret: 'عنوان واعد يثير الفضول الشديد وصورة مصغرة تظهر المشهد الأكثر إثارة.'
          };
        });
      }
    } catch (err) {
      console.warn('Live search error, falling back to simulated query matches:', err.message);
    }
  }

  // Simulated search matches based on query
  const cleanQ = query.toLowerCase();
  const matched = TOP_GLOBAL_TRENDS.filter(item => 
    item.title.toLowerCase().includes(cleanQ) || 
    item.titleEn.toLowerCase().includes(cleanQ) ||
    item.tags.some(t => t.toLowerCase().includes(cleanQ))
  );

  if (matched.length > 0) {
    return matched;
  }

  // Dynamically synthesize high-impact results for this query
  return [
    {
      id: `query-match-1`,
      title: `أكبر تجربة في العالم عن "${query}" مع جوائز خيالية!`,
      titleEn: `The World's Biggest "${query}" Experiment with Extreme Stakes!`,
      channelTitle: 'Cosmic Beast Lab',
      channelAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&auto=format&fit=crop&q=80',
      views: 52100000,
      likes: 3890000,
      comments: 142000,
      publishedDaysAgo: 4,
      category: 'challenges',
      thumbnail: 'https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=600&auto=format&fit=crop&q=80',
      velocity: '13M مشاهدة / يوم',
      viralScore: 99,
      hookBreakdown: `المقدم يقف بجانب أكبر نموذج لـ ${query} ويطلق التحدي في الثانية 1 مباشرة.`,
      tags: [query, 'تحدي', 'mrbeast', 'viral', 'viral video', 'world record'],
      retentionSecret: 'تصوير سينمائي متعدد الكاميرات وإثارة متصاعدة كل 20 ثانية.'
    },
    {
      id: `query-match-2`,
      title: `السر الغامض الذي لا يعرفه أحد عن "${query}" (وثائقي كوني)`,
      titleEn: `The Shocking Hidden Reality of "${query}"`,
      channelTitle: 'Cosmic Documentary',
      channelAvatar: 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=120&auto=format&fit=crop&q=80',
      views: 31400000,
      likes: 2150000,
      comments: 87000,
      publishedDaysAgo: 10,
      category: 'curiosity',
      thumbnail: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80',
      velocity: '3.1M مشاهدة / يوم',
      viralScore: 94,
      hookBreakdown: `طرح سؤال غير تقليدي يربط ${query} بمستقبل البشرية في أول ثانيتين.`,
      tags: [query, 'documentary', 'أسرار', 'kurzgesagt', 'mind blown'],
      retentionSecret: 'مؤثرات بصرية وصوتية ثلاثية الأبعاد لا تترك أي لحظة صمت مملة.'
    }
  ];
}

// Upload Video (Live via YouTube Data API v3 or Smart Simulation)
export async function publishVideo({
  videoFilePath,
  thumbnailFilePath,
  title,
  description,
  tags = [],
  privacyStatus = 'public',
  categoryId = '24', // 24 = Entertainment, 28 = Science & Tech
  isShort = false
}) {
  const config = loadConfig();
  const { client, isOAuth } = getYouTubeClient();

  // If OAuth is configured and connected, do real upload
  if (isOAuth && client && videoFilePath && fs.existsSync(videoFilePath)) {
    try {
      const formattedTitle = isShort && !title.includes('#Shorts') ? `${title} #Shorts` : title;
      const formattedDescription = `${description}\n\n#Viral #Trending #CosmicTube`;

      const res = await client.videos.insert({
        part: ['snippet', 'status'],
        requestBody: {
          snippet: {
            title: formattedTitle,
            description: formattedDescription,
            tags: Array.isArray(tags) ? tags : tags.split(',').map(t => t.trim()),
            categoryId: categoryId || '24',
            defaultLanguage: 'ar'
          },
          status: {
            privacyStatus: privacyStatus || 'public',
            selfDeclaredMadeForKids: false
          }
        },
        media: {
          body: fs.createReadStream(videoFilePath)
        }
      });

      const uploadedVideoId = res.data.id;
      if (!uploadedVideoId) throw new Error('YouTube returned no video ID');
      let thumbnailUploaded = false;

      // Upload thumbnail if provided
      if (thumbnailFilePath && fs.existsSync(thumbnailFilePath) && uploadedVideoId) {
        try {
          await client.thumbnails.set({
            videoId: uploadedVideoId,
            media: {
              body: fs.createReadStream(thumbnailFilePath)
            }
          });
          thumbnailUploaded = true;
        } catch (thumbErr) {
          console.warn('Thumbnail upload warning:', thumbErr.message);
        }
      }

      const videoRecord = {
        id: uploadedVideoId,
        title: formattedTitle,
        description: formattedDescription,
        publishedAt: new Date().toISOString(),
        privacyStatus,
        url: `https://youtu.be/${uploadedVideoId}`,
        thumbnailUrl: thumbnailFilePath ? `/uploads/${path.basename(thumbnailFilePath)}` : 'https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=600&auto=format&fit=crop&q=80',
        liveUploaded: true,
        channelTitle: config.channel?.title || 'قناتك الرسمية',
        views: 0,
        likes: 0
      };

      saveVideoRecord(videoRecord);
      return { success: true, video: videoRecord, message: 'تم نشر الفيديو بنجاح على قناتك في يوتيوب!' };
    } catch (uploadErr) {
      console.error('YouTube API upload failed:', uploadErr);
      throw new Error(`فشل الرفع عبر API يوتيوب: ${uploadErr.message}`);
    }
  }

  throw new Error('النشر الحقيقي يتطلب ربط OAuth صالحًا وملف فيديو موجودًا؛ لم يتم نشر أي فيديو.');
}
