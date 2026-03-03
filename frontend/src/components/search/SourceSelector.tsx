/**
 * 音乐源选择器组件
 *
 * 使用Checkbox.Group多选音乐源，支持全选/取消全选
 * 音乐源配置从后端 API 动态获取
 */
import { Checkbox, Col, Row, Space, Typography, Button, Spin } from 'antd';
import { useUIStore } from '../../stores/useUIStore';

const { Text } = Typography;

function SourceSelector() {
  const { selectedSources, setSelectedSources, availableSources, sourcesLoaded, fetchSources } = useUIStore();

  // 如果音乐源未加载，显示加载状态
  if (!sourcesLoaded) {
    // 触发加载
    fetchSources();
    return (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Text strong>选择音乐源:</Text>
        <Spin size="small" />
      </Space>
    );
  }

  // 全选
  const handleSelectAll = () => {
    setSelectedSources(availableSources.map(s => s.value));
  };

  // 取消全选
  const handleDeselectAll = () => {
    setSelectedSources([]);
  };

  // 选中常用源（网易云、QQ音乐）
  const handleSelectCommon = () => {
    setSelectedSources(['NeteaseMusicClient', 'QQMusicClient']);
  };

  const allSelected = selectedSources.length === availableSources.length;
  const noneSelected = selectedSources.length === 0;

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text strong>选择音乐源:</Text>
        <Space size="small">
          {!allSelected && (
            <Button type="link" size="small" onClick={handleSelectAll}>
              全选
            </Button>
          )}
          {!noneSelected && (
            <Button type="link" size="small" onClick={handleDeselectAll}>
              清空
            </Button>
          )}
          <Button type="link" size="small" onClick={handleSelectCommon}>
            常用源
          </Button>
        </Space>
      </div>

      <Checkbox.Group
        value={selectedSources}
        onChange={(checkedValues) => setSelectedSources(checkedValues as string[])}
      >
        <Row gutter={[16, 16]}>
          {availableSources.map((source) => (
            <Col span={6} key={source.value}>
              <Checkbox value={source.value}>
                {source.label}
              </Checkbox>
            </Col>
          ))}
        </Row>
      </Checkbox.Group>

      {noneSelected && (
        <Text type="warning" style={{ fontSize: 12 }}>
          ⚠️ 请至少选择一个音乐源
        </Text>
      )}

      {selectedSources.length > 0 && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          已选择 {selectedSources.length} 个音乐源
        </Text>
      )}
    </Space>
  );
}

export default SourceSelector;