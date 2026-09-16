// Video Factory Bridge — Connects Node.js platform with Python 2099 Montage Engine
//
// سياسة الكتالوج (بلا أي اختلاق): مواضيع الإنتاج بتيجي حصريًا من ملفات
// الكتالوج الموجودة في المستودع:
//   content/topics_daousha.json  — كتالوج الـ509 موضوع المعدّين (الأساس)
//   content/topics.json          — الحلقات المؤلّفة يدويًا (احتياطي)
// نُهِى عن هنا السكربت المكرر (نص facts_ar ثابت متطابق كان بيتركب على كل
// موضوع) ومعاه مولد الأفكار العشوائية وأرقام المشاهدات المختلقة. الرادار
// نفسه لسه معروض للعرض فقط عبر /api/trends — بس مايقدرش يقود الإنتاج
// من غير سيناريو حقيقي مكتوب في الكتالوج.
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.join(__dirname, '..');
const VIDS_DIR = path.join(ROOT_DIR, 'content', 'vids');
const TOPICS_PATH = path.join(ROOT_DIR, 'content', 'topics.json');
const DAOUSHA_PATH = path.join(ROOT_DIR, 'content', 'topics_daousha.json');

// Ensure vids directory exists
if (!fs.existsSync(VIDS_DIR)) {
  fs.mkdirSync(VIDS_DIR, { recursive: true });
}

let activeJobs = {};

function readJsonSafe(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch (err) {
    return null;
  }
}

function scriptLineFacts(raw) {
  const lines = Array.isArray(raw?.script?.lines_ar) ? raw.script.lines_ar : [];
  return lines
    .filter(l => l && typeof l.text === 'string' && String(l.seg || '').startsWith('fact'))
    .map(l => l.text.trim())
    .filter(Boolean);
}

// Normalizes one entry of topics_daousha.json into the platform topic shape,
// using only the entry's own authored fields — never shared filler text.
function normalizeDaoushaTopic(raw) {
  const lines = Array.isArray(raw?.script?.lines_ar) ? raw.script.lines_ar : [];
  const hook = String(
    raw?.hook_ar || (lines.find(l => l && l.seg === 'hook') || {}).text || ''
  ).trim();
  const facts = Array.isArray(raw?.facts_ar) && raw.facts_ar.length
    ? raw.facts_ar.map(f => String(f).trim()).filter(Boolean)
    : scriptLineFacts(raw);
  const done = ['published', 'produced'].includes(raw?.status);
  const tags = Array.isArray(raw?.tags)
    ? raw.tags.join(',')
    : (typeof raw?.tags === 'string' ? raw.tags : '');
  return {
    id: raw?.id,
    angle: raw?.angle || raw?.topic || '',
    topic: raw?.topic || '',
    title_ar: raw?.title_ar || raw?.topic || raw?.angle || raw?.id,
    title_en: raw?.title_en || '',
    hook_ar: hook,
    hook_en: raw?.hook_en || '',
    facts_ar: facts,
    facts_en: Array.isArray(raw?.facts_en) ? raw.facts_en : [],
    outro_ar: raw?.outro_ar || '',
    outro_en: raw?.outro_en || '',
    tags,
    _visual_queries: Array.isArray(raw?.scene_queries) ? raw.scene_queries : [],
    category: raw?.theme || 'science',
    status: raw?.status || 'queued',
    origin: raw?.origin || '',
    catalog: 'daousha',
    producible: !done && Boolean(hook && facts.length),
    done
  };
}

// الكتالوج الرئيسي: 509 موضوع من content/topics_daousha.json
export function loadDaoushaTopics() {
  const data = readJsonSafe(DAOUSHA_PATH);
  if (!Array.isArray(data)) return [];
  return data.map(normalizeDaoushaTopic).filter(t => t.id);
}

export function listAvailableTopics() {
  const topics = [];

  // 1. الكتالوج الرئيسي — كل مواضيع دوّشة بسيناريوهاتها الحقيقية
  for (const t of loadDaoushaTopics()) {
    topics.push(t);
  }

  // 2. الحلقات المؤلّفة يدويًا (content/topics.json). عند تصادم نفس الـid
  //    مع مدخل دوّشة، المؤلَّف يكسب: سجل الإنتاج والروابط المنشورة
  //    متعلقة بالـid ده من تاريخ المستودع ده بالذات.
  const authored = readJsonSafe(TOPICS_PATH);
  if (Array.isArray(authored)) {
    for (const t of authored) {
      if (!t || !t.id) continue;
      const idx = topics.findIndex(x => x.id === t.id);
      const wrapped = {
        ...t,
        category: t.category || 'authored',
        producible: Boolean(t.hook_ar && (t.facts_ar || []).length),
        done: false
      };
      if (idx >= 0) topics[idx] = wrapped;
      else topics.push(wrapped);
    }
  }

  return topics;
}

// Deterministic production queue: only catalog topics carrying a real,
// complete script (hook + facts) may drive production. Radar entries and
// random "infinite ideas" are deliberately excluded — they carry no authored
// script and fabricated metrics, so nothing real could ever be produced
// from them.
export function listProductionQueue() {
  return listAvailableTopics()
    .filter(t => t.id && t.producible && !String(t.id).startsWith('infinite-'))
    .map(t => ({
      ...t,
      source: t.catalog === 'daousha'
        ? 'daousha'
        : ((t.id.startsWith('ep') || t.id.startsWith('auto-')) ? 'authored' : 'radar')
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
    // No silent substitution: an explicitly requested id that is not in the
    // catalog must fail loudly.
    targetTopic = topics.find(t => t.id === topicInput) || null;
    if (!targetTopic) {
      throw new Error(`Topic not found in the catalog: ${topicInput}`);
    }
  } else if (topicInput && typeof topicInput === 'object') {
    targetTopic = topicInput;
  } else {
    // No explicit choice → first catalog topic with a complete authored script.
    targetTopic = topics.find(t => t.producible) || null;
    if (!targetTopic) {
      throw new Error('The catalog holds no producible topic (hook + facts).');
    }
  }
  if (!targetTopic.id) {
    throw new Error('Selected topic has no id — refusing to render.');
  }
  if (targetTopic.producible === false) {
    throw new Error(
      `Topic ${targetTopic.id} has no authored script (hook + facts) in the catalog — refusing to render filler.`
    );
  }
  const topicId = targetTopic.id;
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
