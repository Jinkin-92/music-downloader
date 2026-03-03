/**
 * 空状态组件
 *
 * 当没有搜索结果时的占位提示
 */
import { Empty, Button, Typography, Space } from 'antd';
import { PlusOutlined, SearchOutlined, CloudDownloadOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface EmptyStateProps {
  type?: 'search' | 'download' | 'default';
  actionText?: string;
  onAction?: () => void;
}

function EmptyState({
  type = 'default',
  actionText,
  onAction,
}: EmptyStateProps) {
  const getConfig = () => {
    switch (type) {
      case 'search':
        return {
          description: '输入歌曲名或歌手开始搜索',
          icon: <SearchOutlined style={{ fontSize: 64 }} />,
          actionText: actionText || '开始搜索',
        };
      case 'download':
        return {
          description: '下载的歌曲将显示在这里',
          icon: <CloudDownloadOutlined style={{ fontSize: 64 }} />,
          actionText: actionText || '查看下载',
        };
      default:
        return {
          description: '暂无数据',
          icon: undefined,
          actionText: actionText || '刷新',
        };
    }
  };

  const config = getConfig();

  return (
    <Empty
      image={config.icon}
      description={
        <Space direction="vertical" size="small" align="center">
          <Text type="secondary">{config.description}</Text>
          {onAction && actionText && (
            <Button type="primary" icon={<PlusOutlined />} onClick={onAction}>
              {actionText}
            </Button>
          )}
        </Space>
      }
    />
  );
}

export default EmptyState;
