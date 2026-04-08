/**
 * SSE连接状态指示器
 *
 * 显示实时连接状态：连接中、已连接、已断开、错误
 */
import React from 'react';
import { Badge, Space, Typography } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';

const { Text } = Typography;

export type SSEStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface SSEStatusIndicatorProps {
  status: SSEStatus;
  label?: string;
  showText?: boolean;
  className?: string;
}

const SSE_STATUS_CONFIG = {
  connecting: {
    color: 'processing',
    icon: <LoadingOutlined spin />,
    text: '连接中...',
    textColor: '#1890ff'
  },
  connected: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    text: '实时连接',
    textColor: '#52c41a'
  },
  disconnected: {
    color: 'default',
    icon: <CloseCircleOutlined />,
    text: '未连接',
    textColor: '#8c8c8c'
  },
  error: {
    color: 'error',
    icon: <ExclamationCircleOutlined />,
    text: '连接错误',
    textColor: '#ff4d4f'
  }
};

const SSEStatusIndicator: React.FC<SSEStatusIndicatorProps> = ({
  status,
  label,
  showText = true,
  className
}) => {
  const config = SSE_STATUS_CONFIG[status];

  return (
    <Space size={8} className={className}>
      <Badge
        status={config.color as any}
      />
      {showText && (
        <Text style={{ fontSize: 12, color: config.textColor }}>
          {label || config.text}
        </Text>
      )}
    </Space>
  );
};

export default SSEStatusIndicator;
