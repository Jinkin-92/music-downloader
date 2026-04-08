/**
 * 错误处理和建议组件
 */
import React from 'react';
import { Alert, Typography, Button } from 'antd';
import {
  ExclamationCircleOutlined,
  ReloadOutlined,
  LinkOutlined,
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;

export interface ErrorSuggestion {
  title: string;
  description: string;
  solutions: string[];
  actionLabel?: string;
  onAction?: () => void;
}

interface ErrorAlertProps {
  error: ErrorSuggestion;
  type?: 'warning' | 'error';
  closable?: boolean;
  onClose?: () => void;
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({
  error,
  type = 'warning',
  closable = true,
  onClose
}) => {
  const alertType = type === 'error' ? 'error' : 'warning';

  return (
    <Alert
      message={error.title}
      description={
        <div>
          <Paragraph style={{ marginBottom: 12 }}>
            {error.description}
          </Paragraph>
          <div style={{ marginTop: 12 }}>
            <Text strong>可能的解决方案：</Text>
            <ul style={{ marginTop: 8, paddingLeft: 20 }}>
              {error.solutions.map((solution, index) => (
                <li key={index} style={{ marginBottom: 4 }}>
                  {solution}
                </li>
              ))}
            </ul>
          </div>
          {error.actionLabel && error.onAction && (
            <Button
              type="primary"
              size="small"
              icon={type === 'error' ? <ReloadOutlined /> : <LinkOutlined />}
              onClick={error.onAction}
              style={{ marginTop: 12 }}
            >
              {error.actionLabel}
            </Button>
          )}
        </div>
      }
      type={alertType}
      icon={<ExclamationCircleOutlined />}
      closable={closable}
      onClose={onClose}
      showIcon
      style={{ marginBottom: 16 }}
    />
  );
};

// 预定义的错误建议
export const ERROR_SUGGESTIONS = {
  NETWORK_ERROR: {
    title: '网络连接失败',
    description: '无法连接到服务器或音乐源API',
    solutions: [
      '检查网络连接是否正常',
      '确认防火墙是否阻止了请求',
      '尝试切换到其他音乐源',
      '稍后重试'
    ],
    actionLabel: '重试',
  },
  PLAYLIST_PRIVATE: {
    title: '歌单无法访问',
    description: '该歌单可能是私密歌单或已被删除',
    solutions: [
      '确认歌单设置为公开状态',
      '尝试复制歌单链接后重新解析',
      '联系歌单分享者确认权限'
    ],
  },
  NO_MATCHES: {
    title: '未找到匹配歌曲',
    description: '在所有选中的音乐源中都没有找到匹配的歌曲',
    solutions: [
      '检查歌曲名称和歌手是否正确',
      '尝试手动编辑歌曲信息',
      '增加更多音乐源进行搜索',
      '降低相似度阈值设置'
    ],
    actionLabel: '编辑歌曲',
  },
  DOWNLOAD_FAILED: {
    title: '下载失败',
    description: '部分歌曲因版权保护或其他原因无法下载',
    solutions: [
      '尝试切换到其他音乐源',
      '该歌曲可能在您的地区不可用',
      '尝试下载其他歌曲'
    ],
  },
};

export default ErrorAlert;
