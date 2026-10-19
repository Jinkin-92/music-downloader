import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import * as path from 'path';

/**
 * Playwright 全局设置：每次套件运行前重置测试下载状态。
 * 修复 E2E 套件不可重复执行的问题——下载历史跨运行累积后，
 * 二次运行时批量搜索会因"全部歌曲已下载"而全部跳过。
 * 仅清理测试夹具目录 test_downloads/ 与测试产生的下载历史。
 */
export default function globalSetup(): void {
  console.log('[global-setup] 重置测试下载状态，保证套件可重复执行...');
  const e2eDir = path.dirname(fileURLToPath(import.meta.url));
  try {
    const pythonBin = path.resolve(e2eDir, '../../.venv/bin/python');
    const resetScript = path.resolve(e2eDir, 'reset_test_state.py');
    execSync(`"${pythonBin}" "${resetScript}"`, { stdio: 'inherit', timeout: 30000 });
  } catch (e) {
    // 重置失败不阻断测试，仅告警（可能影响可重复性）
    console.warn('[global-setup] 重置下载状态失败（继续执行）:', (e as Error).message);
  }
}
