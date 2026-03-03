/**
 * 工具函数
 */

/**
 * 解析行数（粗略估计）
 */
export const parseLineCount = (text: string): number => {
  if (!text) return 0;
  const lines = text.split('\n').filter(line => line.trim());
  return lines.length;
};

/**
 * 转换字节为可读大小
 */
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 转换秒数为可读时长
 */
export const formatDuration = (seconds: number): string => {
  if (!seconds || seconds === 0) return '--:--';
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  return `${min}:${sec.toString().padStart(2, '0')}`;
};
