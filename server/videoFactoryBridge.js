// Video Factory Bridge — Connects Node.js platform with Python 2099 Montage Engine
import { exec, spawn } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { TOP_GLOBAL_TRENDS, generateInfiniteViralIdeas } from './viralEngine.js';

const execPromise = util.promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.join(__dirname, '..');
const VIDS_DIR = path.join(ROOT_DIR, 'content', 'vids');
const TOPICS_PATH = path.join(ROOT_DIR, 'content', 'topics.json');

// Ensure vids directory exists
if (!fs.existsSync(VIDS_DIR)) {
  fs.mkdirSync(VIDS_DIR, { recursive: true });
}

let activeJobs = {};

export function listAvailableTopics() {
  const topics = [];

  // 1. Add top global viral radar trends
  for (const tr of TOP_GLOBAL_TRENDS) {
    topics.push({
      id: tr.id,
      angle: tr.title,
      title_ar: tr.title,
      title_en: tr.titleEn,
      hook_ar: tr.hookBreakdown || `في الثانية الأولى، يحدث الحدث الصاعق الذي لا يصدقه عقل!`,
      hook_en: `In the first second, the impossible spectacle begins!`,
      category: tr.category,
      facts_ar: [
        `في الدقيقة الأولى: تصعيد التحدي ورفع الرهان لأقصى حد ممكن تحت مراقبة الكاميرات.`,
        `المنعطف الأوسط: حدث غير متوقع كلياً يقلب الموازين ويصدم المشاهدين.`,
        `اللحظة الحاسمة: النتيجة الصادمة التي كسرت الأرقام القياسية واجتاحت العالم.`
      ],
      facts_en: [
        `Minute 1: Escalating the challenge stakes to maximum intensity.`,
        `Mid-twist: Totally unexpected twist completely flips the table.`,
        `The Climax: Shocking conclusion that broke world records.`
      ],
      outro_ar: 'اشترك الآن في القناة الكونية CosmicTube عشان تشوف التحديات القادمة!',
      outro_en: 'Subscribe to CosmicTube for the next impossible viral challenge!',
      tags: tr.tags ? tr.tags.join(',') : 'viral,mrbeast,challenges,trending',
      thumbnail: tr.thumbnail,
      viewsEst: `${(tr.views / 1000000).toFixed(1)}M`,
      ctr: '17.8%',
      viralScore: tr.viralScore,
      themeColor: tr.category === 'challenges' ? '#ef4444' : tr.category === 'science' ? '#8b5cf6' : '#f59e0b',
      bgGradient: tr.category === 'challenges' 
        ? 'from-red-950 via-slate-950 to-slate-900' 
        : tr.category === 'science' 
        ? 'from-purple-950 via-slate-950 to-blue-950' 
        : 'from-amber-950 via-slate-950 to-emerald-950'
    });
  }

  // 2. Add infinite viral matrix ideas
  const infiniteIdeas = generateInfiniteViralIdeas(10);
  for (let i = 0; i < infiniteIdeas.length; i++) {
    const inf = infiniteIdeas[i];
    topics.push({
      id: inf.id,
      angle: inf.titleAr,
      title_ar: inf.titleAr,
      title_en: inf.titleEn,
      hook_ar: inf.hook3s,
      hook_en: 'In second zero, the countdown timer ticks down with heart-stopping sirens!',
      category: inf.niche,
      facts_ar: [
        `المرحلة الأولى: اختبار القواعد المستحيلة تحت أعين الكاميرات بدقة متناهية.`,
        `المرحلة الثانية: انهيار كل التوقعات ومفاجأة غير مسبوقة تصدم الجميع.`,
        `الخاتمة: إعلان الفائز الصامد وجائزة التحدي الخيالية وسط احتفال أسطوري.`
      ],
      facts_en: [
        `Stage 1: Testing impossible rules on camera under extreme pressure.`,
        `Stage 2: Complete collapse of expectations with surprise.`,
        `Climax: Final survivor crowned with historic prize.`
      ],
      outro_ar: 'اشترك بالقناة الكونية CosmicTube واكتب في التعليقات التحدي اللي تريده!',
      outro_en: 'Subscribe to CosmicTube and comment your challenge idea!',
      tags: inf.tags ? inf.tags.join(',') : 'viral,challenge,shorts',
      thumbnail: 'https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=600&auto=format&fit=crop&q=80',
      viewsEst: inf.predictedViews,
      ctr: inf.predictedCtr,
      viralScore: inf.viralScore,
      themeColor: inf.niche === 'challenges' ? '#ef4444' : inf.niche === 'science' ? '#8b5cf6' : '#10b981',
      bgGradient: inf.niche === 'challenges'
        ? 'from-red-950 via-slate-950 to-slate-900'
        : inf.niche === 'science'
        ? 'from-indigo-950 via-slate-950 to-cyan-950'
        : 'from-emerald-950 via-slate-950 to-amber-950'
    });
  }

  // 3. Fallback to existing topics if any
  try {
    if (fs.existsSync(TOPICS_PATH)) {
      const data = JSON.parse(fs.readFileSync(TOPICS_PATH, 'utf-8'));
      for (const t of data) {
        if (!topics.some(x => x.id === t.id)) {
          topics.push(t);
        }
      }
    }
  } catch (err) {
    // ignore
  }

  return topics;
}

