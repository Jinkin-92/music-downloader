/**
 * 匹配设置面板组件
 *
 * 整合匹配模式、音乐源选择、下载目录、过滤选项
 */
import { useState, useEffect } from 'react';
import {
  Space,
  Typography,
  Radio,
  Checkbox,
  Input,
  Select,
  Button,
  Divider,
  Row,
  Col,
} from 'antd';
import { SearchOutlined, FolderOutlined, SettingFilled } from '@ant-design/icons';
import { useUIStore } from '../../stores/useUIStore';

const { Text } = Typography;

// 匹配模式配置
const MATCH_MODE_OPTIONS = [
  { key: 'strict', label: '精确', value: 0.8, description: '80%相似度' },
  { key: 'standard', label: '标准', value: 0.6, description: '60%相似度' },
  { key: 'loose', label: '宽松', value: 0.4, description: '40%相似度' },
];

// 音乐源配置
const MUSIC_SOURCE_OPTIONS = [
  { value: 'NeteaseMusicClient', label: '网易云' },
  { value: 'QQMusicClient', label: 'QQ音乐' },
  { value: 'KugouMusicClient', label: '酷狗' },
  { value: 'KuwoMusicClient', label: '酷我' },
  { value: 'MiguMusicClient', label: '咪咕' },
];

// 快捷下载目录选项
const QUICK_DOWNLOAD_DIRS = [
  { label: '桌面', value: '桌面' },
  { label: '文档', value: '文档' },
  { label: '下载', value: '下载' },
  { label: '音乐', value: '音乐' },
  { label: '视频', value: '视频' },
  { label: '图片', value: '图片' },
];

interface MatchSettingsPanelProps {
  /** 下载目录 */
  downloadDir: string;
  /** 下载目录变化回调 */
  onDownloadDirChange: (dir: string) => void;
  /** 过滤试听片段 */
  filterShortTracks: boolean;
  /** 过滤试听片段变化回调 */
  onFilterShortTracksChange: (filter: boolean) => void;
  /** 过滤重复歌曲 */
  filterDuplicates: boolean;
  /** 过滤重复歌曲变化回调 */
  onFilterDuplicatesChange: (filter: boolean) => void;
  /** 批量搜索按钮点击回调 */
  onBatchSearch: () => void;
  /** 搜索按钮是否加载中 */
  searchLoading?: boolean;
  /** 搜索按钮是否禁用 */
  searchDisabled?: boolean;
  /** 已识别的歌曲数量 */
  parsedCount?: number;
}

