/**
 * 歌单导入板块组件
 *
 * 用于批量下载页面中的歌单导入功能
 * 包含URL输入、解析按钮、解析结果表格
 * v2: 支持歌曲选择、编辑功能，移除时长列
 */
import React, { useState, useCallback } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Table,
  Tag,
  Alert,
  Modal,
  Form,
  Input as FormInput,
} from 'antd';
import { LinkOutlined, SearchOutlined, LoadingOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { App } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { TableRowSelection } from 'antd/es/table/interface';
import { playlistApi } from '../../services/api';
import { saveErrorLog } from '../../utils/errorLogger';

const { Text } = Typography;

// 歌曲数据类型
interface PlaylistSong {
  key: number;
  name: string;
  artist: string;
  album: string;
  duration: string;
}

interface PlaylistImportSectionProps {
  /** 解析成功回调，返回解析的歌曲列表 */
  onParsed?: (songs: PlaylistSong[]) => void;
  /** 自定义样式 */
  style?: React.CSSProperties;
}

function PlaylistImportSection({
  onParsed,
  style,
}: PlaylistImportSectionProps) {
  const { message: messageApi } = App.useApp();

  // 状态管理
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [songs, setSongs] = useState<PlaylistSong[]>([]);
  const [platform, setPlatform] = useState('');
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingSong, setEditingSong] = useState<PlaylistSong | null>(null);
  const [form] = Form.useForm();

  /**
   * 解析歌单URL
   */
  const handleParse = useCallback(async () => {
    if (!url.trim()) {
      messageApi.warning('请输入歌单链接');
      return;
    }

    setLoading(true);
    setSongs([]);
    setPlatform('');
    setSelectedKeys([]);

    try {
      messageApi.loading({ content: '正在解析歌单...', key: 'parse' });

      const response = await playlistApi.parsePlaylist(url);
      const data = response.data;

      if (data.success && data.songs.length > 0) {
        const parsedSongs: PlaylistSong[] = data.songs.map((song: any, index: number) => ({
          key: index,
          name: song.name,
          artist: song.artist,
          album: song.album || '',
          duration: song.duration || '-',
        }));

        setSongs(parsedSongs);
        setPlatform(data.platform);
        // 默认全选
        setSelectedKeys(parsedSongs.map(s => s.key));
        messageApi.success({
          content: `成功解析 ${data.platform}，共 ${parsedSongs.length} 首歌曲`,
          key: 'parse',
        });

        // 回调通知父组件（传递选中的歌曲）
        if (onParsed) {
          onParsed(parsedSongs);
        }
      } else {
        const errorMsg = data.error || '无法解析歌单，请检查链接格式是否正确';
        messageApi.error({ content: errorMsg, key: 'parse' });
      }
    } catch (err: any) {
      saveErrorLog(err, '解析歌单失败');
      messageApi.error({ content: err.message || '解析失败，请检查链接是否正确', key: 'parse' });
    } finally {
      setLoading(false);
    }
  }, [url, messageApi, onParsed]);

  /**
   * 清空结果
   */
  const handleClear = useCallback(() => {
    setUrl('');
    setSongs([]);
    setPlatform('');
    setSelectedKeys([]);
  }, []);

  /**
   * 全选/取消全选
   */
  const handleSelectAll = useCallback(() => {
    if (selectedKeys.length === songs.length) {
      setSelectedKeys([]);
    } else {
      setSelectedKeys(songs.map(s => s.key));
    }
  }, [selectedKeys, songs]);

  /**
   * 删除选中的歌曲
   */
  const handleDeleteSelected = useCallback(() => {
    if (selectedKeys.length === 0) {
      messageApi.warning('请先选择要删除的歌曲');
      return;
    }
    const newSongs = songs.filter(s => !selectedKeys.includes(s.key));
    setSongs(newSongs);
    setSelectedKeys([]);
    if (onParsed) {
      onParsed(newSongs);
    }
    messageApi.success(`已删除 ${selectedKeys.length} 首歌曲`);
  }, [selectedKeys, songs, onParsed, messageApi]);

  /**
   * 编辑歌曲
   */
  const handleEdit = useCallback((song: PlaylistSong) => {
    setEditingSong(song);
    form.setFieldsValue({
      name: song.name,
      artist: song.artist,
      album: song.album,
    });
    setEditModalVisible(true);
  }, [form]);

  /**
   * 保存编辑
   */
  const handleSaveEdit = useCallback(() => {
    form.validateFields().then(values => {
      if (editingSong) {
        const newSongs = songs.map(s =>
          s.key === editingSong.key
            ? { ...s, ...values }
            : s
        );
        setSongs(newSongs);
        if (onParsed) {
          onParsed(newSongs);
        }
        messageApi.success('修改成功');
      }
      setEditModalVisible(false);
      setEditingSong(null);
    });
  }, [editingSong, songs, form, onParsed, messageApi]);

  // 行选择配置
  const rowSelection: TableRowSelection<PlaylistSong> = {
    selectedRowKeys: selectedKeys,
    onChange: (keys) => setSelectedKeys(keys),
    columnWidth: 50,
  };

  // 表格列定义
  const columns: ColumnsType<PlaylistSong> = [
    {
      title: '歌名',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      ellipsis: true,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '歌手',
      dataIndex: 'artist',
      key: 'artist',
      width: 150,
      ellipsis: true,
    },
    {
      title: '专辑',
      dataIndex: 'album',
      key: 'album',
      width: 150,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="text"
          size="small"
          icon={<EditOutlined />}
          onClick={() => handleEdit(record)}
        />
      ),
    },
  ];

  return (
    <Card
      title={
        <Space>
          <LinkOutlined />
          <Text strong>歌单导入</Text>
        </Space>
      }
      extra={
        songs.length > 0 && (
          <Space>
            {platform && <Tag color="blue">{platform}</Tag>}
            <Text type="secondary">已选 {selectedKeys.length}/{songs.length} 首</Text>
            <Button size="small" onClick={handleSelectAll}>
              {selectedKeys.length === songs.length ? '取消全选' : '全选'}
            </Button>
            <Button size="small" danger onClick={handleDeleteSelected} disabled={selectedKeys.length === 0}>
              删除选中
            </Button>
            <Button size="small" onClick={handleClear}>
              清空
            </Button>
          </Space>
        )
      }
      style={style}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 支持的平台提示 */}
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            支持：网易云音乐、QQ音乐歌单
          </Text>
        </div>

        {/* URL输入 */}
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="粘贴网易云或QQ音乐的歌单分享链接"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            size="large"
            prefix={<LinkOutlined style={{ color: '#8e8e93' }} />}
            onPressEnter={handleParse}
            disabled={loading}
          />
          <Button
            type="primary"
            size="large"
            onClick={handleParse}
            loading={loading}
            disabled={!url.trim()}
          >
            {loading ? <LoadingOutlined /> : <SearchOutlined />}
            解析歌单
          </Button>
        </Space.Compact>

        {/* 链接示例 */}
        <Text type="secondary" style={{ fontSize: 12 }}>
          示例：https://music.163.com/#/playlist?id=123456789
        </Text>

        {/* 解析结果表格 */}
        {songs.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Alert
              message={`共解析到 ${songs.length} 首歌曲，已选择 ${selectedKeys.length} 首，点击下方"批量搜索"进行匹配`}
              type="success"
              showIcon
              style={{ marginBottom: 12 }}
            />
            <Table
              columns={columns}
              dataSource={songs}
              rowKey="key"
              rowSelection={rowSelection}
              pagination={false}
              scroll={{ y: 300 }}
              size="small"
              bordered
            />
          </div>
        )}
      </Space>

      {/* 编辑弹窗 */}
      <Modal
        title="编辑歌曲信息"
        open={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingSong(null);
        }}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="歌名" rules={[{ required: true, message: '请输入歌名' }]}>
            <FormInput />
          </Form.Item>
          <Form.Item name="artist" label="歌手" rules={[{ required: true, message: '请输入歌手' }]}>
            <FormInput />
          </Form.Item>
          <Form.Item name="album" label="专辑">
            <FormInput />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

export default PlaylistImportSection;