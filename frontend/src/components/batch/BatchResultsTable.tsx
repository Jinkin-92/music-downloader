/**
 * 批量结果表格组件
 *
 * 显示批量匹配结果，支持相似度颜色编码和候选切换
 */
import { Table, Button, Tag, Space, Typography } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { BatchMatchInfo } from '../../types';
import { getSimilarityTagColor } from '../../styles/theme';
import { useUIStore } from '../../stores/useUIStore';

const { Text } = Typography;

interface BatchResultsTableProps {
  data?: BatchMatchInfo[];
}

function BatchResultsTable({ data = [] }: BatchResultsTableProps) {
  const { matchMode } = useUIStore();
  const threshold = matchMode === 'strict' ? 0.7 : matchMode === 'standard' ? 0.6 : 0.5;

  /**
   * 过滤低于阈值的结果
   */
  const filteredData = data.filter((item) => item.similarity >= threshold);

  /**
   * 切换候选（下拉菜单）
   */
  const _handleSwitchCandidate = (record: BatchMatchInfo) => {
    // TODO: 实现候选切换逻辑
    console.log('Switch candidate:', record);
  };
  // 避免 eslint 警告
  void _handleSwitchCandidate;

  const columns: ColumnsType<BatchMatchInfo> = [
    {
      title: '查询',
      key: 'query',
      width: 150,
      render: (_, record) => (
        <div>
          <div>
            <Text strong>{record.query_name}</Text>
          </div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.query_singer}
          </Text>
        </div>
      ),
    },
    {
      title: '匹配结果',
      key: 'result',
      width: 400,
      render: (_, record) => (
        <div>
          <div>
            <Text strong>{record.song_name}</Text>
          </div>
          <Space size={4}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.singers}
            </Text>
            {record.album && (
              <Tag style={{ fontSize: 11 }}>{record.album}</Tag>
            )}
          </Space>
        </div>
      ),
    },
    {
      title: '大小/时长',
      key: 'size',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size={0} style={{ fontSize: 12 }}>
          <Text>{record.size || '-'}</Text>
          <Text type="secondary">{record.duration || '-'}</Text>
        </Space>
      ),
    },
    {
      title: '相似度',
      key: 'similarity',
      width: 120,
      render: (_, record) => (
        <Tag color={getSimilarityTagColor(record.similarity)}>
          {(record.similarity * 100).toFixed(0)}%
        </Tag>
      ),
    },
    {
      title: '来源',
      key: 'source',
      width: 100,
      render: (_, record) => {
        const sourceLabels: Record<string, string> = {
          'QQMusicClient': 'QQ音乐',
          'NeteaseMusicClient': '网易云',
          'KugouMusicClient': '酷狗',
          'KuwoMusicClient': '酷我',
        };
        return <Tag color="blue">{sourceLabels[record.source] || record.source}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: () => (
        <Space>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            size="small"
          >
            下载
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={filteredData}
      rowKey={(record) => `${record.query_name}-${record.source}`}
      pagination={false}
      scroll={{ y: 500 }}
      size="middle"
    />
  );
}

export default BatchResultsTable;
