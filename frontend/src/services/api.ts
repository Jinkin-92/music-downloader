/**
 * API客户端配置
 *
 * 封装axios，提供类型安全的API调用
 */
import axios, { AxiosError } from 'axios';

/**
 * API基础配置
 */
export const api = axios.create({
  baseURL: '/api',
  timeout: 900000, // 900秒（15分钟）- 批量搜索大量歌曲需要更长时间
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 请求拦截器（可选）
 */
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器
 */
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // 统一错误处理
    console.error('API Error:', error.message);

    if (error.response) {
      // 服务器返回错误状态码
      const status = error.response.status;
      const message = (error.response.data as any)?.detail || error.message;

      return Promise.reject({
        status,
        message,
        originalError: error,
      });
    } else if (error.request) {
      // 请求已发出但没有收到响应
      return Promise.reject({
        message: '网络错误，请检查网络连接',
        originalError: error,
      });
    } else {
      // 请求配置错误
      return Promise.reject({
        message: error.message,
        originalError: error,
      });
    }
  }
);

/**
 * API端点
 * 注意：baseURL已包含/api前缀，这里不需要再重复
 */
export const apiEndpoints = {
  // 搜索
  sources: '/search/sources',
  search: '/search/',
  batchSearch: '/search/batch',

  // 批量
  batchParse: '/batch/parse',
  batchMatch: '/batch/match',

  // 歌单
  playlistParse: '/playlist/parse',
  playlistPlatforms: '/playlist/platforms',

  // 下载
  downloadStart: '/download/start',
  downloadStatus: (taskId: string) => `/download/status/${taskId}`,
  downloadFiles: '/download/files',

  // SSE流
  streamDownload: (taskId: string) => `/stream/download/${taskId}`,
  streamBatchSearch: (taskId: string) => `/stream/batch-search/${taskId}`,

  // 系统
  health: '/health',
  logs: '/logs',
};

/**
 * 搜索API
 */
export const searchApi = {
  /**
   * 获取音乐源列表
   */
  getSources: () => api.get(apiEndpoints.sources),

  /**
   * 单曲搜索
   */
  searchMusic: (keyword: string, sources?: string[]) =>
    api.post(apiEndpoints.search, {
      keyword,
      sources: sources || null,
    }),

  /**
   * 批量搜索
   */
  batchSearch: (text: string, sources?: string[], concurrency?: number) =>
    api.post(apiEndpoints.batchSearch, {
      text,
      sources: sources || null,
      concurrency: concurrency || 20,  // 修复：使用20作为默认值
    }),
};

/**
 * 批量API
 */
export const batchApi = {
  /**
   * 解析批量文本
   */
  parseText: (text: string) =>
    api.post(apiEndpoints.batchParse, { text }),

  /**
   * 批量匹配
   */
  batchMatch: (songs: any[], sources?: string[]) =>
    api.post(apiEndpoints.batchMatch, {
      songs,
      sources: sources || null,
    }),
};

/**
 * 下载API
 */
export const downloadApi = {
  /**
   * 开始下载
   */
  startDownload: (songs: any[], downloadDir?: string) =>
    api.post(apiEndpoints.downloadStart, {
      songs,
      download_dir: downloadDir,
    }),

  /**
   * SSE流式下载 - 实时推送下载进度
   * @param songs 歌曲列表
   * @param downloadDir 下载目录（可选）
   * @returns SSE EventSource URL
   */
  streamDownloadUrl: (songs: any[], downloadDir?: string) => {
    const songsJson = JSON.stringify(songs);
    const params = new URLSearchParams({ songs_json: songsJson });
    if (downloadDir) {
      params.append('download_dir', downloadDir);
    }
    return `/api/download/stream?${params.toString()}`;
  },

  /**
   * 获取下载状态
   */
  getStatus: (taskId: string) =>
    api.get(apiEndpoints.downloadStatus(taskId)),

  /**
   * 获取已下载文件列表
   */
  getFiles: () => api.get(apiEndpoints.downloadFiles),
};

/**
 * 歌单API
 */
export const playlistApi = {
  /**
   * 解析歌单URL
   */
  parsePlaylist: (url: string) =>
    api.post(apiEndpoints.playlistParse, { url }),

  /**
   * 批量搜索歌单歌曲（POST - 返回完整结果）
   */
  batchSearchPlaylist: (request: {
    songs: { name: string; artist: string; album: string }[];
    sources?: string[];
    concurrency?: number;
  }) => api.post('/playlist/batch-search', request),

  /**
   * 启动后台批量搜索任务
   * 返回task_id，可轮询查询进度
   */
  startBatchSearch: (request: {
    songs: { name: string; artist: string; album: string }[];
    sources?: string[];
    concurrency?: number;
    filter_duplicates?: boolean;
    similarity_threshold?: number;
  }) => api.post('/playlist/batch-search-start', request),

  /**
   * 查询后台搜索任务状态
   */
  getBatchSearchStatus: (taskId: string) =>
    api.get(`/playlist/batch-search-status/${taskId}`),

  /**
   * 取消后台搜索任务
   */
  cancelBatchSearch: (taskId: string) =>
    api.delete(`/playlist/batch-search-status/${taskId}`),

  /**
   * 批量搜索歌单歌曲（SSE流式 - GET请求）
   * @param songsJson JSON字符串格式的歌曲列表
   * @param sources 逗号分隔的音乐源
   * @param concurrency 并发数
   * @param similarityThreshold 相似度阈值 (0.0-1.0)
   * @returns SSE EventSource URL
   */
  batchSearchStreamUrl: (songsJson: string, sources?: string, concurrency = 5, similarityThreshold?: number) => {
    const params = new URLSearchParams({
      songs_json: songsJson,
      concurrency: concurrency,
    });
    if (sources) {
      params.append('sources', sources);
    }
    if (similarityThreshold !== undefined) {
      params.append('similarity_threshold', similarityThreshold.toString());
    }
    return `/api/playlist/batch-search-stream?${params.toString()}`;
  },

  /**
   * 获取支持的平台
   */
  getPlatforms: () => api.get(apiEndpoints.playlistPlatforms),
};

/**
 * SSE连接
 */
export const connectSSE = (url: string, onMessage: (data: any) => void, onError?: (error: any) => void) => {
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('SSE parse error:', error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    if (onError) {
      onError(error);
    }
    // 如果连接失败，EventSource会自动重试
  };

  return eventSource;
};

export default api;