// Deterministic production queue: authored episodes first, then the viral radar.
// The "infinite ideas" generator is intentionally excluded — it returns a fresh
// random id and fabricated metrics on every call, so nothing could ever be
// deduplicated against it and no real episode could be tracked.
export function listProductionQueue() {
  return listAvailableTopics()
    .filter(t => t.id && !String(t.id).startsWith('infinite-'))
    .map(t => ({
      ...t,
      source: (t.id.startsWith('ep') || t.id.startsWith('auto-')) ? 'authored' : 'radar'
    }));
}

export function listProducedVideos() {
  try {
    if (!fs.existsSync(VIDS_DIR)) return [];
    const topics = listAvailableTopics();
    const topicMap = {};
    for (const t of topics) {
      if (t.id) topicMap[t.id] = t;
    }

    const files = fs.readdirSync(VIDS_DIR).filter(f => f.endsWith('.mp4'));
    return files.map(file => {
      const filePath = path.join(VIDS_DIR, file);
      const stat = fs.statSync(filePath);
      const id = file.replace('.mp4', '');
      const meta = topicMap[id] || {};
      const title = meta.title_ar || meta.title_en || meta.angle || (id === 'ep1' ? 'جسمك فيه نجوم حقيقية… والدليل هيصدمك!' : `حلقة إنتاجية ${id}`);
      return {
        id,
        filename: file,
        path: filePath,
        url: `/content/vids/${file}`,
        sizeMB: (stat.size / (1024 * 1024)).toFixed(1),
        createdAt: stat.mtime.toISOString(),
        title,
        hook: meta.hook_ar || meta.hook_en || '',
        category: meta.category || 'Science & Mystery'
      };
    }).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  } catch (err) {
    console.error('Error listing produced vids:', err);
    return [];
  }
}

