/**
 * 批量下载页面 V2
 *
 * 新布局：
 * - 上方：文本输入板块 + 歌单导入板块（并列）
 * - 下方：匹配设置板块（匹配模式、音乐源、下载目录、过滤选项、批量搜索按钮）
 * - 结果：匹配结果表格（相似度在操作列显示）
 */
import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import {
  Card,
  Space,
  Typography,
  Button,
  Progress,
  Row,
  Col,
  Alert,
  Tag,
} from 'antd';
import {
  DownloadOutlined,
  CheckSquareOutlined,
  BorderOutlined,
  ClearOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { App } from 'antd';
import { useUIStore } from '../stores/useUIStore';
import { useLocalStorage } from '../hooks/useLocalStorage';
import BatchTextInput from '../components/batch/BatchTextInput';
import MatchSettingsPanel from '../components/batch/MatchSettingsPanel';
import PlaylistImportSection from '../components/batch/PlaylistImportSection';
import BatchResultsTable from '../components/batch/BatchResultsTable';
import { playlistApi, downloadApi } from '../services/api';
import { parseLineCount } from '../utils/format';
import { BatchMatchInfo, MATCH_MODES } from '../types';

const { Title, Text } = Typography;

// 歌单歌曲类型
interface PlaylistSong {
  key: number;
  name: string;
  artist: string;
  album: string;
  duration: string;
}

function BatchDownloadPage() {
  const { message } = App.useApp();
  const { selectedSources, matchMode } = useUIStore();

  // ========== 文本输入状态 ==========
  const [batchText, setBatchText] = useLocalStorage('batch-download-text', '');
  const [parsedCount, setParsedCount] = useState(0);

  // ========== 歌单导入状态 ==========
  const [playlistSongs, setPlaylistSongs] = useState<PlaylistSong[]>([]);

  // ========== 搜索状态 ==========
  const [searchResults, setSearchResults] = useLocalStorage<BatchMatchInfo[]>('batch-download-results', []);
  const [hasSearched, setHasSearched] = useLocalStorage('batch-download-searched', false);
  const [selectedRows, setSelectedRows, clearSelectedRows] = useLocalStorage<string[]>('batch-download-selected', []);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchProgress, setSearchProgress] = useState(0);

  // ========== 下载状态 ==========
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [downloadDir, setDownloadDir] = useState('');
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadCurrentSong, setDownloadCurrentSong] = useState('');
  const [downloadCompleted, setDownloadCompleted] = useState(0);
  const [downloadTotal, setDownloadTotal] = useState(0);
  const [showDownloadProgress, setShowDownloadProgress] = useState(false);

  // ========== 过滤选项 ==========
  const [filterShortTracks, setFilterShortTracks] = useLocalStorage('filter-short-tracks', true);
  const [filterDuplicates, setFilterDuplicates] = useLocalStorage('filter-duplicates', true);

  // SSE连接引用
  const eventSourceRef = useRef<EventSource | null>(null);
  const downloadEventSourceRef = useRef<EventSource | null>(null);

  // 组件卸载时清理SSE连接
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (downloadEventSourceRef.current) {
        downloadEventSourceRef.current.close();
        downloadEventSourceRef.current = null;
      }
    };
  }, []);

  // 计算总歌曲数（文本 + 歌单）
  const totalSongCount = useMemo(() => {
    return parsedCount + playlistSongs.length;
  }, [parsedCount, playlistSongs.length]);

  // ========== 歌单解析回调 ==========
  const handlePlaylistParsed = useCallback((songs: PlaylistSong[]) => {
    setPlaylistSongs(songs);
  }, []);

  // ========== 批量搜索 ==========
  const handleBatchSearch = useCallback(async () => {
    // 合并文本输入和歌单导入的歌曲
    const textSongs = batchText.split('\n')
      .filter(line => line.trim())
      .map(line => {
        const parts = line.split('-');
        return { name: parts[0]?.trim() || '', artist: parts[1]?.trim() || '', album: '' };
      });

    const playlistSongsList = playlistSongs.map(s => ({
      name: s.name,
      artist: s.artist,
      album: s.album,
    }));

    const allSongs = [...textSongs, ...playlistSongsList];

    if (allSongs.length === 0) {
      message.warning('请输入歌曲列表或导入歌单');
      return;
    }
    if (selectedSources.length === 0) {
      message.warning('请至少选择一个音乐源');
      return;
    }

    // 关闭之前的SSE连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setSearchLoading(true);
    setSearchProgress(0);
    setSearchResults([]);
    setHasSearched(false);
    setSelectedRows([]);

    // 显示原始歌曲数量
    const originalCount = allSongs.length;

    try {
      // 使用后台任务API（支持页面切换后继续执行）
      const response = await playlistApi.startBatchSearch({
        songs: allSongs,
        sources: selectedSources,
        concurrency: 5,
        filter_duplicates: filterDuplicates,
      });

      const taskId = response.data.task_id;
      console.log('[后台任务] 启动:', taskId);

      // 轮询任务状态
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await playlistApi.getBatchSearchStatus(taskId);
          const status = statusResponse.data;

          console.log('[后台任务] 状态:', status);

          if (status.status === 'running') {
            setSearchProgress(status.progress?.percent || 0);
          } else if (status.status === 'completed') {
            clearInterval(pollInterval);

            // 获取跳过的歌曲（已下载的重复歌曲）
            const skippedSongs = status.result?.skipped_songs || [];
            const skippedCount = skippedSongs.length;

            // 转换结果格式
            const matches = status.result?.matches || {};
            const results: BatchMatchInfo[] = Object.entries(matches).map(([key, match]: [string, any]) => {
              const current = match.current_match;
              const allMatches = match.all_matches || {};

              // 计算候选数量
              const totalCandidates = Object.values(allMatches).reduce((sum: number, candidates: any) => {
                return sum + (Array.isArray(candidates) ? candidates.length : 0);
              }, 0);

              return {
                query_name: match.query?.name || key,
                query_singer: match.query?.singer || '',
                song_name: current?.song_name || '未找到',
                singers: current?.singers || '-',
                album: current?.album || '-',
                size: current?.file_size || current?.size || '-',
                duration: current?.duration || '-',
                source: current?.source || '-',
                similarity: current?.similarity_score || current?.similarity || 0,
                has_candidates: totalCandidates > 1,
                all_candidates: allMatches,
                _raw_match: match,
              };
            });

            // 过滤逻辑
            let filteredResults = results;

            // 过滤35秒以下试听片段
            if (filterShortTracks) {
              filteredResults = filteredResults.filter(r => {
                if (r.source === '-') return true; // 保留未匹配的
                const duration = r.duration || '';
                // 解析时长格式 (如 "03:45" 或 "00:03:45" 或 "225秒")
                if (duration.includes(':')) {
                  const parts = duration.split(':');
                  let seconds = 0;
                  if (parts.length === 3) {
                    // HH:MM:SS 格式
                    seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
                  } else if (parts.length === 2) {
                    // MM:SS 格式
                    seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);
                  }
                  return seconds >= 35;
                }
                return true;
              });
            }

            setSearchResults(filteredResults);
            setSelectedRows(filteredResults.map((_, idx) => `${filteredResults[idx].query_name}-${idx}`));
            setHasSearched(true);
            setSearchLoading(false);

            const matchedCount = filteredResults.filter(r => r.source !== '-').length;

            // 构建完成消息，包含过滤信息
            let completeMsg = `搜索完成，找到 ${matchedCount} 首匹配歌曲`;
            if (skippedCount > 0) {
              completeMsg += `，已过滤 ${skippedCount} 首已下载歌曲`;
            }
            message.success(completeMsg);

            // 如果有跳过的歌曲，显示详情
            if (skippedCount > 0) {
              console.log('[下载历史过滤] 跳过的歌曲:', skippedSongs);
            }
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            message.error(status.error || '搜索失败');
            setSearchLoading(false);
          }
        } catch (err) {
          console.error('[后台任务] 轮询错误:', err);
        }
      }, 2000); // 每2秒轮询一次

    } catch (err: any) {
      console.error('[批量搜索] 错误:', err);
      message.error(err.message || '批量搜索失败');
      setSearchLoading(false);
    }
  }, [batchText, playlistSongs, selectedSources, matchMode, filterShortTracks, filterDuplicates, message]);

  // ========== 全选/反选/清除 ==========
  const handleSelectAll = useCallback(() => {
    setSelectedRows(searchResults.map((record, idx) => `${record.query_name}-${idx}`));
  }, [searchResults, setSelectedRows]);

  const handleSelectInvert = useCallback(() => {
    const allKeys = searchResults.map((record, idx) => `${record.query_name}-${idx}`);
    const newSelected = allKeys.filter(key => !selectedRows.includes(key));
    setSelectedRows(newSelected);
  }, [searchResults, selectedRows, setSelectedRows]);

  const handleSelectClear = useCallback(() => {
    clearSelectedRows();
  }, [clearSelectedRows]);

  // ========== 候选源切换 ==========
  const handleSwitchCandidate = useCallback((index: number, source: string, candidate: any, candidateIndex: number = 0) => {
    const sourceLabels: Record<string, string> = {
      'QQMusicClient': 'QQ音乐',
      'NeteaseMusicClient': '网易云',
      'KugouMusicClient': '酷狗',
      'KuwoMusicClient': '酷我',
    };

    const updatedResults = [...searchResults];
    const record = updatedResults[index];

    updatedResults[index] = {
      ...record,
      song_name: candidate.song_name,
      singers: candidate.singers,
      album: candidate.album || '-',
      size: candidate.file_size || '-',
      duration: candidate.duration || '-',
      source: candidate.source,
      similarity: candidate.similarity_score || candidate.similarity || 0,
    };

    setSearchResults(updatedResults);
    message.success(`已切换到 ${sourceLabels[source] || source} 的匹配结果`);
  }, [searchResults, setSearchResults, message]);

  // ========== 单曲下载 ==========
  const handleSingleDownload = useCallback(async (record: BatchMatchInfo) => {
    try {
      await downloadApi.startDownload([{
        song_name: record.song_name,
        singers: record.singers,
        album: record.album,
        size: record.size,
        duration: record.duration,
        source: record.source,
      }]);
      message.success(`已提交下载: ${record.song_name}`);
    } catch {
      message.error('下载失败');
    }
  }, [message]);

  // ========== 批量下载 ==========
  const handleBatchDownload = useCallback(async () => {
    if (selectedRows.length === 0) {
      message.warning('请选择要下载的歌曲');
      return;
    }

    // 关闭之前的下载SSE连接
    if (downloadEventSourceRef.current) {
      downloadEventSourceRef.current.close();
      downloadEventSourceRef.current = null;
    }

    setDownloadLoading(true);
    setShowDownloadProgress(true);
    setDownloadProgress(0);
    setDownloadCurrentSong('');
    setDownloadCompleted(0);
    setDownloadTotal(selectedRows.length);

    try {
      const songsToDownload = selectedRows.map(key => {
        const record = searchResults.find(r => key === `${r.query_name}-${searchResults.indexOf(r)}`);
        return record!;
      });

      const streamUrl = downloadApi.streamDownloadUrl(
        songsToDownload.map(song => ({
          song_name: song.song_name,
          singers: song.singers,
          album: song.album,
          size: song.size,
          duration: song.duration,
          source: song.source,
        })),
        downloadDir || undefined
      );

      console.log('[SSE下载] 连接:', streamUrl);

      const eventSource = new EventSource(streamUrl);
      downloadEventSourceRef.current = eventSource;

      eventSource.addEventListener('start', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.log('[SSE下载] 开始:', data);
          setDownloadTotal(data.total || selectedRows.length);
        } catch (err) {
          console.error('[SSE下载] 解析start事件失败:', err);
        }
      });

      eventSource.addEventListener('progress', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.log('[SSE下载] 进度:', data);
          setDownloadProgress(data.percent || 0);
          setDownloadCurrentSong(data.song_name || '');
          setDownloadCompleted(data.completed || 0);
        } catch (err) {
          console.error('[SSE下载] 解析progress事件失败:', err);
        }
      });

      eventSource.addEventListener('complete', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.log('[SSE下载] 完成:', data);

          setDownloadProgress(100);
          setDownloadCompleted(data.completed || 0);
          setDownloadLoading(false);

          eventSource.close();
          downloadEventSourceRef.current = null;

          const failedCount = data.failed || 0;
          if (failedCount > 0) {
            message.warning(`下载完成：成功 ${data.completed} 首，失败 ${failedCount} 首`);
          } else {
            message.success(`下载完成：成功 ${data.completed} 首歌曲`);
          }

          setTimeout(() => {
            setShowDownloadProgress(false);
          }, 3000);
        } catch (err) {
          console.error('[SSE下载] 解析complete事件失败:', err);
          message.error('解析下载结果失败');
          setDownloadLoading(false);
        }
      });

      eventSource.addEventListener('error', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.error('[SSE下载] 错误:', data);
          message.error(data.error || '下载连接失败');
        } catch {
          console.error('[SSE下载] 连接错误');
          message.error('下载连接失败');
        }
        setDownloadLoading(false);
        eventSource.close();
        downloadEventSourceRef.current = null;
      });

      eventSource.onerror = (err) => {
        console.error('[SSE下载] EventSource错误:', err);
        message.error('下载连接中断');
        setDownloadLoading(false);
        eventSource.close();
        downloadEventSourceRef.current = null;
      };

    } catch (err: any) {
      console.error('[批量下载] 错误:', err);
      message.error(err.message || '下载失败');
      setDownloadLoading(false);
      setShowDownloadProgress(false);
    }
  }, [selectedRows, searchResults, downloadDir, message]);

  return (
    <div className="page">
      <Title level={2} className="page-title">批量下载</Title>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 上方：文本输入 + 歌单导入（并列） */}
        <Row gutter={16}>
          {/* 文本输入板块 */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <FileTextOutlined />
                  <Text strong>文本输入</Text>
                </Space>
              }
              extra={
                batchText && (
                  <Button
                    size="small"
                    icon={<ClearOutlined />}
                    onClick={() => {
                      setBatchText('');
                      setParsedCount(0);
                    }}
                  >
                    清空
                  </Button>
                )
              }
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}>
                    每行一首歌曲，格式：歌名 - 歌手
                  </Text>
                  <BatchTextInput
                    value={batchText}
                    onChange={(value) => {
                      setBatchText(value);
                      setParsedCount(parseLineCount(value));
                    }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text type="secondary">
                    已识别 <Text strong style={{ color: parsedCount > 0 ? '#52c41a' : undefined }}>
                      {parsedCount}
                    </Text> 首歌曲
                  </Text>
                </div>
              </Space>
            </Card>
          </Col>

          {/* 歌单导入板块 */}
          <Col xs={24} lg={12}>
            <PlaylistImportSection onParsed={handlePlaylistParsed} />
          </Col>
        </Row>

        {/* 下方：匹配设置板块 */}
        <Card title={<Text strong><DownloadOutlined /> 匹配设置</Text>}>
          <MatchSettingsPanel
            downloadDir={downloadDir}
            onDownloadDirChange={setDownloadDir}
            filterShortTracks={filterShortTracks}
            onFilterShortTracksChange={setFilterShortTracks}
            filterDuplicates={filterDuplicates}
            onFilterDuplicatesChange={setFilterDuplicates}
            onBatchSearch={handleBatchSearch}
            searchLoading={searchLoading}
            searchDisabled={totalSongCount === 0 || selectedSources.length === 0}
            parsedCount={totalSongCount}
          />
        </Card>

        {/* 搜索进度 */}
        {searchLoading && (
          <Card title="搜索进度">
            <Progress
              percent={searchProgress}
              status="active"
              strokeWidth={12}
              style={{ marginBottom: 8 }}
            />
            <Text type="secondary">正在从多个音乐源搜索匹配歌曲...</Text>
          </Card>
        )}

        {/* 搜索结果 */}
        {hasSearched && (
          <Card
            title={
              <Space>
                <CheckSquareOutlined />
                <Text strong>搜索结果 ({searchResults.length} 首)</Text>
              </Space>
            }
            extra={
              <Space>
                <Text type="secondary">
                  已选 <Text strong>{selectedRows.length}</Text> / {searchResults.length}
                </Text>
              </Space>
            }
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* 操作按钮组 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                <Space wrap>
                  <Text strong>批量操作：</Text>
                  <Button
                    size="middle"
                    onClick={handleSelectAll}
                    icon={<CheckSquareOutlined />}
                  >
                    全选
                  </Button>
                  <Button size="middle" onClick={handleSelectInvert}>
                    反选
                  </Button>
                  <Button
                    size="middle"
                    onClick={handleSelectClear}
                    icon={<BorderOutlined />}
                  >
                    清除选择
                  </Button>
                </Space>
                <Button
                  type="primary"
                  size="large"
                  icon={<DownloadOutlined />}
                  loading={downloadLoading}
                  onClick={handleBatchDownload}
                  disabled={selectedRows.length === 0}
                >
                  下载选中歌曲 ({selectedRows.length})
                </Button>
              </div>

              {/* 统计信息 */}
              <Alert
                message={
                  <Space size="large">
                    <span>
                      匹配成功：<Text strong style={{ color: '#52c41a' }}>
                        {searchResults.filter(r => r.source !== '-').length}
                      </Text> 首
                    </span>
                    <span>
                      未匹配：<Text strong style={{ color: '#ff4d4f' }}>
                        {searchResults.filter(r => r.source === '-').length}
                      </Text> 首
                    </span>
                    <span>
                      高相似度(≥80%)：<Text strong style={{ color: '#52c41a' }}>
                        {searchResults.filter(r => r.similarity >= 0.8).length}
                      </Text> 首
                    </span>
                  </Space>
                }
                type="info"
                showIcon={false}
                style={{ backgroundColor: '#f6ffed', borderColor: '#b7eb8f' }}
              />

              {/* 结果表格 */}
              <BatchResultsTable
                data={searchResults}
                onDownload={handleSingleDownload}
                onSwitchCandidate={handleSwitchCandidate}
                rowSelection={{
                  selectedRowKeys: selectedRows,
                  onChange: (keys) => setSelectedRows(keys),
                }}
              />
            </Space>
          </Card>
        )}

        {/* 下载进度 */}
        {showDownloadProgress && (
          <Card
            title={
              <Space>
                <DownloadOutlined spin={downloadLoading} />
                <Text strong>正在下载歌曲...</Text>
              </Space>
            }
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Progress
                percent={downloadProgress}
                status={downloadLoading ? 'active' : 'success'}
                strokeWidth={16}
                format={(percent) => (
                  <Space>
                    <span style={{ fontSize: 16, fontWeight: 'bold' }}>{percent}%</span>
                  </Space>
                )}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                <Space size="large">
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>下载进度</Text>
                    <br />
                    <Text strong style={{ fontSize: 16, color: '#1890ff' }}>
                      {downloadCompleted} / {downloadTotal}
                    </Text>
                  </div>
                  {downloadCurrentSong && (
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>当前歌曲</Text>
                      <br />
                      <Text strong style={{ fontSize: 14 }} ellipsis={{ tooltip: downloadCurrentSong }}>
                        {downloadCurrentSong}
                      </Text>
                    </div>
                  )}
                </Space>
                {!downloadLoading && downloadProgress === 100 && (
                  <Tag color="success" style={{ fontSize: 14, padding: '4px 12px' }}>
                    下载完成
                  </Tag>
                )}
              </div>
            </Space>
          </Card>
        )}
      </Space>
    </div>
  );
}

export default BatchDownloadPage;