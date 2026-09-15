// GitHub Cloud Storage & Production Backup Sync
import { exec } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const execPromise = util.promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.join(__dirname, '..');

export async function getGitHubStatus() {
  try {
    const { stdout: branch } = await execPromise('git branch --show-current', { cwd: ROOT_DIR });
    const { stdout: lastCommit } = await execPromise('git log -1 --pretty=format:"%h - %s (%cr)"', { cwd: ROOT_DIR });
    const { stdout: statusOut } = await execPromise('git status -s', { cwd: ROOT_DIR });

    return {
      connected: true,
      branch: branch.trim(),
      lastCommit: lastCommit.trim(),
      hasUncommittedChanges: statusOut.trim().length > 0,
      repository: 'DawshaX/youtube',
      storageEngine: 'GitHub Native Cloud Storage'
    };
  } catch (err) {
    return {
      connected: false,
      error: err.message
    };
  }
}

export async function syncToGitHub(commitMsg = 'chore: auto-sync cosmic channel data and video archives') {
  try {
    // 1. Stage changes in data/
    await execPromise('git add data/', { cwd: ROOT_DIR });
    
    // Check if there are staged changes
    const { stdout: diff } = await execPromise('git diff --cached --name-only', { cwd: ROOT_DIR });
    
    if (diff.trim().length > 0) {
      await execPromise(`git commit -m "${commitMsg}"`, { cwd: ROOT_DIR });
      await execPromise('git push origin arena/01a0a5d4-youtube', { cwd: ROOT_DIR });
      return { success: true, message: 'تمت مزامنة وحفظ كافة بيانات القناة وسجل الفيديوهات على GitHub بنجاح!' };
    }

    return { success: true, message: 'كافة بيانات القناة وسجل الفيديوهات متزامنة ومحفوظة مسبقاً على سحابة GitHub!' };
  } catch (err) {
    console.error('GitHub sync error:', err);
    throw new Error(`فشل المزامنة مع سحابة GitHub: ${err.message}`);
  }
}