export async function startProduceJob(topicInput = 'ep1') {
  const jobId = `job_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  
  let targetTopic = null;
  const topics = listAvailableTopics();
  if (typeof topicInput === 'string') {
    targetTopic = topics.find(t => t.id === topicInput) || topics[0];
  } else if (topicInput && typeof topicInput === 'object') {
    targetTopic = topicInput;
  } else {
    targetTopic = topics[0];
  }

  const topicId = targetTopic.id || `topic_${Date.now()}`;
  const topicJsonPath = `/tmp/target_topic_${jobId}.json`;
  fs.writeFileSync(topicJsonPath, JSON.stringify(targetTopic, null, 2), 'utf-8');

  activeJobs[jobId] = {
    jobId,
    topicId,
    title: targetTopic.title_ar || targetTopic.title || 'فيديو فيروسي',
    status: 'processing',
    progress: 10,
    stage: 'جاري اختيار وفحص السيناريو الكوني والفيروسي من الرادار ومصفوفة الملايير...',
    startedAt: new Date().toISOString(),
    outputVideo: null,
    error: null
  };

  // Run in background
  (async () => {
    try {
      activeJobs[jobId].progress = 25;
      activeJobs[jobId].stage = 'توليد وهندسة السرد الصوتي والمؤثرات الصوتية والخطاف الصاعق...';

      const script = `
from xtrendaw import produce
from pathlib import Path
import json

with open('${topicJsonPath}', 'r', encoding='utf-8') as f:
    target_topic = json.load(f)

workdir = Path('/tmp/work_${jobId}')
res = produce.produce_episode(target_topic, workdir)
plan = res.get("plan") or {}
audio_sources = sorted({(it.get("timing_source") or "unknown") for it in plan.get("items", [])})
report_path = workdir / "report.json"
report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None
print(json.dumps({
    "ok": True,
    "video": str(res["video"]),
    "cover": str(res.get("cover") or ""),
    "episode": target_topic["id"],
    "title": target_topic.get("title_ar", ""),
    "audio_sources": audio_sources,
    "report": report
}, ensure_ascii=False))
`;

      activeJobs[jobId].progress = 50;
      activeJobs[jobId].stage = 'بناء المشاهد السينمائية النيونية ودوائر الـ HUD وحبيبات السرعة...';

      const pyProcess = spawn('python3', ['-c', script], {
        cwd: ROOT_DIR
      });

      let stdout = '';
      let stderr = '';

      pyProcess.stdout.on('data', (d) => { stdout += d.toString(); });
      pyProcess.stderr.on('data', (d) => { stderr += d.toString(); });

      // Progress simulation during ffmpeg rendering
      const interval = setInterval(() => {
        if (activeJobs[jobId] && activeJobs[jobId].progress < 90) {
          activeJobs[jobId].progress += 5;
          if (activeJobs[jobId].progress > 75) {
            activeJobs[jobId].stage = 'المونتاج السينمائي النهائي ودمج الكابتشنز بـ FFmpeg...';
          }
        }
      }, 5000);

      pyProcess.on('error', (err) => {
        clearInterval(interval);
        activeJobs[jobId].status = 'error';
        activeJobs[jobId].error = err.message;
      });

      pyProcess.on('close', (code) => {
        clearInterval(interval);
        try { fs.unlinkSync(topicJsonPath); } catch (_) {}

        if (code === 0) {
          try {
            const outPath = path.join(VIDS_DIR, `${topicId}.mp4`);
            if (!fs.existsSync(outPath) || fs.statSync(outPath).size === 0) {
              throw new Error('Renderer did not produce a nonempty MP4');
            }

            // The renderer prints one JSON line with the real ffprobe report.
            let renderReport = null;
            let audioSources = [];
            let coverPath = null;
            const reportLine = stdout
              .split('\n')
              .map(l => l.trim())
              .filter(l => l.startsWith('{'))
              .pop();
            if (reportLine) {
              try {
                const parsed = JSON.parse(reportLine);
                renderReport = parsed.report || null;
                audioSources = Array.isArray(parsed.audio_sources) ? parsed.audio_sources : [];
                if (parsed.cover && fs.existsSync(parsed.cover)) coverPath = parsed.cover;
              } catch (_) {
                // keep going; the file checks below still apply
              }
            }
            if (!coverPath) {
              const fallbackCover = path.join(VIDS_DIR, `${topicId}-cover.png`);
              if (fs.existsSync(fallbackCover)) coverPath = fallbackCover;
            }

            const validation = renderReport?.validate || null;
            if (validation && validation.ok === false) {
              const failed = Object.entries(validation.checks || {})
                .filter(([, ok]) => !ok)
                .map(([name]) => name);
              throw new Error(`Rendered MP4 failed spec validation: ${failed.join(', ')}`);
            }

            activeJobs[jobId].status = 'completed';
            activeJobs[jobId].progress = 100;
            activeJobs[jobId].stage = '✅ تم إنتاج حلقة الفيديو MP4 بنجاح وجاهزة للعرض والنشر!';
            activeJobs[jobId].outputVideo = {
              id: topicId,
              filename: `${topicId}.mp4`,
              url: `/content/vids/${topicId}.mp4`,
              filePath: outPath,
              coverPath,
              title: targetTopic.title_ar || targetTopic.title,
              sizeBytes: fs.statSync(outPath).size,
              audioSources,
              report: renderReport
            };
          } catch (e) {
            activeJobs[jobId].status = 'error';
            activeJobs[jobId].error = e.message;
          }
        } else {
          activeJobs[jobId].status = 'error';
          activeJobs[jobId].error = stderr || `Exit code ${code}`;
        }
      });

    } catch (err) {
      activeJobs[jobId].status = 'error';
      activeJobs[jobId].error = err.message;
    }
  })();

  return activeJobs[jobId];
}

export function getJobStatus(jobId) {
  return activeJobs[jobId] || null;
}
