/**
 * 匹配设置组件
 *
 * 可折叠的匹配设置面板
 */
import { Collapse, Space, Typography, Radio, Alert } from 'antd';
import { SettingFilled } from '@ant-design/icons';
import { useUIStore } from '../../stores/useUIStore';
import { MATCH_MODES } from '../../types';

const { Text } = Typography;

function MatchSettings() {
  const { matchMode, setMatchMode } = useUIStore();

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'strict': return 'error';
      case 'standard': return 'warning';
      case 'loose': return 'success';
      default: return 'default';
    }
  };

  const items = [
    {
      key: '1',
      label: (
        <Space>
          <Text strong>相似度阈值设置</Text>
          <Text type="secondary">（当前：{MATCH_MODES[matchMode].label}）</Text>
        </Space>
      ),
      children: (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            message="相似度阈值决定匹配的严格程度"
            description="严格模式只接受高相似度匹配，宽松模式会接受更多可能的匹配结果"
            type="info"
            showIcon
            style={{ backgroundColor: '#e6f7ff', borderColor: '#91d5ff' }}
          />

          <div>
            <Text strong style={{ display: 'block', marginBottom: 16 }}>
              选择匹配模式
            </Text>
            <Radio.Group
              value={matchMode}
              onChange={(e) => setMatchMode(e.target.value)}
              optionType="button"
              buttonStyle="solid"
              size="large"
              style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}
            >
              {Object.entries(MATCH_MODES).map(([key, { label, value }]) => (
                <Radio.Button
                  key={key}
                  value={key}
                  style={{
                    flex: 1,
                    minWidth: 120,
                    textAlign: 'center',
                    height: 'auto',
                    padding: '8px 16px',
                  }}
                >
                  <Space direction="vertical" size={4}>
                    <Text strong>{label}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {(value * 100).toFixed(0)}%
                    </Text>
                  </Space>
                </Radio.Button>
              ))}
            </Radio.Group>
          </div>

          <div>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>
              当前模式说明
            </Text>
            <Alert
              message={MATCH_MODES[matchMode].label}
              description={MATCH_MODES[matchMode].description}
              type={getModeColor(matchMode) as any}
              showIcon
            />
          </div>
        </Space>
      ),
    },
  ];

  return (
    <Collapse
      items={items}
      defaultActiveKey={[]}
      bordered={false}
      expandIcon={({ isActive }) => (
        <SettingFilled
          rotate={isActive ? 90 : 0}
          style={{ color: '#1890ff' }}
        />
      )}
      style={{ backgroundColor: 'transparent' }}
    />
  );
}

export default MatchSettings;
