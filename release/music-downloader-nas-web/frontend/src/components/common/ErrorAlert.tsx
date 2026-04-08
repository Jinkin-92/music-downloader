/**
 * 智能错误提示组件
 *
 * 根据错误类型显示不同的提示和恢复建议
 */
import { Alert, Button, Space, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface ErrorAlertProps {
  error: string;
  onRetry?: () => void;
  type?: '403' | 'network' | 'parse' | 'default';
}

function ErrorAlert({ error, onRetry, type = 'default' }: ErrorAlertProps) {
  const getErrorConfig = (errorType: string, errorMsg: string) => {
    // 403版权错误
    if (errorType === '403' || errorMsg.includes('403') || errorMsg.includes('版权')) {
      return {
        title: '版权保护',
        message: '该歌曲受版权保护，正在尝试切换其他音乐源...',
        action: '自动重试中',
        icon: '⚠️',
        showRetry: false,
      };
    }

    // 网络错误
    if (errorType === 'network' || errorMsg.includes('网络') || errorMsg.includes('连接')) {
      return {
        title: '网络错误',
        message: '网络连接失败，请检查网络设置后重试',
        action: '重试',
        icon: '📡',
        showRetry: true,
      };
    }

    // 解析错误
    if (errorType === 'parse' || errorMsg.includes('格式') || errorMsg.includes('解析')) {
      return {
        title: '格式错误',
        message: '批量文本格式不正确，请使用 "歌名 - 歌手" 格式，每行一首歌',
        action: '查看示例',
        icon: '📝',
        showRetry: false,
      };
    }

    // 默认错误
    return {
      title: '下载失败',
      message: errorMsg,
      action: '重试',
      icon: '❌',
      showRetry: true,
    };
  };

  const config = getErrorConfig(type, error);

  return (
    <Alert
      type="error"
      message={config.title}
      description={
        <Space direction="vertical" size="small">
          <Text>{config.message}</Text>
          {onRetry && config.showRetry && (
            <Button
              size="small"
              icon={config.action === '自动重试中' ? <ReloadOutlined spin /> : undefined}
              onClick={onRetry}
            >
              {config.action}
            </Button>
          )}
        </Space>
      }
      showIcon
      icon={config.icon}
      closable
    />
  );
}

export default ErrorAlert;
