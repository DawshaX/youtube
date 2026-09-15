// Video Factory Bridge — Connects Node.js platform with Python 2099 Montage Engine
import { exec, spawn } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

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
  try {
    if (fs.existsSync(TOPICS_PATH)) {
      const data = JSON.parse(fs.readFileSync(TOPICS_PATH, 'utf-8'));
      return data;
    }
  } catch (err) {
    console.error('Error reading topics:', err);
  }
  return [];
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

export async function startProduceJob(topicId = 'ep1') {
  const jobId = `job_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  
  activeJobs[jobId] = {
    jobId,
    topicId,
    status: 'processing',
    progress: 10,
    stage: 'جاري اختيار وفحص السيناريو الكوني 2099...',
    startedAt: new Date().toISOString(),
    outputVideo: null,
    error: null
  };

  // Run in background
  (async () => {
    try {
      activeJobs[jobId].progress = 25;
      activeJobs[jobId].stage = 'توليد وهندسة السرد الصوتي والمؤثرات الصوتية...';

      const script = `
from xtrendaw import content, produce
from pathlib import Path
import json

topics = content.load_topics()
target_topic = None
for t in topics:
    if t["id"] == "${topicId}":
        target_topic = t
        break
if not target_topic:
    target_topic = topics[0]

workdir = Path('/tmp/work_${jobId}')
res = produce.produce_episode(target_topic, workdir)
print(json.dumps({"ok": True, "video": str(res["video"]), "episode": target_topic["id"], "title": target_topic.get("title_ar", "")}))
`;

      activeJobs[jobId].progress = 50;
      activeJobs[jobId].stage = 'بناء وتوليد المشاهد النيونية 2099 وحبيبات الفضاء...';

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

      pyProcess.on('close', (code) => {
        clearInterval(interval);
        if (code === 0) {
          try {
            const outPath = path.join(VIDS_DIR, `${topicId}.mp4`);
            activeJobs[jobId].status = 'completed';
            activeJobs[jobId].progress = 100;
            activeJobs[jobId].stage = '✅ تم إنتاج حلقة الفيديو MP4 بنجاح وجاهزة للعرض والنشر!';
            activeJobs[jobId].outputVideo = {
              id: topicId,
              filename: `${topicId}.mp4`,
              url: `/content/vids/${topicId}.mp4`,
              filePath: outPath
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
