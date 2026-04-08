/**
 * 增强进度条组件
 *
 * 显示详细的进度信息：
 * - 进度百分比
 * - 速度（歌曲/秒）
 * - 剩余时间
 * - 当前操作
 */
import React from 'react';
import { Progress, Space, Typography, Row, Col } from 'antd';
import { ClockCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';

const { Text } = Typography;

export interface EnhancedProgressProps {
  percent: number;
  current?: string;
  completed: number;
  total: number;
  speed?: number; // 歌曲/秒
  remainingTime?: number; // 秒
  status?: 'active' | 'success' | 'exception';
  showDetails?: boolean;
}

const EnhancedProgress: React.FC<EnhancedProgressProps> = ({
  percent,
  current,
  completed,
  total,
  speed,
  remainingTime,
  status = 'active',
  showDetails = true
}) => {
  // 格式化剩余时间
  const formatRemainingTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}小时${mins}分`;
  };

  // 格式化速度
  const formatSpeed = (songsPerSecond: number): string => {
    if (songsPerSecond >= 1) return `${songsPerSecond.toFixed(1)} 首/秒`;
    return `${(1 / songsPerSecond).toFixed(1)} 秒/首`;
  };

  return (
    <div style={{ width: '100%' }}>
      <Progress
        percent={percent}
        status={status}
        strokeWidth={12}
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#87d068',
          from: '#108ee9',
          to: '#87d068',
        }}
        style={{ marginBottom: 16 }}
      />

      {showDetails && (
        <Row gutter={[16, 16]}>
          <Col span={status === 'active' ? 8 : 12}>
            <Space size={4}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                进度
              </Text>
              <Text strong style={{ fontSize: 14 }}>
                {completed} / {total}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                ({percent.toFixed(0)}%)
              </Text>
            </Space>
          </Col>

          {status === 'active' && speed && (
            <Col span={8}>
              <Space size={4}>
                <ThunderboltOutlined style={{ fontSize: 12, color: '#faad14' }} />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  速度
                </Text>
                <Text strong style={{ fontSize: 14, color: '#faad14' }}>
                  {formatSpeed(speed)}
                </Text>
              </Space>
            </Col>
          )}

          {status === 'active' && remainingTime !== undefined && (
            <Col span={8}>
              <Space size={4}>
                <ClockCircleOutlined style={{ fontSize: 12, color: '#1890ff' }} />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  剩余
                </Text>
                <Text strong style={{ fontSize: 14, color: '#1890ff' }}>
                  {formatRemainingTime(remainingTime)}
                </Text>
              </Space>
            </Col>
          )}

          {current && (
            <Col span={24}>
              <Text
                ellipsis={{ tooltip: current }}
                style={{
                  fontSize: 12,
                  color: '#666',
                  display: 'block',
                  marginTop: 4
                }}
              >
                正在处理: {current}
              </Text>
            </Col>
          )}
        </Row>
      )}
    </div>
  );
};

export default EnhancedProgress;
