/**
 * 音乐源选择组件
 *
 * 统一的音乐源选择器，供批量下载和歌单导入页面使用
 */
import { Space, Typography, Checkbox, Button, message } from 'antd';
import { useUIStore } from '../../stores/useUIStore';

const { Text } = Typography;

// 音乐源配置
export const MUSIC_SOURCES = [
  { value: 'NeteaseMusicClient', label: '网易云' },
  { value: 'QQMusicClient', label: 'QQ音乐' },
  { value: 'KugouMusicClient', label: '酷狗' },
  { value: 'KuwoMusicClient', label: '酷我' },
  { value: 'MiguMusicClient', label: '咪咕' },
] as const;

interface SourceSelectorProps {
  /** 是否显示快捷模式按钮 */
  showQuickMode?: boolean;
  /** 标题文本 */
  label?: string;
  /** 额外样式 */
  style?: React.CSSProperties;
}

function SourceSelector({
  showQuickMode = true,
  label = '音乐源：',
  style,
}: SourceSelectorProps) {
  const { selectedSources, setSelectedSources } = useUIStore();

  const handleQuickMode = () => {
    setSelectedSources(['NeteaseMusicClient', 'QQMusicClient']);
    message.info('已切换到快速模式（网易云+QQ音乐），搜索更快');
  };

  const handleFullMode = () => {
    setSelectedSources(['NeteaseMusicClient', 'QQMusicClient', 'KugouMusicClient', 'KuwoMusicClient']);
    message.info('已切换到完整模式（4个源），匹配更全面但较慢');
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 16, ...style }}>
      <Text strong>{label}</Text>
      <Checkbox.Group
        value={selectedSources}
        onChange={(sources) => setSelectedSources(sources as string[])}
      >
        {MUSIC_SOURCES.map((source) => (
          <Checkbox key={source.value} value={source.value}>
            {source.label}
          </Checkbox>
        ))}
      </Checkbox.Group>
      {showQuickMode && (
        <Space size={4}>
          <Button
            type="link"
            size="small"
            onClick={handleQuickMode}
            style={{ padding: '0 4px', fontSize: 12 }}
          >
            快速
          </Button>
          <Button
            type="link"
            size="small"
            onClick={handleFullMode}
            style={{ padding: '0 4px', fontSize: 12 }}
          >
            完整
          </Button>
        </Space>
      )}
    </div>
  );
}

export default SourceSelector;