import { useCallback, useMemo, useState } from 'react';
import {
  Alert,
  App,
  Button,
  Card,
  Input,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  DownloadOutlined,
  SearchOutlined,
  CheckSquareOutlined,
} from '@ant-design/icons';
import { downloadApi, searchApi } from '../services/api';
import { useUIStore } from '../stores/useUIStore';
import type { Song } from '../types';
import SourceSelector from '../components/common/SourceSelector';

const { Title, Text } = Typography;

const SOURCE_LABELS: Record<string, string> = {
  QQMusicClient: 'QQ音乐',
  NeteaseMusicClient: '网易云',
  KugouMusicClient: '酷狗',
  KuwoMusicClient: '酷我',
  MiguMusicClient: '咪咕',
  Pjmp3Client: 'pjmp3',
};

function SingleSearchPage() {
  const { message } = App.useApp();
  const selectedSources = useUIStore((state) => state.selectedSources);
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState<Song[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);

  const handleDownload = useCallback(async (songs: Song[]) => {
    if (songs.length === 0) {
      message.warning('请选择要下载的歌曲');
      return;
    }

    setDownloadLoading(true);
    try {
      await downloadApi.startDownload(songs);
      message.success(`已提交 ${songs.length} 首歌曲到下载队列`);
    } catch (error: any) {
      message.error(error?.message || '提交下载失败');
    } finally {
      setDownloadLoading(false);
    }
  }, [message]);

  const columns: ColumnsType<Song & { key: string }> = useMemo(() => ([
    {
      title: '歌曲名',
      dataIndex: 'song_name',
      key: 'song_name',
      width: 220,
      ellipsis: true,
    },
    {
      title: '歌手',
      dataIndex: 'singers',
      key: 'singers',
      width: 180,
      ellipsis: true,
    },
    {
      title: '专辑',
      dataIndex: 'album',
      key: 'album',
      width: 180,
      ellipsis: true,
      render: (value: string) => value || '-',
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (value: string) => value || '-',
    },
    {
      title: '时长',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      render: (value: string) => value || '-',
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 110,
      render: (value: string) => <Tag color="blue">{SOURCE_LABELS[value] || value}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_value, record) => (
        <Button
          type="link"
          icon={<DownloadOutlined />}
          onClick={() => handleDownload([record])}
        >
          下载
        </Button>
      ),
    },
  ]), [handleDownload]);

  const tableData = useMemo(
    () => results.map((song, index) => ({ ...song, key: `${song.song_name}-${song.singers}-${song.source}-${index}` })),
    [results]
  );

  const handleSearch = useCallback(async () => {
    const trimmed = keyword.trim();
    if (!trimmed) {
      message.warning('请输入歌曲名、歌手或关键词');
      return;
    }
    if (selectedSources.length === 0) {
      message.warning('请至少选择一个音乐源');
      return;
    }

    setLoading(true);
    setSelectedRowKeys([]);

    try {
      const response = await searchApi.searchMusic(trimmed, selectedSources);
      const songs = response.data.songs || [];
      setResults(songs);

      if (songs.length === 0) {
        message.info('未找到匹配结果');
      } else {
        message.success(`搜索完成，找到 ${songs.length} 条结果`);
      }
    } catch (error: any) {
      message.error(error?.message || '单曲搜索失败');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [keyword, message, selectedSources]);

  const selectedSongs = useMemo(
    () => tableData.filter((song) => selectedRowKeys.includes(song.key)),
    [selectedRowKeys, tableData]
  );

  return (
    <div className="page">
      <Title level={2} className="page-title">单曲搜索</Title>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Alert
              type="info"
              showIcon
              message="桌面版和 Web 版现在共用同一套后端搜索与下载核心。这里提供单曲搜索入口，补齐 Web 主界面的能力缺口。"
            />

            <SourceSelector />

            <Space.Compact style={{ width: '100%' }}>
              <Input
                size="large"
                value={keyword}
                placeholder="输入歌曲名、歌手或关键词，例如：夜曲 周杰伦"
                onChange={(event) => setKeyword(event.target.value)}
                onPressEnter={handleSearch}
              />
              <Button
                type="primary"
                size="large"
                icon={<SearchOutlined />}
                loading={loading}
                onClick={handleSearch}
              >
                搜索
              </Button>
            </Space.Compact>
          </Space>
        </Card>

        <Card
          title={<Text strong>搜索结果 ({tableData.length})</Text>}
          extra={(
            <Space>
              <Text type="secondary">
                已选 <Text strong>{selectedSongs.length}</Text> 首
              </Text>
              <Button
                icon={<CheckSquareOutlined />}
                onClick={() => setSelectedRowKeys(tableData.map((song) => song.key))}
                disabled={tableData.length === 0}
              >
                全选
              </Button>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                loading={downloadLoading}
                disabled={selectedSongs.length === 0}
                onClick={() => handleDownload(selectedSongs)}
              >
                下载选中
              </Button>
            </Space>
          )}
        >
          <Table
            rowSelection={{
              selectedRowKeys,
              onChange: setSelectedRowKeys,
            }}
            columns={columns}
            dataSource={tableData}
            loading={loading}
            pagination={{ pageSize: 10, showSizeChanger: false }}
            scroll={{ x: 980 }}
            locale={{ emptyText: '输入关键词后开始搜索' }}
          />
        </Card>
      </Space>
    </div>
  );
}

export default SingleSearchPage;
