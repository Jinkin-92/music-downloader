/**
 * 自定义Hooks - SSE实时进度推送
 *
 * 用于连接SSE端点，接收实时进度更新
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { connectSSE, api } from '../services/api';

/**
 * SSE进度数据
 */
interface SSEProgress {
  status: 'pending' | 'progress' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
  [key: string]: any;
}

/**
 * 使用SSE Hook
 *
 * @param url SSE端点URL
 * @returns { data, progress, status, error, isConnected }
 */
export function useSSE(url: string) {
  const [data, setData] = useState<SSEProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // 防止重复连接
    if (eventSourceRef.current) {
      return;
    }

    try {
      // 连接SSE
      const eventSource = connectSSE(
        url,
        (message) => {
          setData(message);
          setIsConnected(true);
          setError(null);

          // 如果任务完成，关闭连接
          if (message.status === 'completed' || message.status === 'failed') {
            setIsConnected(false);
            eventSource.close();
          }
        },
        () => {
          setError('SSE连接失败');
          setIsConnected(false);
        }
      );

      eventSourceRef.current = eventSource;

      // 清理函数
      return () => {
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      };
    } catch (err) {
      setError('创建SSE连接失败');
      console.error('SSE init error:', err);
    }
  }, [url]);

  return {
    data,
    progress: data?.progress || 0,
    status: data?.status || 'pending',
    message: data?.message,
    result: data?.result,
    error: data?.error || error,
    isConnected,
  };
}

/**
 * 批量搜索Hook（含SSE进度）
 *
 * @returns { search, isLoading, progress, status, ... }
 */
export function useBatchSearch() {
  const [isLoading, setIsLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { progress, status, result } = useSSE(
    taskId ? `/api/stream/batch-search/${taskId}` : ''
  );

  /**
   * 开始批量搜索
   */
  const search = useCallback(async (batchText: string, sources?: string[], concurrency?: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const { apiEndpoints } = await import('../services/api');
      const response = await api.post(apiEndpoints.batchSearch, {
        text: batchText,
        sources: sources || null,
        concurrency: concurrency || 5,
      });

      setTaskId(response.data.task_id);
    } catch (err: any) {
      setError(err.message || '批量搜索失败');
      setIsLoading(false);
    }
  }, []);

  return {
    search,
    isLoading: isLoading || status === 'pending',
    progress,
    status,
    result,
    error,
  };
}

/**
 * 下载Hook（含SSE进度）
 *
 * @returns { download, isLoading, progress, status, ... }
 */
export function useDownload() {
  const [isLoading, setIsLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { progress, status, result } = useSSE(
    taskId ? `/api/stream/download/${taskId}` : ''
  );

  /**
   * 开始下载
   */
  const download = useCallback(async (songs: any[], downloadDir?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const { apiEndpoints } = await import('../services/api');
      const response = await api.post(apiEndpoints.downloadStart, {
        songs,
        download_dir: downloadDir,
      });

      setTaskId(response.data.task_id);
    } catch (err: any) {
      setError(err.message || '下载失败');
      setIsLoading(false);
    }
  }, []);

  return {
    download,
    isLoading: isLoading || status === 'pending',
    progress,
    status,
    result,
    error,
  };
}
