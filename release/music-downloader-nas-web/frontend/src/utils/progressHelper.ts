/**
 * 进度计算辅助工具
 */

/**
 * 计算搜索/下载速度
 */
export function calculateSpeed(
  completed: number,
  startTime: number
): number {
  const elapsed = (Date.now() - startTime) / 1000; // 秒
  if (elapsed === 0) return 0;
  return completed / elapsed;
}

/**
 * 估算剩余时间（秒）
 */
export function estimateRemainingTime(
  completed: number,
  total: number,
  speed: number
): number {
  if (speed === 0) return 0;
  const remaining = total - completed;
  return Math.ceil(remaining / speed);
}

/**
 * 格式化时间显示
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}秒`;
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}小时${mins}分`;
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

/**
 * 估算下载文件总大小
 */
export function estimateDownloadSize(
  songCount: number,
  avgFileSize: number = 5 * 1024 * 1024 // 默认5MB/首
): string {
  return formatFileSize(songCount * avgFileSize);
}
