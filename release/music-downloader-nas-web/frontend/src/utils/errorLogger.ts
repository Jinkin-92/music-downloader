/**
 * 错误日志工具
 *
 * 保存前端错误日志到localStorage和服务器
 */
import { api } from '../services/api';

/**
 * 错误日志条目
 */
export interface ErrorLog {
  timestamp: string;
  context: string;
  error: {
    message: string;
    stack?: string;
    response?: any;
  };
  userAgent: string;
  url: string;
}

/**
 * 保存错误日志
 *
 * @param error - 错误对象
 * @param context - 错误上下文描述
 */
export const saveErrorLog = (error: any, context: string) => {
  const logEntry: ErrorLog = {
    timestamp: new Date().toISOString(),
    context,
    error: {
      message: error.message || String(error),
      stack: error.stack,
      response: error.response?.data,
    },
    userAgent: navigator.userAgent,
    url: window.location.href,
  };

  // 1. 保存到localStorage（保留最近100条）
  try {
    const logs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
    logs.push(logEntry);
    localStorage.setItem('errorLogs', JSON.stringify(logs.slice(-100)));
    console.log('[ErrorLogger] 已保存到localStorage:', logEntry);
  } catch (e) {
    console.error('[ErrorLogger] 保存到localStorage失败:', e);
  }

  // 2. 发送到后端保存
  api.post('/logs/error', logEntry).catch((err) => {
    console.error('[ErrorLogger] 发送到后端失败:', err);
  });
};

/**
 * 从localStorage获取错误日志
 *
 * @returns 错误日志列表
 */
export const getErrorLogs = (): ErrorLog[] => {
  try {
    const logs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
    return logs;
  } catch (e) {
    console.error('[ErrorLogger] 读取错误日志失败:', e);
    return [];
  }
};

/**
 * 清除错误日志
 */
export const clearErrorLogs = () => {
  try {
    localStorage.removeItem('errorLogs');
    console.log('[ErrorLogger] 已清除错误日志');
  } catch (e) {
    console.error('[ErrorLogger] 清除错误日志失败:', e);
  }
};

/**
 * API拦截器错误处理
 *
 * 在axios响应拦截器中使用此函数来处理错误
 */
export const handleApiError = (error: any) => {
  saveErrorLog(error, 'API请求失败');

  // 提取友好的错误消息
  let message = '操作失败，请稍后重试';

  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;

    if (status === 400) {
      message = data.detail || '请求参数错误';
    } else if (status === 404) {
      message = '请求的资源不存在';
    } else if (status === 500) {
      message = '服务器错误，请稍后重试';
    } else if (data.detail) {
      message = data.detail;
    }
  } else if (error.message) {
    message = error.message;
  }

  return Promise.reject({
    message,
    originalError: error,
  });
};
