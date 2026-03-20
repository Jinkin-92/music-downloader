/**
 * App根组件
 *
 * 定义路由和布局
 */
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Layout, Typography, Menu } from 'antd';
import { useUIStore } from './stores/useUIStore';
import BatchDownloadPage from './pages/BatchDownloadPage';
import DownloadHistoryPage from './pages/DownloadHistoryPage';

const { Title, Text } = Typography;

function App() {
  const navigate = useNavigate();
  const selectedSources = useUIStore((state) => state.selectedSources);

  const menuItems = [
    {
      key: '/batch',
      label: '批量下载',
    },
    {
      key: '/history',
      label: '下载历史',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#F2F2F7' }}>
      <Layout.Header style={{
        background: '#fff',
        padding: '0 24px',
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <Title level={3} style={{ margin: 0, lineHeight: '64px' }}>
          音乐下载器
        </Title>
        <Text type="secondary" style={{ fontSize: 12 }}>
          已选 {selectedSources.length} 个音乐源
        </Text>
      </Layout.Header>

      <Layout>
        <Layout.Sider
          width={200}
          style={{
            background: '#fff',
            borderRight: '1px solid #E5E5EA',
          }}
          collapsible={false}
        >
          <Menu
            mode="inline"
            defaultSelectedKeys={['/batch']}
            style={{ borderRight: 0 }}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Layout.Sider>

        <Layout.Content style={{ padding: '24px' }}>
          <Routes>
            {/* 默认重定向到批量下载 */}
            <Route path="/" element={<Navigate to="/batch" replace />} />

            {/* 批量下载页 */}
            <Route path="/batch" element={<BatchDownloadPage />} />

            {/* 下载历史页 */}
            <Route path="/history" element={<DownloadHistoryPage />} />
          </Routes>
        </Layout.Content>
      </Layout>

      <Layout.Footer style={{
        textAlign: 'center',
        background: '#fff',
        borderTop: '1px solid #E5E5EA',
      }}>
        <Text type="secondary">
          音乐下载器 Web版 v2.0.0 | Powered by FastAPI + React
        </Text>
      </Layout.Footer>
    </Layout>
  );
}

export default App;
