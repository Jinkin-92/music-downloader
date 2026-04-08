/**
 * 下载历史页面 V2
 *
 * 新功能：
 * - 统计信息显示（总数、有效、缺失）
 * - 刷新按钮：重新读取历史记录
 * - 清理无效记录按钮：删除文件缺失的记录
 * - 打开文件夹功能（通过后端API）
 * - 重新下载功能
 */
import { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  message,
  Tag,
  Tooltip,
  Modal,
  Alert,
  Input,
  Select,
  Statistic,
  Row,
  Col,
  Empty,
} from 'antd';
import {
  FolderOpenOutlined,
  ReloadOutlined,
  FileOutlined,
  RedoOutlined,
  ClearOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import EmptyState from '../components/common/EmptyState';

const { Title, Text } = Typography;
const { Search } = Input;

// 下载历史记录类型
interface DownloadRecord {
  id: number;
  song_name: string;
  singers: string;
  file_path: string;
  file_size: number;
  source: string;
  similarity: number;
  download_time: string;
  file_exists: boolean;
}

// 统计信息类型
interface HistoryStats {
  total: number;
  valid: number;
  missing: number;
}

// 音乐源标签
const SOURCE_LABELS: Record<string, string> = {
  'QQMusicClient': 'QQ音乐',
  'NeteaseMusicClient': '网易云',
  'KugouMusicClient': '酷狗',
  'KuwoMusicClient': '酷我',
  'MiguMusicClient': '咪咕',
  'Pjmp3Client': 'pjmp3',
};

// 音乐源颜色
const SOURCE_COLORS: Record<string, string> = {
  'QQMusicClient': 'green',
  'NeteaseMusicClient': 'red',
  'KugouMusicClient': 'blue',
  'KuwoMusicClient': 'orange',
  'MiguMusicClient': 'purple',
  'Pjmp3Client': 'cyan',
};

function DownloadHistoryPage() {
  const [searchText, setSearchText] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'valid' | 'missing'>('all');
  const [selectedRecord, setSelectedRecord] = useState<DownloadRecord | null>(null);
  const [redownloadVisible, setRedownloadVisible] = useState(false);
  const queryClient = useQueryClient();

  // 获取历史记录
  const {
    data: historyData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['downloadHistory'],
    queryFn: async () => {
      const response = await fetch('/api/history');
      if (!response.ok) throw new Error('获取历史记录失败');
      return response.json();
    },
    staleTime: 30 * 1000,
  });

  // 获取统计信息
  const { data: stats } = useQuery<HistoryStats>({
    queryKey: ['historyStats'],
    queryFn: async () => {
      const response = await fetch('/api/history/stats');
      if (!response.ok) throw new Error('获取统计信息失败');
      return response.json();
    },
  });

  // 清理缺失记录
  const cleanMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/history/clean', { method: 'DELETE' });
      if (!response.ok) throw new Error('清理失败');
      return response.json();
    },
    onSuccess: (data) => {
      message.success(`已清理 ${data.deleted_count} 条无效记录`);
      queryClient.invalidateQueries({ queryKey: ['downloadHistory'] });
      queryClient.invalidateQueries({ queryKey: ['historyStats'] });
    },
    onError: () => {
      message.error('清理失败');
    },
  });

  // 打开文件夹
  const handleOpenFolder = async (filePath: string) => {
    try {
      const response = await fetch('/api/history/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath }),
      });
      const data = await response.json();
      if (data.success) {
        message.success('已打开文件夹');
      } else {
        message.warning(data.message || '无法打开文件夹');
      }
    } catch {
      message.error('打开文件夹失败');
    }
  };

  // 刷新
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['downloadHistory'] });
    queryClient.invalidateQueries({ queryKey: ['historyStats'] });
    message.success('已刷新');
  };

  // 清理确认
  const handleCleanConfirm = () => {
    Modal.confirm({
      title: '清理无效记录',
      content: '确定要删除所有文件缺失的历史记录吗？此操作不可恢复。',
      okText: '确认清理',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => cleanMutation.mutate(),
    });
  };

  // 格式化文件大小
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '--';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化相似度
  const formatSimilarity = (sim: number) => {
    const percent = Math.round(sim * 100);
    let color = 'default';
    if (percent >= 80) color = 'success';
    else if (percent >= 60) color = 'warning';
    else if (percent > 0) color = 'error';
    return { percent, color };
  };

  // 过滤数据
  const filteredRecords = (historyData?.records || []).filter((record: DownloadRecord) => {
    // 状态过滤
    if (filterStatus === 'valid' && !record.file_exists) return false;
    if (filterStatus === 'missing' && record.file_exists) return false;
    // 搜索过滤
    if (searchText) {
      const search = searchText.toLowerCase();
      return (
        record.song_name.toLowerCase().includes(search) ||
        record.singers.toLowerCase().includes(search)
      );
    }
    return true;
  });

  // 表格列定义
  const columns: import('antd/es/table').ColumnsType<DownloadRecord> = [
    {
      title: '文件名称',
      key: 'name',
      width: 280,
      render: (_: any, record: DownloadRecord) => (
        <div style={{ opacity: record.file_exists ? 1 : 0.5 }}>
          <Space>
            {record.file_exists ? (
              <FileOutlined style={{ color: '#1890ff' }} />
            ) : (
              <WarningOutlined style={{ color: '#ff4d4f' }} />
            )}
            <div>
              <Text strong={record.file_exists}>
                {record.song_name} - {record.singers}
              </Text>
              {!record.file_exists && (
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    原路径: {record.file_path}
                  </Text>
                </div>
              )}
            </div>
          </Space>
        </div>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'size',
      width: 100,
      render: (size: number, record: DownloadRecord) => (
        <Text style={{ opacity: record.file_exists ? 1 : 0.5 }}>
          {formatBytes(size)}
        </Text>
      ),
    },
    {
      title: '下载时间',
      dataIndex: 'download_time',
      key: 'download_time',
      width: 160,
      render: (time: string, record: DownloadRecord) => (
        <Text style={{ opacity: record.file_exists ? 1 : 0.5 }}>
          {time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'}
        </Text>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      render: (source: string, record: DownloadRecord) => {
        const sim = formatSimilarity(record.similarity);
        return (
          <Space size={4} style={{ opacity: record.file_exists ? 1 : 0.5 }}>
            <Tag color={SOURCE_COLORS[source] || 'blue'}>
              {SOURCE_LABELS[source] || source || '-'}
            </Tag>
            <Tag color={sim.color}>{sim.percent}%</Tag>
          </Space>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'file_exists',
      key: 'status',
      width: 80,
      render: (exists: boolean) => (
        exists ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>正常</Tag>
        ) : (
          <Tag color="error" icon={<WarningOutlined />}>缺失</Tag>
        )
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: DownloadRecord) => (
        <Space size="small">
          <Tooltip title="重新下载">
            <Button
              type="text"
              icon={<RedoOutlined />}
              onClick={() => {
                setSelectedRecord(record);
                setRedownloadVisible(true);
              }}
            />
          </Tooltip>
          {record.file_exists && (
            <Tooltip title="打开文件夹">
              <Button
                type="text"
                icon={<FolderOpenOutlined />}
                onClick={() => handleOpenFolder(record.file_path)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="page">
      {/* 标题栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} className="page-title" style={{ margin: 0 }}>
          下载历史
        </Title>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={isLoading}
          >
            刷新
          </Button>
          <Button
            icon={<ClearOutlined />}
            danger
            onClick={handleCleanConfirm}
            loading={cleanMutation.isPending}
          >
            清理无效记录
          </Button>
        </Space>
      </div>

      {/* 统计信息 */}
      {stats && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={24}>
            <Col span={8}>
              <Statistic
                title="总计"
                value={stats.total}
                suffix="首歌曲"
                prefix={<FileOutlined />}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="有效"
                value={stats.valid}
                suffix="首"
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="缺失"
                value={stats.missing}
                suffix="首"
                valueStyle={{ color: stats.missing > 0 ? '#ff4d4f' : undefined }}
                prefix={<WarningOutlined />}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 筛选和搜索 */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle">
          <Text strong>筛选:</Text>
          <Select
            value={filterStatus}
            onChange={setFilterStatus}
            style={{ width: 120 }}
            options={[
              { value: 'all', label: '全部' },
              { value: 'valid', label: '有效文件' },
              { value: 'missing', label: '缺失文件' },
            ]}
          />
          <Search
            placeholder="搜索歌曲名或歌手..."
            allowClear
            style={{ width: 250 }}
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </Space>
      </Card>

      {/* 数据表格 */}
      <Card>
        {isError ? (
          <Empty
            description="加载失败"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={handleRefresh}>
              重试
            </Button>
          </Empty>
        ) : (
          <Table
            columns={columns}
            dataSource={filteredRecords}
            loading={isLoading}
            rowKey="id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条记录`,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
            scroll={{ x: 1100 }}
            rowClassName={(record) => !record.file_exists ? 'missing-record' : ''}
            locale={{
              emptyText: (
                <EmptyState
                  type="history"
                  onAction={() => window.location.href = '/'}
                />
              ),
            }}
          />
        )}
      </Card>

      {/* 重新下载弹窗 */}
      <Modal
        title="重新下载"
        open={redownloadVisible}
        onCancel={() => setRedownloadVisible(false)}
        footer={null}
        width={600}
      >
        {selectedRecord && (
          <div>
            <Alert
              message="重新下载将删除原文件并更新历史记录"
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <p><strong>歌曲：</strong>{selectedRecord.song_name} - {selectedRecord.singers}</p>
            <p><strong>原文件：</strong>{selectedRecord.file_path}</p>
            <p><strong>原大小：</strong>{formatBytes(selectedRecord.file_size)}</p>

            <div style={{ marginTop: 24, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setRedownloadVisible(false)}>取消</Button>
                <Button
                  type="primary"
                  icon={<RedoOutlined />}
                  onClick={() => {
                    message.success('重新下载功能开发中...');
                    setRedownloadVisible(false);
                  }}
                >
                  开始下载
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Modal>

      <style>{`
        .missing-record {
          background-color: #fff1f0;
        }
        .missing-record:hover td {
          background-color: #ffe7e6 !important;
        }
      `}</style>
    </div>
  );
}

export default DownloadHistoryPage;
