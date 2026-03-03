/**
 * 加载动画组件
 *
 * Apple风格的加载指示器
 */
import { Spin, Space, Typography } from 'antd';

const { Text } = Typography;

interface LoadingSpinnerProps {
  tip?: string;
  size?: 'small' | 'large' | 'default';
}

function LoadingSpinner({ tip = '加载中...', size = 'large' }: LoadingSpinnerProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '200px',
    }}>
      <Space direction="vertical" size="middle" align="center">
        <Spin size={size} tip="" />
        {tip && (
          <Text type="secondary" style={{ fontSize: 14 }}>
            {tip}
          </Text>
        )}
      </Space>
    </div>
  );
}

export default LoadingSpinner;
