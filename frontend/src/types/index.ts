/**
 * TypeScript类型定义
 */

/**
 * 音乐源
 */
export interface Source {
  value: string;
  label: string;
}

/**
 * 歌曲信息
 */
export interface Song {
  song_name: string;
  singers: string;
  album: string;
  size: string;
  duration: string;
  source: string;
  _fallback_candidates?: Song[];
}

/**
 * 搜索结果
 */
export interface SearchResult {
  success: boolean;
  keyword: string;
  total: number;
  songs: Song[];
}

/**
 * 批量匹配信息
 */
export interface BatchMatchInfo {
  query_name: string;
  query_singer: string;
  song_name: string;
  singers: string;
  album: string;
  size: string;
  duration: string;
  source: string;
  similarity: number;
  has_candidates: boolean;
  all_candidates?: Record<string, MatchCandidate[]>;
  _raw_match?: any; // 保存原始匹配数据，用于候选源切换
  // 相似度分解字段
  name_similarity?: number;
  singer_similarity?: number;
  album_similarity?: number;
}

/**
 * 批量搜索结果
 */
export interface BatchSearchResult {
  success: boolean;
  total: number;
  matched: number;
  matches: BatchMatchInfo[];
}

/**
 * 匹配候选（V2版本 - 用于歌单导入）
 */
export interface MatchCandidate {
  song_name: string;
  singers: string;
  album: string;
  size: string;
  duration: string;
  source: string;
  similarity: number;
  // 下载相关字段
  download_url?: string;   // 直接下载URL
  duration_s?: number;      // 时长（秒），用于过滤
  ext?: string;             // 文件扩展名
  song_id?: string;         // 缓存ID，用于获取SongInfo对象
  // 相似度分解字段
  name_similarity?: number;    // 歌名相似度
  singer_similarity?: number;  // 歌手相似度
  album_similarity?: number;   // 专辑相似度
}

/**
 * 批量匹配信息V2（用于歌单导入）
 */
export interface BatchMatchInfoV2 {
  query_name: string;
  query_singer: string;
  current_match: MatchCandidate | null;
  all_matches: Record<string, MatchCandidate[]>;
  has_match: boolean;
}

/**
 * 批量搜索结果V2（用于歌单导入）
 */
export interface BatchSearchResultV2 {
  success: boolean;
  total: number;
  matched: number;
  matches: BatchMatchInfoV2[];
}

/**
 * 批量解析请求
 */
export interface BatchParseRequest {
  text: string;
}

/**
 * 批量解析响应
 */
export interface BatchParseResponse {
  success: boolean;
  total: number;
  songs: ParsedSong[];
}

/**
 * 解析后的歌曲
 */
export interface ParsedSong {
  name: string;
  singer: string;
  album: string;
}

/**
 * 下载请求
 */
export interface DownloadRequest {
  songs: Song[];
  download_dir?: string;
}

/**
 * 下载响应
 */
export interface DownloadResponse {
  success: boolean;
  message: string;
  total: number;
  task_id: string;
}

/**
 * 任务状态
 */
export interface TaskStatus {
  status: 'pending' | 'progress' | 'success' | 'failed';
  progress: number;
  result?: any;
  error?: string;
}

/**
 * UI状态（Zustand）
 */
export interface UIState {
  theme: 'light' | 'dark';
  selectedSources: string[];
  matchMode: 'strict' | 'standard' | 'loose';
  toggleSource: (source: string) => void;
  setMatchMode: (mode: UIState['matchMode']) => void;
}

/**
 * 音乐源列表
 */
export const SOURCES: Source[] = [
  { value: 'QQMusicClient', label: 'QQ音乐' },
  { value: 'NeteaseMusicClient', label: '网易云' },
  { value: 'KugouMusicClient', label: '酷狗' },
  { value: 'KuwoMusicClient', label: '酷我' },
];

/**
 * 默认音乐源
 */
export const DEFAULT_SOURCES = SOURCES.map(s => s.value);

/**
 * 匹配模式选项
 */
export const MATCH_MODES = {
  strict: {
    label: '严格',
    value: 0.7,
    description: '只接受高相似度匹配（≥70%），减少误匹配但可能漏掉部分歌曲'
  },
  standard: {
    label: '标准',
    value: 0.6,
    description: '平衡的匹配策略（≥60%），在准确度和覆盖率之间取得平衡'
  },
  loose: {
    label: '宽松',
    value: 0.5,
    description: '接受更多可能的匹配（≥50%），提高匹配成功率但可能包含不准确结果'
  },
};
