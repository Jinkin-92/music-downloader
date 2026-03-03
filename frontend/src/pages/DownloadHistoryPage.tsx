/**
 * 下载历史页面
 *
 * 显示已下载的文件列表，支持文件管理和播放
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
  Empty,
  Tooltip,
  Modal,
} from 'antd';
import {
  FolderOpenOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
  ReloadOutlined,
  FileOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { downloadApi } from '../services/api';
import { formatBytes, formatDuration } from '../styles/theme';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface DownloadedFile {
  name: string;
  size: number;
  modified: number;
}

function DownloadHistoryPage() {
  const [selectedFile, setSelectedFile] = useState<DownloadedFile | null>(null);
  const [previewVisible, setPreviewVisible] = useState(false);
  const queryClient = useQueryClient();

  // 获取文件列表
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['downloadedFiles'],
    queryFn: async () => {
      const response = await downloadApi.getFiles();
      return response.data;
    },
    staleTime: 30 * 1000, // 30秒内不重新请求
  });

  // 刷新文件列表
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['downloadedFiles'] });
    refetch();
    message.success('已刷新');
  };

  // 预览文件
  const handlePreview = (file: DownloadedFile) => {
    setSelectedFile(file);
    setPreviewVisible(true);
  };

  // 表格列定义
  const columns = [
    {
      title: '文件名称',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      ellipsis: true,
      render: (name: string) => (
        <Space>
          <FileOutlined />
          <Text strong style={{ fontFamily: 'monospace' }}>{name}</Text>
        </Space>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: (size: number) => formatBytes(size),
    },
    {
      title: '修改时间',
      dataIndex: 'modified',
      key: 'modified',
      width: 180,
      render: (timestamp: number) => dayjs(timestamp * 1000).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '格式',
      key: 'format',
      width: 80,
      render: (_: any, record: DownloadedFile) => {
        const ext = record.name.split('.').pop()?.toLowerCase();
        const formatTags: Record<string, { color: string; label: string }> = {
          mp3: { color: 'blue', label: 'MP3' },
          flac: { color: 'green', label: 'FLAC' },
          ogg: { color: 'orange', label: 'OGG' },
          wav: { color: 'purple', label: 'WAV' },
          m4a: { color: 'cyan', label: 'M4A' },
        };
        const tag = formatTags[ext || ''];
        return tag ? (
          <Tag color={tag.color}>{tag.label}</Tag>
        ) : (
          <Tag>{ext?.toUpperCase()}</Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_: any, record: DownloadedFile) => (
        <Space size="small">
          <Tooltip title="预览">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              onClick={() => handlePreview(record)}
            />
          </Tooltip>
          <Tooltip title="打开文件夹">
            <Button
              type="text"
              icon={<FolderOpenOutlined />}
              onClick={() => {
                // 在浏览器中无法直接打开文件夹，显示提示
                message.info(`文件位置: ${record.name}`);
              }}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: '确认删除',
                  content: `确定要删除文件 "${record.name}" 吗？`,
                  okText: '删除',
                  okType: 'danger',
                  cancelText: '取消',
                  onOk: () => {
                    message.success('删除功能开发中');
                  },
                });
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} className="page-title" style={{ margin: 0 }}>
          下载历史
        </Title>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleRefresh}
          loading={isLoading}
        >
          刷新
        </Button>
      </div>

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
            dataSource={data?.files || []}
            loading={isLoading}
            rowKey="name"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个文件`,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
            scroll={{ x: 1000 }}
            locale={{
              emptyText: (
                <Empty
                  description="暂无下载文件"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                >
                  <Text type="secondary">
                    下载的歌曲会自动显示在这里
                  </Text>
                </Empty>
              ),
            }}
          />
        )}
      </Card>

      {/* 文件预览弹窗 */}
      <Modal
        title="文件信息"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>,
          <Button key="open" type="primary" icon={<FolderOpenOutlined />}>
            打开文件
          </Button>,
        ]}
      >
        {selectedFile && (
          <div>
            <p><strong>文件名：</strong>{selectedFile.name}</p>
            <p><strong>大小：</strong>{formatBytes(selectedFile.size)}</p>
            <p><strong>修改时间：</strong>{dayjs(selectedFile.modified * 1000).format('YYYY-MM-DD HH:mm:ss')}</p>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default DownloadHistoryPage;
