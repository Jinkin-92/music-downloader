/**
 * 批量下载页面
 *
 * 支持批量文本输入、智能匹配、实时进度显示
 */
import { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import {
  Card,
  Space,
  Typography,
  Button,
  Progress,
  Row,
  Col,
  Table,
  Dropdown,
  Alert,
  Tag,
  Tooltip,
  Input,
  Select,
} from 'antd';
import { SearchOutlined, DownloadOutlined, CheckSquareOutlined, BorderOutlined, ClearOutlined, SwapOutlined, FileTextOutlined, SettingFilled } from '@ant-design/icons';
import { App } from 'antd';
import { useUIStore } from '../stores/useUIStore';
import { useLocalStorage } from '../hooks/useLocalStorage';
import BatchTextInput from '../components/batch/BatchTextInput';
import MatchSettings from '../components/batch/MatchSettings';
import { playlistApi, downloadApi } from '../services/api';
import { parseLineCount } from '../utils/format';
import { BatchMatchInfo, MATCH_MODES } from '../types';

const { Title, Text } = Typography;

function BatchDownloadPage() {
  const { message } = App.useApp();
  const { selectedSources, matchMode } = useUIStore();

  // Persistent state (survives page navigation)
  const [batchText, setBatchText] = useLocalStorage('batch-download-text', '');
  const [searchResults, setSearchResults] = useLocalStorage<BatchMatchInfo[]>('batch-download-results', []);
  const [hasSearched, setHasSearched] = useLocalStorage('batch-download-searched', false);
  const [selectedRows, setSelectedRows, clearSelectedRows] = useLocalStorage<string[]>('batch-download-selected', []);

  // Temporary state (not persisted)
  const [parsedCount, setParsedCount] = useState(0);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchProgress, setSearchProgress] = useState(0);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [downloadDir, setDownloadDir] = useState('');  // 下载目录路径

  // 下载进度状态
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadCurrentSong, setDownloadCurrentSong] = useState('');
  const [downloadCompleted, setDownloadCompleted] = useState(0);
  const [downloadTotal, setDownloadTotal] = useState(0);
  const [showDownloadProgress, setShowDownloadProgress] = useState(false);

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

  const handleBatchSearch = useCallback(async () => {
    if (!batchText.trim()) {
      message.warning('请输入批量歌曲列表');
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

    try {
      const lines = batchText.split('\n').filter(line => line.trim());
      const songs = lines.map(line => {
        const parts = line.split('-');
        return { name: parts[0]?.trim() || '', artist: parts[1]?.trim() || '', album: '' };
      });

      // 构建SSE URL
      const songsJson = JSON.stringify(songs);
      const sources = selectedSources.join(',');
      const threshold = MATCH_MODES[matchMode].value;
      const sseUrl = playlistApi.batchSearchStreamUrl(songsJson, sources, 5, threshold);

      console.log('[SSE] 连接:', sseUrl);

      // 创建SSE连接
      const eventSource = new EventSource(sseUrl);
      eventSourceRef.current = eventSource;


      eventSource.addEventListener('start', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.log('[SSE] 开始:', data);
        } catch (err) {
          console.error('[SSE] 解析start事件失败:', err);
        }
      });

      eventSource.addEventListener('progress', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.log('[SSE] 进度:', data);
          setSearchProgress(data.percent || 0);
        } catch (err) {
          console.error('[SSE] 解析progress事件失败:', err);
        }
      });

      eventSource.addEventListener('complete', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.log('[SSE] 完成:', data);

          // 转换结果格式，保存完整的候选数据
          const matches = data.matches || {};
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
              _raw_match: match, // 保存原始数据用于切换
            };
          });

          // 不再根据相似度过滤，显示所有结果
          setSearchResults(results);
          setSelectedRows(results.map((_, idx) => `${results[idx].query_name}-${idx}`));
          setHasSearched(true);
          setSearchLoading(false);

          eventSource.close();
          eventSourceRef.current = null;

          const matchedCount = results.filter(r => r.source !== '-').length;
          if (matchedCount > 0) {
            message.success(`搜索完成，找到 ${matchedCount} 首匹配歌曲`);
          } else {
            message.warning('未找到匹配的歌曲');
          }
        } catch (err) {
          console.error('[SSE] 解析complete事件失败:', err);
          message.error('解析搜索结果失败');
          setSearchLoading(false);
        }
      });

      eventSource.addEventListener('error', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          console.error('[SSE] 错误:', data);
          message.error(data.error || '搜索连接失败');
        } catch {
          console.error('[SSE] 连接错误');
          message.error('搜索连接失败');
        }
        setSearchLoading(false);
        eventSource.close();
        eventSourceRef.current = null;
      });

      eventSource.onerror = (err) => {
        console.error('[SSE] EventSource错误:', err);
        message.error('搜索连接中断');
        setSearchLoading(false);
        eventSource.close();
        eventSourceRef.current = null;
      };

    } catch (err: any) {
      console.error('[批量搜索] 错误:', err);
      message.error(err.message || '批量搜索失败');
      setSearchLoading(false);
    }
  }, [batchText, selectedSources, matchMode, message]);

  // 全选/反选/清除选择
  const handleSelectAll = useCallback(() => {
    setSelectedRows(searchResults.map((record, idx) => `${record.query_name}-${idx}`));
  }, [searchResults]);

  const handleSelectInvert = useCallback(() => {
    const allKeys = searchResults.map((record, idx) => `${record.query_name}-${idx}`);
    const newSelected = allKeys.filter(key => !selectedRows.includes(key));
    setSelectedRows(newSelected);
  }, [searchResults, selectedRows]);

  const handleSelectClear = useCallback(() => {
    clearSelectedRows();
  }, [clearSelectedRows]);

  // 候选源切换（支持源内多候选切换）
  const handleSwitchCandidate = useCallback((index: number, source: string, candidate: any, candidateIndex: number = 0) => {
    const updatedResults = [...searchResults];
    const record = updatedResults[index];

    // 更新为选中的候选
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

    const candidateCount = record.all_candidates?.[source]?.length || 1;
    const candidateLabel = candidateCount > 1 ? ` (#${candidateIndex + 1})` : '';
    setSearchResults(updatedResults);
    message.success(`已切换到 ${sourceLabels[source] || source}${candidateLabel} 的匹配结果`);
  }, [searchResults, message]);

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

    // 重置下载进度状态
    setDownloadLoading(true);
    setShowDownloadProgress(true);
    setDownloadProgress(0);
    setDownloadCurrentSong('');
    setDownloadCompleted(0);
    setDownloadTotal(selectedRows.length);

    try {
      // 解析string rowKey到实际记录
      const songsToDownload = selectedRows.map(key => {
        const record = searchResults.find(r => key === `${r.query_name}-${searchResults.indexOf(r)}`);
        return record!;
      });

      // 构建SSE下载URL
      const streamUrl = downloadApi.streamDownloadUrl(
        songsToDownload.map(song => ({
          song_name: song.song_name,
          singers: song.singers,
          album: song.album,
          size: song.size,
          duration: song.duration,
          source: song.source,
        })),
        downloadDir || undefined  // 传递下载目录
      );

      console.log('[SSE下载] 连接:', streamUrl);

      // 创建SSE连接
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

          // 3秒后隐藏进度条
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
  }, [selectedRows, searchResults, message]);

  const sourceLabels: Record<string, string> = {
    'QQMusicClient': 'QQ音乐',
    'NeteaseMusicClient': '网易云',
    'KugouMusicClient': '酷狗',
    'KuwoMusicClient': '酷我',
  };

  // 获取相似度标签颜色
  const getSimilarityTag = (similarity: number) => {
    if (similarity >= 0.8) return { color: 'success', text: `${(similarity * 100).toFixed(0)}%` };
    if (similarity >= 0.6) return { color: 'warning', text: `${(similarity * 100).toFixed(0)}%` };
    return { color: 'error', text: `${(similarity * 100).toFixed(0)}%` };
  };

  const columns = useMemo(() => [
    {
      title: '查询',
      key: 'query',
      width: 180,
      render: (_: any, record: BatchMatchInfo) => (
        <div>
          <Text strong style={{ fontSize: 14 }}>{record.query_name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{record.query_singer || '-'}</Text>
        </div>
      ),
    },
    {
      title: '匹配结果',
      key: 'result',
      width: 320,
      render: (_: any, record: BatchMatchInfo, index: number) => {
        const hasCandidates = record.has_candidates && record.all_candidates;
        const candidateSources = hasCandidates ? Object.keys(record.all_candidates || {}) : [];
        const similarityTag = getSimilarityTag(record.similarity);

        // 如果有多个候选源，显示二级下拉菜单
        if (hasCandidates && candidateSources.length > 1) {
          // 构建嵌套菜单：第一级选择源，第二级选择该源的具体候选
          const _menuItems = candidateSources.map((source: string) => {
            const candidates = record.all_candidates![source] || [];
            return {
              key: source,
              label: `${sourceLabels[source] || source}`,
              children: candidates.map((candidate: any, idx: number) => ({
                key: `${source}-${idx}`,
                label: candidate.song_name || `候选 #${idx + 1}`,
                onClick: () => handleSwitchCandidate(index, source, candidate, idx),
              })),
            };
          });
          void _menuItems; // avoid unused warning

          return (
            <Space direction="vertical" size={4}>
              <Space>
                <Text strong style={{ fontSize: 14 }}>{record.song_name}</Text>
                {record.source !== '-' && (
                  <Dropdown
                    trigger={['click']}
                    dropdownRender={() => (
                      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px 0 rgba(0, 0, 0, 0.12), 0 9px 28px 8px 0 rgba(0, 0, 0, 0.05)' }}>
                        {candidateSources.map((source: string) => {
                          const candidates = record.all_candidates![source] || [];
                          return (
                            <div key={source}>
                              <div style={{ padding: '8px 12px', fontWeight: 'bold', color: '#1890ff' }}>
                                {sourceLabels[source] || source}
                              </div>
                              {candidates.map((candidate: any, idx: number) => (
                                <div
                                  key={`${source}-${idx}`}
                                  style={{
                                    padding: '8px 12px 8px 24px',
                                    cursor: 'pointer',
                                    transition: 'background 0.2s',
                                  }}
                                  onClick={() => handleSwitchCandidate(index, source, candidate, idx)}
                                  onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f5'}
                                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                >
                                  {candidate.song_name || `候选 #${idx + 1}`}
                                </div>
                              ))}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  >
                    <Button
                      type="text"
                      size="small"
                      icon={<SwapOutlined />}
                      style={{ padding: '0 4px', fontSize: 12 }}
                    >
                      切换
                    </Button>
                  </Dropdown>
                )}
              </Space>
              <Text type="secondary" style={{ fontSize: 12 }}>{record.singers}</Text>
            </Space>
          );
        }

        return (
          <Space direction="vertical" size={4}>
            <Space>
              <Text strong style={{ fontSize: 14 }}>{record.song_name}</Text>
              {record.source !== '-' && (
                <Tooltip
                  title={
                    record.name_similarity !== undefined ? (
                      <div style={{ fontSize: 12 }}>
                        <div>歌名: {(record.name_similarity * 100).toFixed(0)}%</div>
                        <div>歌手: {((record.singer_similarity ?? 0) * 100).toFixed(0)}%</div>
                        <div>专辑: {((record.album_similarity ?? 0) * 100).toFixed(0)}%</div>
                        <div style={{ marginTop: 4, paddingTop: 4, borderTop: '1px solid #eee' }}>
                          <strong>总计: {(record.similarity * 100).toFixed(0)}%</strong>
                        </div>
                      </div>
                    ) : similarityTag.text
                  }
                >
                  <Tag color={similarityTag.color} style={{ fontSize: 11, cursor: 'help' }}>
                    {similarityTag.text}
                  </Tag>
                </Tooltip>
              )}
            </Space>
            <Text type="secondary" style={{ fontSize: 12 }}>{record.singers}</Text>
          </Space>
        );
      },
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      render: (source: string) => {
        const sourceLabel = sourceLabels[source] || source;
        if (source === '-') {
          return <Text type="secondary" style={{ fontSize: 12 }}>未匹配</Text>;
        }
        return <Tag color="blue" style={{ fontSize: 12 }}>{sourceLabel}</Tag>;
      },
    },
    {
      title: '专辑',
      dataIndex: 'album',
      key: 'album',
      width: 150,
      ellipsis: true,
      render: (album: string) => (
        <Text type="secondary" style={{ fontSize: 12 }} ellipsis={{ tooltip: album }}>
          {album || '-'}
        </Text>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 80,
      render: (size: string) => (
        <Text type="secondary" style={{ fontSize: 12 }}>{size || '-'}</Text>
      ),
    },
    {
      title: '时长',
      dataIndex: 'duration',
      key: 'duration',
      width: 80,
      render: (duration: string) => (
        <Text type="secondary" style={{ fontSize: 12 }}>{duration || '-'}</Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right' as const,
      render: (_: any, record: BatchMatchInfo) => (
        <Button
          type="primary"
          size="small"
          icon={<DownloadOutlined />}
          disabled={record.source === '-'}
          onClick={async () => {
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
          }}
        >
          下载
        </Button>
      ),
    },
  ], [handleSwitchCandidate, sourceLabels, message]);

  return (
    <div className="page">
      <Title level={2} className="page-title">批量下载</Title>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 歌曲输入卡片 */}
        <Card
          title={
            <Space>
              <FileTextOutlined />
              <Text strong>1. 输入歌曲列表</Text>
            </Space>
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
              <Space>
                <Text type="secondary">
                  已识别 <Text strong style={{ color: parsedCount > 0 ? '#52c41a' : undefined }}>
                    {parsedCount}
                  </Text> 首歌曲
                </Text>
              </Space>
              {batchText && (
                <Button
                  size="small"
                  icon={<ClearOutlined />}
                  onClick={() => {
                    setBatchText('');
                    setParsedCount(0);
                  }}
                >
                  清空输入
                </Button>
              )}
            </div>
          </Space>
        </Card>

        {/* 匹配设置卡片 */}
        <Card
          title={
            <Space>
              <SettingFilled />
              <Text strong>2. 匹配设置</Text>
            </Space>
          }
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <MatchSettings />

            {/* 下载路径选择 */}
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                下载目录（可选）：
              </Text>
              <Space.Compact style={{ width: '420px' }}>
                <Input
                  placeholder="下载目录（支持完整路径或快捷名称）"
                  value={downloadDir}
                  onChange={(e) => setDownloadDir(e.target.value)}
                  style={{ width: '280px' }}
                />
                <Select
                  placeholder="快捷选择"
                  value={null}
                  onChange={(value) => setDownloadDir(value || '')}
                  style={{ width: '140px' }}
                  options={[
                    { label: '桌面', value: '桌面' },
                    { label: '文档', value: '文档' },
                    { label: '下载', value: '下载' },
                    { label: '音乐', value: '音乐' },
                    { label: '视频', value: '视频' },
                    { label: '图片', value: '图片' },
                  ]}
                />
              </Space.Compact>
              <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                留空使用默认目录，可输入完整路径或使用快捷选择
              </Text>
            </div>
          </Space>
        </Card>

        {/* 搜索操作卡片 */}
        <Card
          title={
            <Space>
              <SearchOutlined />
              <Text strong>3. 开始批量搜索</Text>
            </Space>
          }
        >
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Row gutter={[16, 16]} align="middle">
              <Col>
                <Button
                  type="primary"
                  size="large"
                  icon={<SearchOutlined />}
                  onClick={handleBatchSearch}
                  loading={searchLoading}
                  disabled={!batchText || parsedCount === 0}
                >
                  开始批量搜索
                </Button>
              </Col>
              <Col>
                {searchLoading && (
                  <Space>
                    <Progress
                      type="circle"
                      percent={searchProgress}
                      width={50}
                      status="active"
                    />
                    <Text type="secondary">搜索中...</Text>
                  </Space>
                )}
              </Col>
            </Row>
            {parsedCount > 0 && !searchLoading && (
              <Alert
                message={`即将搜索 ${parsedCount} 首歌曲，预计耗时 ${Math.ceil(parsedCount * 0.8)} 秒`}
                type="info"
                showIcon
                style={{ marginTop: 8 }}
              />
            )}
          </Space>
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
                <Text strong>4. 搜索结果 ({searchResults.length} 首)</Text>
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
              <Table
                columns={columns}
                dataSource={searchResults}
                rowKey={(record, index) => `${record.query_name}-${index ?? 0}`}
                pagination={false}
                size="middle"
                scroll={{ x: 1200 }}
                rowSelection={{
                  selectedRowKeys: selectedRows,
                  onChange: (keys) => setSelectedRows(keys as string[]),
                  columnWidth: 50,
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
                  <Alert
                    message="下载完成！"
                    type="success"
                    showIcon
                  />
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
