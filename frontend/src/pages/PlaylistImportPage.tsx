/**
 * 歌单导入页面（简化版V2）
 *
 * 核心功能：
 * - 3列可编辑表格（歌名、歌手、专辑）
 * - 4个音乐源checkbox
 * - 批量搜索功能
 * - 相似度颜色编码
 * - 错误日志保存
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Table,
  Tag,
  Checkbox,
  Progress,
  Row,
  Col,
  Statistic,
  Divider,
} from 'antd';
import {
  LinkOutlined,
  SearchOutlined,
  CheckCircleFilled,
  FolderOpenOutlined,
  ClockCircleFilled,
  PlayCircleFilled,
  DownloadOutlined,
  SelectOutlined,
  SwapOutlined,
  DownOutlined,
  FolderOutlined,
} from '@ant-design/icons';
import { App, Dropdown } from 'antd';
import type { MenuProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { BatchMatchInfoV2, MatchCandidate } from '../types';
import { saveErrorLog } from '../utils/errorLogger';
import { playlistApi } from '../services/api';
import { useUIStore } from '../stores/useUIStore';
import SourceSelector from '../components/common/SourceSelector';

const { Title, Text } = Typography;

// 音乐源配置
const SOURCE_CONFIG: Record<string, { label: string; color: string; shortLabel: string }> = {
  'QQMusicClient': { label: 'QQ音乐', color: 'green', shortLabel: 'QQ' },
  'NeteaseMusicClient': { label: '网易云', color: 'red', shortLabel: '网易' },
  'KugouMusicClient': { label: '酷狗', color: 'blue', shortLabel: '酷狗' },
  'KuwoMusicClient': { label: '酷我', color: 'orange', shortLabel: '酷我' },
};

// 歌曲数据类型
interface PlaylistSong {
  key: number;
  name: string;
  artist: string;
  album: string;
  duration: number;
  batchMatch?: BatchMatchInfoV2;
  selectedIndex?: number;
}

// 可编辑单元格组件
interface EditableCellProps {
  value: string;
  onChange: (value: string) => void;
}

const EditableCell: React.FC<EditableCellProps> = ({ value, onChange }) => {
  const [editing, setEditing] = useState(false);

  return editing ? (
    <Input
      defaultValue={value}
      onBlur={(e) => {
        setEditing(false);
        onChange(e.target.value);
      }}
      onPressEnter={(e) => {
        setEditing(false);
        onChange((e.target as HTMLInputElement).value);
      }}
      autoFocus
      size="small"
    />
  ) : (
    <div
      onClick={() => setEditing(true)}
      style={{
        cursor: 'pointer',
        padding: '4px 8px',
        borderRadius: 4,
        transition: 'background 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = '#f0f0f0';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'transparent';
      }}
    >
      {value || '(点击编辑)'}
    </div>
  );
};

function PlaylistImportPage() {
  const { message: messageApi } = App.useApp();
  const { selectedSources } = useUIStore();

  // 状态管理
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [songs, setSongs] = useState<PlaylistSong[]>([]);
  const [platform, setPlatform] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState(0);
  const [selectedForDownload, setSelectedForDownload] = useState<Set<number>>(new Set());
  const [searchCompleted, setSearchCompleted] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [downloadPath, setDownloadPath] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const folderInputRef = React.useRef<HTMLInputElement>(null);

  // Refs 用于存储最新状态，避免闭包捕获问题
  const searchedSongsRef = React.useRef<PlaylistSong[]>([]);  // 存储正在搜索的歌曲列表
  const hasRestoredRef = React.useRef(false);  // 防止重复恢复任务

  // 统计数据
  const stats = useMemo(() => {
    const total = songs.length;
    const matched = searchCompleted ? songs.filter((s) => s.batchMatch?.has_match).length : 0;
    const selected = selectedForDownload.size;
    return { total, matched, selected, unmatched: total - matched };
  }, [songs, selectedForDownload, searchCompleted]);

  // 初始化默认音乐源
  useEffect(() => {
    const store = useUIStore.getState();
    // 如果没有选中任何音乐源，设置为默认值
    if (!store.selectedSources || store.selectedSources.length === 0) {
      console.log('[初始化] 设置默认音乐源');
      store.resetSources();
    }
    // 触发从 API 获取音乐源
    if (!store.sourcesLoaded) {
      store.fetchSources();
    }
  }, []);

  // 页面加载时检查是否有未完成的任务（支持页面切换后恢复）
  useEffect(() => {
    // 只在组件首次挂载时恢复一次，避免重复触发
    if (hasRestoredRef.current) {
      return;
    }

    const savedTaskId = localStorage.getItem('currentSearchTaskId');
    const savedSongsJson = localStorage.getItem('currentSearchSongs');

    // 只在以下情况恢复任务：
    // 1. 当前没有正在进行的搜索
    // 2. 有保存的任务ID
    // 3. 有保存的歌曲列表
    // 4. 当前有歌曲显示
    if (!searching && savedTaskId && savedSongsJson && songs.length > 0) {
      try {
        const savedKeys: number[] = JSON.parse(savedSongsJson);
        const songsToSearch = songs.filter(s => savedKeys.includes(s.key));

        if (songsToSearch.length > 0) {
          console.log('[页面恢复] 发现未完成的搜索任务:', savedTaskId);
          hasRestoredRef.current = true;  // 标记已尝试恢复
          searchedSongsRef.current = songsToSearch;  // 保存到 ref
          messageApi.info('检测到未完成的搜索，正在恢复...');
          setSearching(true);
          pollTaskProgress(savedTaskId);
        }
      } catch (err) {
        console.error('[页面恢复] 恢复任务失败:', err);
        // 清除无效的任务ID
        localStorage.removeItem('currentSearchTaskId');
        localStorage.removeItem('currentSearchSongs');
        hasRestoredRef.current = true;  // 标记已尝试恢复
      }
    }

    // 组件卸载时清理轮询
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [searching, songs.length]);  // 只依赖 searching 和 songs.length

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
    setSelectedForDownload(new Set());

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
          duration: song.duration || 0,
        }));

        setSongs(parsedSongs);
        setPlatform(data.platform);
        messageApi.success({
          content: `成功解析 ${data.platform}，共 ${parsedSongs.length} 首歌曲`,
          key: 'parse',
        });
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
  }, [url, messageApi]);

  /**
   * 编辑歌曲信息
   */
  const handleEditSong = useCallback((key: number, field: keyof PlaylistSong, value: string) => {
    setSongs((prev) =>
      prev.map((song) =>
        song.key === key
          ? { ...song, [field]: value }
          : song
      )
    );
  }, []);

  /**
   * 批量搜索（使用后台任务模式，支持页面切换）
   *
   * 新架构：启动后台任务 → 获取task_id → 轮询查询进度
   * 优势：即使切换页面，搜索也会在后台继续执行
   */
  const handleBatchSearch = useCallback(async () => {
    // 获取选中的歌曲进行搜索
    const songsToSearch = selectedForDownload.size > 0
      ? songs.filter((s) => selectedForDownload.has(s.key))
      : songs;

    if (songsToSearch.length === 0) {
      messageApi.warning('请先勾选要搜索的歌曲');
      return;
    }

    if (selectedSources.length === 0) {
      messageApi.warning('请先选择音乐源');
      return;
    }

    // 保存到 ref，避免闭包捕获问题
    searchedSongsRef.current = songsToSearch;

    setSearching(true);
    setSearchProgress(0);
    setSearchCompleted(false);
    setSearchError(null);

    try {
      console.log('[后台搜索] 启动批量搜索', {
        songCount: songsToSearch.length,
        sources: selectedSources,
      });

      // 启动后台搜索任务
      const response = await fetch('/api/playlist/batch-search-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          songs: songsToSearch.map((s) => ({
            name: s.name,
            artist: s.artist,
            album: s.album,
          })),
          sources: selectedSources,
          concurrency: 8,
        }),
      });

      if (!response.ok) {
        throw new Error(`启动搜索失败: ${response.status}`);
      }

      const { task_id, total } = await response.json();
      console.log('[后台搜索] 任务已启动:', task_id, '总数:', total);

      // 保存task_id到localStorage，支持页面切换后恢复
      localStorage.setItem('currentSearchTaskId', task_id);
      localStorage.setItem('currentSearchSongs', JSON.stringify(songsToSearch.map(s => s.key)));

      // 开始轮询任务进度（不再传递 songsToSearch 参数，从 ref 读取）
      pollTaskProgress(task_id);

    } catch (err: any) {
      console.error('[后台搜索] 启动失败:', err);
      saveErrorLog(err, '批量搜索启动失败');
      const errorMsg = err.message || '启动搜索失败，请检查网络连接';
      setSearchError(errorMsg);
      setSearching(false);
      messageApi.error(errorMsg);
    }
  }, [songs, selectedSources, selectedForDownload, messageApi]);

  /**
   * 轮询任务进度
   * 不再接收 songsToSearch 参数，从 searchedSongsRef 读取
   */
  const pollTaskProgress = useCallback((
    taskId: string
  ) => {
    let intervalId: NodeJS.Timeout | null = null;

    const poll = async () => {
      try {
        const response = await fetch(`/api/playlist/batch-search-status/${taskId}`);
        if (!response.ok) {
          throw new Error(`查询状态失败: ${response.status}`);
        }

        const task = await response.json();
        console.log('[后台搜索] 任务状态:', task.status, '进度:', task.progress, '/', task.total);

        // 更新进度
        if (task.total > 0) {
          setSearchProgress(Math.round(task.progress / task.total * 100));
        }

        // 检查任务状态
        if (task.status === 'completed') {
          // 清理轮询
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
          localStorage.removeItem('currentSearchTaskId');
          localStorage.removeItem('currentSearchSongs');

          // 处理搜索结果（从 ref 读取歌曲列表）
          handleSearchComplete(task.result);

        } else if (task.status === 'failed') {
          // 清理轮询
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
          localStorage.removeItem('currentSearchTaskId');
          localStorage.removeItem('currentSearchSongs');

          // 处理失败
          setSearching(false);
          setSearchCompleted(true);
          setSearchError(task.error || '搜索失败');
          messageApi.error(task.error || '搜索失败');

        } else if (task.status === 'cancelled') {
          // 清理轮询
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
          localStorage.removeItem('currentSearchTaskId');
          localStorage.removeItem('currentSearchSongs');

          // 处理取消
          setSearching(false);
          setSearchCompleted(true);
          messageApi.info('搜索已取消');
        }

      } catch (err: any) {
        console.error('[后台搜索] 查询状态失败:', err);
        // 继续轮询，不中断
      }
    };

    // 立即执行一次
    poll();

    // 每秒轮询一次
    intervalId = setInterval(poll, 1000);

    // 保存intervalId以便清理
    setPollingInterval(intervalId);
  }, [messageApi]);

  /**
   * 处理搜索完成
   * 从 searchedSongsRef 读取歌曲列表，使用函数式更新避免闭包问题
   */
  const handleSearchComplete = useCallback((
    result: { total: number; matched: number; matches: Record<string, BatchMatchInfoV2> }
  ) => {
    console.log('[后台搜索] 搜索完成:', result.matched, '/', result.total);

    // 从 ref 读取正在搜索的歌曲列表
    const songsToSearch = searchedSongsRef.current;

    // 转换结果格式
    const resultMap = new Map<number, BatchMatchInfoV2>();
    Object.entries(result.matches || {}).forEach(([originalLine, match]) => {
      const song = songsToSearch.find((s) =>
        `${s.name} - ${s.artist}` === originalLine
      );
      if (song) {
        resultMap.set(song.key, match);
      }
    });

    console.log('[后台搜索] 结果映射:', resultMap.size, '/', songsToSearch.length);

    // 使用函数式更新，避免闭包捕获旧的 songs
    setSongs((prevSongs) => {
      // 更新歌曲列表，添加搜索结果
      return prevSongs.map((song) => {
        if (resultMap.has(song.key)) {
          return {
            ...song,
            batchMatch: resultMap.get(song.key),
            selectedIndex: 0,
          };
        }
        return song;
      });
    });

    // 自动选中已匹配的歌曲
    const matchedKeys = songsToSearch
      .filter((s) => resultMap.get(s.key)?.has_match)
      .map((s) => s.key);
    setSelectedForDownload(new Set(matchedKeys));

    // 更新状态
    setSearching(false);
    setSearchCompleted(true);
    messageApi.success(`搜索完成！${result.matched}/${result.total} 首歌曲匹配成功`);
  }, [messageApi]);

  /**

  /**
   * 切换候选源
   */
  const handleChangeCandidate = useCallback((songKey: number, candidate: MatchCandidate) => {
    setSongs((prev) =>
      prev.map((song) => {
        if (song.key === songKey) {
          return {
            ...song,
            batchMatch: song.batchMatch
              ? {
                  ...song.batchMatch,
                  current_match: candidate,
                }
              : undefined,
          };
        }
        return song;
      })
    );
  }, []);

  /**
   * 下载选中的歌曲
   */
  const handleDownload = useCallback(async () => {
    if (selectedForDownload.size === 0) {
      messageApi.warning('请先选择要下载的歌曲');
      return;
    }

    const songsToDownload = songs.filter((s) =>
      selectedForDownload.has(s.key) && s.batchMatch?.current_match
    );

    if (songsToDownload.length === 0) {
      messageApi.warning('没有可下载的歌曲（已匹配的歌曲才能下载）');
      return;
    }

    // 构造下载请求数据 - 包含所有下载所需的字段
    const downloadData = songsToDownload.map((song) => {
      const match = song.batchMatch?.current_match!;
      return {
        song_name: match.song_name,
        singers: match.singers,
        album: match.album || '',
        size: match.size || '',
        duration: match.duration || '',
        source: match.source,
        // 关键：传递 download_url 用于直接下载
        download_url: match.download_url,
        ext: match.ext || 'mp3',
        duration_s: match.duration_s || 0,
        // 关键：传递 song_id 用于从缓存获取 SongInfo 对象
        song_id: match.song_id,
        // 传递相似度信息用于调试
        similarity: match.similarity,
      };
    });

    try {
      setDownloading(true);
      setDownloadProgress(0);
      messageApi.loading({ content: `正在下载 ${downloadData.length} 首歌曲...`, key: 'download' });

      console.log('[下载] 发送下载请求:', downloadData);
      console.log('[下载] 下载路径:', downloadPath || '(默认)');

      // 修复：使用GET请求配合URL参数，后端只支持GET
      const songsJson = JSON.stringify(downloadData);
      const params = new URLSearchParams({ songs_json: songsJson });
      if (downloadPath) {
        params.append('download_dir', downloadPath);
      }

      const response = await fetch(`/api/download/stream?${params.toString()}`, {
        method: 'GET',
        headers: {
          Accept: 'text/event-stream',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法获取响应流');
      }

      const decoder = new TextDecoder();
      let downloadedCount = 0;
      let failedCount = 0;
      const totalSongs = downloadData.length;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('event:')) {
            const eventType = line.replace('event: ', '').trim();
            const lineIndex = lines.indexOf(line);
            const dataLine = lineIndex >= 0 && lineIndex + 1 < lines.length ? lines[lineIndex + 1] : null;
            if (dataLine && dataLine.startsWith('data:')) {
              try {
                const data = JSON.parse(dataLine.replace('data: ', ''));

                if (eventType === 'progress') {
                  if (data.success) {
                    downloadedCount++;
                    const progress = Math.round((downloadedCount / totalSongs) * 100);
                    setDownloadProgress(progress);
                    console.log(`[下载] ${downloadedCount}/${totalSongs} (${progress}%): ${data.song_name || '完成'}`);
                  } else if (data.error) {
                    failedCount++;
                    console.error(`[下载] 失败: ${data.error}`);
                  }
                } else if (eventType === 'complete') {
                  downloadedCount = data.completed || 0;
                  failedCount = data.failed || 0;
                  setDownloadProgress(100);
                  setDownloading(false);
                  messageApi.success({
                    content: `下载完成！成功: ${downloadedCount}, 失败: ${failedCount}`,
                    key: 'download',
                    duration: 5,
                  });
                  console.log('[下载] 完成:', data);
                } else if (eventType === 'error') {
                  setDownloading(false);
                  messageApi.error({
                    content: `下载错误: ${data.error || '未知错误'}`,
                    key: 'download',
                  });
                } else if (eventType === 'debug') {
                  console.log('[下载] DEBUG:', data.message);
                }
              } catch (parseError) {
                console.error('[下载] 解析响应失败:', parseError);
              }
            }
          }
        }
      }
    } catch (err: any) {
      console.error('[下载] 错误:', err);
      setDownloading(false);
      messageApi.error({
        content: err.message || '下载失败，请检查网络连接',
        key: 'download',
      });
    }
  }, [songs, selectedForDownload, messageApi, downloadPath]);

  /**
   * 获取相似度颜色
   */
  const getSimilarityColor = (similarity: number): string => {
    const percent = Math.round(similarity * 100);
    if (percent >= 80) return '#52c41a'; // 绿色
    if (percent >= 60) return '#faad14'; // 黄色
    return '#ff4d4f'; // 红色
  };

  /**
   * 解析结果表格列（不含匹配结果）
   */
  const parseColumns: ColumnsType<PlaylistSong> = [
    {
      title: '歌名',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: PlaylistSong) => (
        <EditableCell
          value={text}
          onChange={(value) => handleEditSong(record.key, 'name', value)}
        />
      ),
    },
    {
      title: '歌手',
      dataIndex: 'artist',
      key: 'artist',
      width: 180,
      render: (text: string, record: PlaylistSong) => (
        <EditableCell
          value={text}
          onChange={(value) => handleEditSong(record.key, 'artist', value)}
        />
      ),
    },
    {
      title: '专辑',
      dataIndex: 'album',
      key: 'album',
      width: 180,
      render: (text: string, record: PlaylistSong) => (
        <EditableCell
          value={text}
          onChange={(value) => handleEditSong(record.key, 'album', value)}
        />
      ),
    },
  ];

  /**
   * 搜索结果表格列（含匹配结果）
   */
  const searchColumns: ColumnsType<PlaylistSong> = [
    {
      title: '歌名',
      dataIndex: 'name',
      key: 'name',
      width: 180,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '歌手',
      dataIndex: 'artist',
      key: 'artist',
      width: 120,
    },
    {
      title: '专辑',
      dataIndex: 'album',
      key: 'album',
      width: 120,
      ellipsis: true,
    },
    {
      title: '匹配结果',
      key: 'match',
      width: 350,
      render: (_: any, record: PlaylistSong) => {
        if (!record.batchMatch || !record.batchMatch.has_match) {
          return <Text type="secondary">未匹配</Text>;
        }

        const current = record.batchMatch.current_match;
        if (!current) {
          return <Text type="secondary">未匹配</Text>;
        }

        const simPercent = current.similarity != null ? Math.round(current.similarity * 100) : 0;
        const simColor = getSimilarityColor(current.similarity ?? 0);

        // 获取所有候选源 - 使用安全的扁平化方式
        const allCandidates = Object.values(record.batchMatch?.all_matches || {})
          .flat()
          .filter((c): c is MatchCandidate =>
            c !== null &&
            c !== undefined &&
            typeof c === 'object' &&
            'song_name' in c &&
            'source' in c
          );

        // 创建下拉菜单
        const candidateMenu: MenuProps = {
          items: allCandidates.map((candidate) => ({
            key: `${candidate.source}-${candidate.song_name}`,
            label: (
              <Space size="small" direction="vertical" style={{ lineHeight: 1.2 }}>
                <Space size="small">
                  <Tag color={SOURCE_CONFIG[candidate.source]?.color || 'default'}>
                    {SOURCE_CONFIG[candidate.source]?.shortLabel || candidate.source}
                  </Tag>
                  <Text>{candidate.song_name}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {Math.round(candidate.similarity * 100)}%
                  </Text>
                </Space>
                {candidate.duration && (
                  <Text type="secondary" style={{ fontSize: 11, marginLeft: 24 }}>
                    ⏱ {candidate.duration}
                  </Text>
                )}
              </Space>
            ),
            onClick: () => handleChangeCandidate(record.key, candidate),
          })),
        };

        return (
          <Space size="small" wrap>
            <Dropdown menu={candidateMenu} trigger={['click']} disabled={allCandidates.length <= 1}>
              <Space size="small" style={{ cursor: allCandidates.length > 1 ? 'pointer' : 'default' }}>
                <Tag color={SOURCE_CONFIG[current.source]?.color || 'default'}>
                  {SOURCE_CONFIG[current.source]?.shortLabel || current.source}
                </Tag>
                {allCandidates.length > 1 && <DownOutlined style={{ fontSize: 12 }} />}
              </Space>
            </Dropdown>
            <Text style={{ color: simColor, fontWeight: 600 }}>{simPercent}%</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {current.song_name}
            </Text>
          </Space>
        );
      },
    },
  ];

  // 空状态
  const emptyNode = (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 300,
        color: '#8e8e93',
      }}
    >
      <FolderOpenOutlined style={{ fontSize: 48, marginBottom: 16, opacity: 0.5 }} />
      <Text>暂无歌曲</Text>
      <Text type="secondary" style={{ fontSize: 12 }}>
        粘贴歌单链接并点击解析来导入歌曲
      </Text>
    </div>
  );

  return (
    <div className="page">
      <Title level={2} className="page-title">歌单导入</Title>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 链接输入区域 */}
        <Card bordered={false} style={{ borderRadius: 12 }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <Title level={4} style={{ marginBottom: 8 }}>支持的歌单平台</Title>
              <Space size="small">
                <Tag color="red" style={{ borderRadius: 4 }}>网易云音乐</Tag>
                <Tag color="blue" style={{ borderRadius: 4 }}>QQ音乐</Tag>
              </Space>
            </div>

            <Input
              placeholder="粘贴网易云或QQ音乐的歌单分享链接"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              size="large"
              prefix={<LinkOutlined style={{ color: '#8e8e93' }} />}
              onPressEnter={handleParse}
              style={{ borderRadius: 8 }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                示例：https://music.163.com/#/playlist?id=123456789
              </Text>
            </div>

            <Button
              type="primary"
              size="large"
              onClick={handleParse}
              loading={loading}
              disabled={!url.trim()}
              icon={<SearchOutlined />}
              style={{ borderRadius: 8, height: 44 }}
            >
              解析歌单
            </Button>
          </Space>
        </Card>

        {/* 歌曲列表 */}
        {songs.length > 0 && (
          <Card bordered={false} style={{ borderRadius: 12 }} bodyStyle={{ padding: '16px 24px' }}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {/* 统计信息栏 */}
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="歌曲总数"
                    value={stats.total}
                    prefix={<FolderOpenOutlined />}
                    valueStyle={{ color: '#000', fontWeight: 600 }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="已匹配"
                    value={stats.matched}
                    valueStyle={{ color: '#34c759', fontWeight: 600 }}
                    prefix={<CheckCircleFilled />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="待匹配"
                    value={stats.unmatched}
                    valueStyle={{ color: '#ff9500', fontWeight: 600 }}
                    prefix={<ClockCircleFilled />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="已选中"
                    value={stats.selected}
                    valueStyle={{ color: '#007aff', fontWeight: 600 }}
                    prefix={<PlayCircleFilled />}
                  />
                </Col>
              </Row>

              {/* 操作按钮栏 */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 16px',
                  background: '#fafafa',
                  borderRadius: 8,
                }}
              >
                <SourceSelector label="音乐源：" showQuickMode />

                <Space>
                  {!searchCompleted ? (
                    <>
                      <Button
                        onClick={() => {
                          const allKeys = songs.map((s) => s.key);
                          setSelectedForDownload(new Set(allKeys));
                        }}
                        disabled={songs.length === 0}
                        icon={<SelectOutlined />}
                      >
                        全选
                      </Button>
                      <Button
                        onClick={() => {
                          setSelectedForDownload(new Set());
                        }}
                        disabled={selectedForDownload.size === 0}
                      >
                        反选
                      </Button>
                      <Button
                        type="primary"
                        onClick={handleBatchSearch}
                        loading={searching}
                        disabled={selectedSources.length === 0 || selectedForDownload.size === 0}
                        icon={<SearchOutlined />}
                      >
                        批量搜索 {selectedForDownload.size > 0 && `(${selectedForDownload.size})`}
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        onClick={() => {
                          const allMatchedKeys = songs
                            .filter((s) => s.batchMatch?.has_match)
                            .map((s) => s.key);
                          setSelectedForDownload(new Set(allMatchedKeys));
                        }}
                        icon={<SelectOutlined />}
                      >
                        全选已匹配
                      </Button>
                      <Button
                        onClick={() => {
                          const newSelected = new Set<number>();
                          songs.forEach((s) => {
                            if (!selectedForDownload.has(s.key) && s.batchMatch?.has_match) {
                              newSelected.add(s.key);
                            }
                          });
                          setSelectedForDownload(newSelected);
                        }}
                      >
                        反选
                      </Button>
                      <Button
                        onClick={() => setSelectedForDownload(new Set())}
                        disabled={selectedForDownload.size === 0}
                      >
                        清空
                      </Button>
                      <Button
                        onClick={() => {
                          setSearchCompleted(false);
                          setSongs((prev) =>
                            prev.map((s) => ({ ...s, batchMatch: undefined, selectedIndex: undefined }))
                          );
                          setSelectedForDownload(new Set());
                        }}
                        icon={<SwapOutlined />}
                      >
                        重新搜索
                      </Button>
                    </>
                  )}
                </Space>
              </div>

              {/* 搜索进度 */}
              {searching && (
                <Progress
                  percent={searchProgress}
                  status="active"
                  strokeColor="#007aff"
                  format={(percent) => `搜索进度: ${percent}%`}
                />
              )}

              {/* 搜索错误提示 */}
              {searchError && (
                <div
                  style={{
                    padding: '12px 16px',
                    background: '#fff2f0',
                    border: '1px solid #ffccc7',
                    borderRadius: 8,
                    color: '#ff4d4f',
                  }}
                >
                  <Text strong>❌ {searchError}</Text>
                </div>
              )}

              {/* 解析结果表格 */}
              <div style={{ marginBottom: searchCompleted ? 24 : 0 }}>
                <Text strong style={{ display: 'block', marginBottom: 12 }}>
                  📋 解析结果（{songs.length} 首歌曲）
                </Text>
                <Table
                  columns={parseColumns}
                  dataSource={songs}
                  rowKey="key"
                  pagination={false}
                  scroll={{ y: 300 }}
                  size="middle"
                  rowSelection={
                    !searchCompleted
                      ? {
                          type: 'checkbox',
                          selectedRowKeys: Array.from(selectedForDownload),
                          onChange: (keys) => setSelectedForDownload(new Set(keys.map(Number))),
                        }
                      : undefined
                  }
                  locale={{ emptyText: emptyNode }}
                />
              </div>

              {/* 搜索结果表格 - 仅在搜索完成后显示 */}
              {searchCompleted && (
                <div>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}>
                    🎯 匹配结果（{stats.matched}/{stats.total} 首匹配成功）
                  </Text>
                  <Table
                    columns={searchColumns}
                    dataSource={songs}
                    rowKey="key"
                    pagination={false}
                    scroll={{ y: 300 }}
                    size="middle"
                    rowSelection={{
                      type: 'checkbox',
                      selectedRowKeys: Array.from(selectedForDownload),
                      onChange: (keys) => setSelectedForDownload(new Set(keys.map(Number))),
                      getCheckboxProps: (record: PlaylistSong) => ({
                        disabled: !record.batchMatch?.has_match,
                      }),
                    }}
                    rowClassName={(record) =>
                      record.batchMatch?.has_match ? 'matched-row' : 'unmatched-row'
                    }
                    locale={{
                      emptyText: (
                        <div style={{ padding: 40, textAlign: 'center', color: '#8e8e93' }}>
                          暂无匹配结果
                        </div>
                      ),
                    }}
                  />
                </div>
              )}

              {/* 下载区域 - 仅在搜索完成后显示 */}
              {searchCompleted && (
                <div style={{ marginTop: 24 }}>
                  <Divider />
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {/* 下载路径选择 */}
                    <div>
                      <Text strong style={{ marginBottom: 8, display: 'block' }}>
                        <FolderOutlined /> 下载路径
                      </Text>
                      <Space.Compact style={{ width: '100%' }}>
                        <Input
                          value={downloadPath}
                          onChange={(e) => setDownloadPath(e.target.value)}
                          placeholder="留空使用默认路径：musicdl_outputs/KugouMusicClient/"
                          prefix={<FolderOutlined />}
                        />
                        <Button
                          icon={<FolderOpenOutlined />}
                          onClick={() => {
                            // 触发隐藏的文件夹选择input
                            if (folderInputRef.current) {
                              folderInputRef.current.click();
                            }
                          }}
                        >
                          浏览
                        </Button>
                        {/* 隐藏的文件夹选择input */}
                        <input
                          ref={folderInputRef}
                          type="file"
                          webkitdirectory
                          directory
                          style={{ display: 'none' }}
                          onChange={(e) => {
                            const files = e.target.files;
                            if (files && files.length > 0) {
                              // 获取选中文件夹的路径
                              const path = files[0].webkitRelativePath?.split('/')[0] || '';
                              setDownloadPath(path);
                              messageApi.success(`已选择下载路径: ${path}`);
                            }
                          }}
                        />
                      </Space.Compact>
                      <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                        默认路径：musicdl_outputs/KugouMusicClient/
                      </Text>
                    </div>

                    {/* 下载进度 */}
                    {downloading && (
                      <Progress
                        percent={downloadProgress}
                        status="active"
                        strokeColor="#52c41a"
                        format={(percent) => `下载进度: ${percent}%`}
                      />
                    )}

                    {/* 下载操作按钮 */}
                    <Row gutter={16} align="middle">
                      <Col>
                        <Statistic
                          title="已选中"
                          value={stats.selected}
                          suffix="首"
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Col>
                      <Col>
                        <Button
                          type="primary"
                          size="large"
                          onClick={handleDownload}
                          disabled={selectedForDownload.size === 0 || downloading}
                          loading={downloading}
                          icon={<DownloadOutlined />}
                        >
                          下载选中 {selectedForDownload.size > 0 && `(${selectedForDownload.size})`}
                        </Button>
                      </Col>
                    </Row>
                  </Space>
                </div>
              )}
            </Space>
          </Card>
        )}

        {/* 使用提示 */}
        <Card bordered={false} style={{ borderRadius: 12 }} bodyStyle={{ padding: '16px 24px' }}>
          <Title level={5} style={{ marginBottom: 12 }}>
            💡 使用提示
          </Title>
          <ul style={{ paddingLeft: 20, margin: 0, color: '#666', lineHeight: 1.8 }}>
            <li>确保歌单为<strong>公开状态</strong>（非私密歌单）</li>
            <li>点击表格内文字可直接编辑歌曲信息</li>
            <li>选择音乐源后点击"批量搜索"进行匹配</li>
            <li>搜索完成后会显示匹配结果表格</li>
            <li>已匹配的歌曲会自动选中，可下载</li>
            <li>部分版权保护歌曲可能无法下载</li>
          </ul>
        </Card>

        {/* 自定义样式 */}
        <style>{`
          .matched-row {
            background-color: #f6ffed;
          }
          .matched-row:hover {
            background-color: #d9f7be !important;
          }
          .unmatched-row {
            background-color: #fafafa;
          }
          .unmatched-row:hover {
            background-color: #f0f0f0 !important;
          }
        `}</style>
      </Space>
    </div>
  );
}

export default PlaylistImportPage;
