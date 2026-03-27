/**
 * 批量结果表格组件
 *
 * 显示批量匹配结果，支持相似度颜色编码和候选切换
 * v2: 去掉相似度列，在操作列显示相似度
 */
import { Table, Button, Tag, Space, Typography, Dropdown, Tooltip } from 'antd';
import { DownloadOutlined, SwapOutlined, DownOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { MenuProps } from 'antd';
import { BatchMatchInfo } from '../../types';

const { Text } = Typography;

// 音乐源标签映射
const SOURCE_LABELS: Record<string, string> = {
  'QQMusicClient': 'QQ音乐',
  'NeteaseMusicClient': '网易云',
  'KugouMusicClient': '酷狗',
  'KuwoMusicClient': '酷我',
  'MiguMusicClient': '咪咕',
};

// 音乐源颜色映射
const SOURCE_COLORS: Record<string, string> = {
  'QQMusicClient': 'green',
  'NeteaseMusicClient': 'red',
  'KugouMusicClient': 'blue',
  'KuwoMusicClient': 'orange',
  'MiguMusicClient': 'purple',
};

interface BatchResultsTableProps {
  data?: BatchMatchInfo[];
  /** 下载单首歌曲回调 */
  onDownload?: (record: BatchMatchInfo) => void;
  /** 切换候选回调 */
  onSwitchCandidate?: (index: number, source: string, candidate: any, candidateIndex: number) => void;
  /** 是否显示行选择 */
  rowSelection?: {
    selectedRowKeys: string[];
    onChange: (keys: string[]) => void;
  };
}

function BatchResultsTable({
  data = [],
  onDownload,
  onSwitchCandidate,
  rowSelection,
}: BatchResultsTableProps) {

  /**
   * 获取相似度颜色和文字
   */
  const getSimilarityDisplay = (similarity: number) => {
    const percent = Math.round(similarity * 100);
    let color = 'error';
    if (percent >= 80) color = 'success';
    else if (percent >= 60) color = 'warning';
    return { color, text: `${percent}%` };
  };

  /**
   * 构建候选切换下拉菜单
   */
  const buildCandidateMenu = (record: BatchMatchInfo, index: number): MenuProps => {
    if (!record.all_candidates) {
      return { items: [] };
    }

    const items: MenuProps['items'] = [];

    Object.entries(record.all_candidates).forEach(([source, candidates]) => {
      if (Array.isArray(candidates) && candidates.length > 0) {
        // 添加源分组标题
        items.push({
          type: 'group',
          label: (
            <Text strong style={{ color: '#1890ff' }}>
              {SOURCE_LABELS[source] || source}
            </Text>
          ),
        });

        // 添加该源下的候选
        candidates.forEach((candidate: any, idx: number) => {
          const simDisplay = getSimilarityDisplay(candidate.similarity || 0);
          items.push({
            key: `${source}-${idx}`,
            label: (
              <Space size="small">
                <Text>{candidate.song_name}</Text>
                <Tag color={simDisplay.color} style={{ fontSize: 11 }}>
                  {simDisplay.text}
                </Tag>
              </Space>
            ),
            onClick: () => onSwitchCandidate?.(index, source, candidate, idx),
          });
        });
      }
    });

    return { items };
  };

  const columns: ColumnsType<BatchMatchInfo> = [
    {
      title: '查询',
      key: 'query',
      width: 180,
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
      width: 350,
      render: (_, record) => {
        return (
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
        );
      },
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      render: (source: string) => {
        if (source === '-') {
          return <Text type="secondary">未匹配</Text>;
        }
        return (
          <Tag color={SOURCE_COLORS[source] || 'blue'}>
            {SOURCE_LABELS[source] || source}
          </Tag>
        );
      },
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
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_, record, index) => {
        const simDisplay = getSimilarityDisplay(record.similarity);
        const hasCandidates = record.has_candidates && record.all_candidates;
        const candidateCount = hasCandidates
          ? Object.values(record.all_candidates || {}).flat().length
          : 0;

        return (
          <Space size="small">
            {/* 相似度显示 */}
            {record.source !== '-' && (
              <Tooltip
                title={
                  record.name_similarity !== undefined ? (
                    <div style={{ fontSize: 12 }}>
                      <div>歌名: {Math.round((record.name_similarity || 0) * 100)}%</div>
                      <div>歌手: {Math.round((record.singer_similarity || 0) * 100)}%</div>
                      <div>专辑: {Math.round((record.album_similarity || 0) * 100)}%</div>
                    </div>
                  ) : (
                    '匹配相似度'
                  )
                }
              >
                <Tag color={simDisplay.color} style={{ cursor: 'help' }}>
                  {simDisplay.text}
                </Tag>
              </Tooltip>
            )}

            {/* 切换匹配源按钮 */}
            {hasCandidates && candidateCount > 1 && (
              <Dropdown
                menu={buildCandidateMenu(record, index)}
                trigger={['click']}
              >
                <Button size="small" icon={<SwapOutlined />}>
                  切换 <DownOutlined style={{ fontSize: 10 }} />
                </Button>
              </Dropdown>
            )}

            {/* 下载按钮 */}
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              size="small"
              disabled={record.source === '-'}
              onClick={() => onDownload?.(record)}
            >
              下载
            </Button>
          </Space>
        );
      },
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      rowKey={(record, index) => `${record.query_name}-${index ?? 0}`}
      pagination={false}
      scroll={{ y: 500, x: 1000 }}
      size="middle"
      rowSelection={rowSelection ? {
        type: 'checkbox',
        selectedRowKeys: rowSelection.selectedRowKeys,
        onChange: (keys) => rowSelection.onChange(keys as string[]),
        columnWidth: 50,
      } : undefined}
    />
  );
}

export default BatchResultsTable;
