/**
 * 搜索结果表格组件
 *
 * 显示搜索结果，支持单歌下载
 */
import { Table, Button, Tag, Typography, message } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useState } from 'react';
import { Song } from '../../types';
import { downloadApi } from '../../services/api';

const { Text } = Typography;

interface SearchResultsTableProps {
  data: Song[];
  loading?: boolean;
}

function SearchResultsTable({ data, loading }: SearchResultsTableProps) {
  const [downloadingRows, setDownloadingRows] = useState<Set<string>>(new Set());

  /**
   * 下载单首歌曲
   */
  const handleDownload = async (song: Song) => {
    const rowKey = `${song.song_name}-${song.source}`;
    
    try {
      // 添加到下载中状态
      setDownloadingRows(prev => new Set(prev).add(rowKey));
      
      message.loading({ content: `正在下载 ${song.song_name}...`, key: rowKey });

      // 调用下载API
      const response = await downloadApi.startDownload([song]);
      
      if (response.data.success) {
        message.success({ 
          content: `${song.song_name} 下载已开始！`, 
          key: rowKey,
          duration: 3
        });
      } else {
        throw new Error('下载失败');
      }
    } catch (error: any) {
      message.error({ 
        content: `下载失败: ${error.message || '未知错误'}`, 
        key: rowKey,
        duration: 3
      });
    } finally {
      // 移除下载中状态
      setDownloadingRows(prev => {
        const newSet = new Set(prev);
        newSet.delete(rowKey);
        return newSet;
      });
    }
  };

  /**
   * 表格列定义
   */
  const columns: ColumnsType<Song> = [
    {
      title: '歌曲名称',
      dataIndex: 'song_name',
      key: 'song_name',
      width: 200,
      ellipsis: true,
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: '歌手',
      dataIndex: 'singers',
      key: 'singers',
      width: 150,
      ellipsis: true,
    },
    {
      title: '专辑',
      dataIndex: 'album',
      key: 'album',
      width: 150,
      ellipsis: true,
      render: (album) => album || <Text type="secondary">-</Text>,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size) => size || <Text type="secondary">-</Text>,
    },
    {
      title: '时长',
      dataIndex: 'duration',
      key: 'duration',
      width: 80,
      render: (duration) => duration || <Text type="secondary">-</Text>,
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 120,
      render: (source) => {
        const sourceLabels: Record<string, { name: string; color: string }> = {
          'QQMusicClient': { name: 'QQ音乐', color: 'green' },
          'NeteaseMusicClient': { name: '网易云', color: 'red' },
          'KugouMusicClient': { name: '酷狗', color: 'blue' },
          'KuwoMusicClient': { name: '酷我', color: 'orange' },
        };
        const info = sourceLabels[source] || { name: source, color: 'default' };
        return <Tag color={info.color}>{info.name}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => {
        const rowKey = `${record.song_name}-${record.source}`;
        const isDownloading = downloadingRows.has(rowKey);
        
        return (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record)}
            size="small"
            loading={isDownloading}
            disabled={isDownloading}
          >
            下载
          </Button>
        );
      },
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      loading={loading}
      rowKey={(record) => `${record.song_name}-${record.source}`}
      pagination={{
        pageSize: 20,
        showSizeChanger: true,
        showTotal: (total) => `共 ${total} 首`,
        pageSizeOptions: ['10', '20', '50', '100'],
      }}
      scroll={{ x: 1200 }}
      locale={{
        emptyText: '暂无搜索结果',
      }}
    />
  );
}

export default SearchResultsTable;