function MatchSettingsPanel({
  downloadDir,
  onDownloadDirChange,
  filterShortTracks,
  onFilterShortTracksChange,
  filterDuplicates,
  onFilterDuplicatesChange,
  onBatchSearch,
  searchLoading = false,
  searchDisabled = false,
  parsedCount = 0,
}: MatchSettingsPanelProps) {
  const { matchMode, setMatchMode, selectedSources, setSelectedSources } = useUIStore();

  // 历史下载目录（从localStorage读取）
  const [historyDirs, setHistoryDirs] = useState<string[]>([]);

  // 组件挂载时读取历史目录
  useEffect(() => {
    const saved = localStorage.getItem('downloadHistoryDirs');
    if (saved) {
      try {
        setHistoryDirs(JSON.parse(saved));
      } catch {
        setHistoryDirs([]);
      }
    }
  }, []);

  // 保存目录到历史记录
  const saveToHistory = (dir: string) => {
    if (!dir || dir.trim() === '') return;
    const newHistory = [dir, ...historyDirs.filter(d => d !== dir)].slice(0, 10);
    setHistoryDirs(newHistory);
    localStorage.setItem('downloadHistoryDirs', JSON.stringify(newHistory));
  };

  // 处理目录选择
  const handleDirSelect = (value: string) => {
    if (value === '__custom__') {
      // 用户选择自定义，不做任何操作
      return;
    }
    onDownloadDirChange(value);
  };

  // 处理目录输入框失焦
  const handleDirBlur = () => {
    if (downloadDir) {
      saveToHistory(downloadDir);
    }
  };

  return (
    <div style={{ padding: '16px 0' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 匹配模式选择 */}
        <div>
          <Text strong style={{ display: 'block', marginBottom: 12 }}>
            <SettingFilled style={{ marginRight: 8, color: '#1890ff' }} />
            匹配模式
          </Text>
          <Radio.Group
            value={matchMode}
            onChange={(e) => setMatchMode(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            size="middle"
          >
            {MATCH_MODE_OPTIONS.map((option) => (
              <Radio.Button key={option.key} value={option.key}>
                <Space size={4}>
                  <Text strong>{option.label}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    ({(option.value * 100).toFixed(0)}%)
                  </Text>
                </Space>
              </Radio.Button>
            ))}
          </Radio.Group>
        </div>

        <Divider style={{ margin: '8px 0' }} />

        {/* 匹配源选择 */}
        <div>
          <Text strong style={{ display: 'block', marginBottom: 12 }}>
            匹配源
          </Text>
          <Checkbox.Group
            value={selectedSources}
            onChange={(sources) => setSelectedSources(sources as string[])}
          >
            <Row gutter={[16, 8]}>
              {MUSIC_SOURCE_OPTIONS.map((source) => (
                <Col key={source.value}>
                  <Checkbox value={source.value}>{source.label}</Checkbox>
                </Col>
              ))}
            </Row>
          </Checkbox.Group>
        </div>

        <Divider style={{ margin: '8px 0' }} />

        {/* 下载目录 */}
        <div>
          <Text strong style={{ display: 'block', marginBottom: 12 }}>
            <FolderOutlined style={{ marginRight: 8 }} />
            下载目录
          </Text>
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="输入完整路径或使用快捷选择"
              value={downloadDir}
              onChange={(e) => onDownloadDirChange(e.target.value)}
              onBlur={handleDirBlur}
              style={{ flex: 1 }}
            />
            <Select
              placeholder="快捷选择"
              value={null}
              onChange={handleDirSelect}
              style={{ width: 120 }}
              options={[
                ...QUICK_DOWNLOAD_DIRS,
                { label: '历史目录', value: '__history__' },
              ]}
              dropdownRender={(menu) => (
                <div>
                  {menu}
                  {historyDirs.length > 0 && (
                    <>
                      <div style={{ padding: '8px 12px', color: '#999', fontSize: 12 }}>
                        历史目录
                      </div>
                      {historyDirs.map((dir) => (
                        <div
                          key={dir}
                          style={{
                            padding: '8px 12px',
                            cursor: 'pointer',
                            transition: 'background 0.2s',
                          }}
                          onClick={() => handleDirSelect(dir)}
                          onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f5'}
                          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        >
                          <Text ellipsis={{ tooltip: dir }} style={{ maxWidth: 200 }}>
                            {dir}
                          </Text>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            />
          </Space.Compact>
          <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
            留空使用默认目录：musicdl_outputs/
          </Text>
        </div>

        <Divider style={{ margin: '8px 0' }} />

        {/* 过滤选项 */}
        <div>
          <Text strong style={{ display: 'block', marginBottom: 12 }}>
            过滤选项
          </Text>
          <Space direction="vertical" size={8}>
            <Checkbox
              checked={filterShortTracks}
              onChange={(e) => onFilterShortTracksChange(e.target.checked)}
            >
              过滤35秒以下试听片段
            </Checkbox>
            <Checkbox
              checked={filterDuplicates}
              onChange={(e) => onFilterDuplicatesChange(e.target.checked)}
            >
              过滤下载历史中重复歌曲
            </Checkbox>
          </Space>
        </div>

        <Divider style={{ margin: '8px 0' }} />

        {/* 批量搜索按钮 */}
        <div style={{ textAlign: 'center', paddingTop: 8 }}>
          <Button
            type="primary"
            size="large"
            icon={<SearchOutlined />}
            onClick={onBatchSearch}
            loading={searchLoading}
            disabled={searchDisabled}
            style={{ minWidth: 200 }}
          >
            批量搜索 {parsedCount > 0 && `(${parsedCount}首)`}
          </Button>
        </div>
      </Space>
    </div>
  );
}

export default MatchSettingsPanel;