/**
 * 单曲搜索页面
 *
 * 支持多源搜索、结果展示、一键下载
 */
import { useState } from 'react';
import { Card, Space, Typography, Alert, Tag } from 'antd';
import { useMutation } from '@tanstack/react-query';
import { App } from 'antd';
import SourceSelector from '../components/search/SourceSelector';
import SearchInput from '../components/search/SearchInput';
import SearchResultsTable from '../components/search/SearchResultsTable';
import { searchApi } from '../services/api';
import { useUIStore } from '../stores/useUIStore';

const { Title } = Typography;

function SingleSearchPage() {
  // 使用App hook获取message API
  const { message } = App.useApp();

  // UI状态
  const { selectedSources } = useUIStore();

  // 搜索状态
  const [keyword, setKeyword] = useState('');
  const [searched, setSearched] = useState(false);
  const [errorInfo, setErrorInfo] = useState<string | null>(null);

  // 搜索Mutation
  const searchMutation = useMutation({
    mutationFn: async () => {
      setErrorInfo(null);
      return await searchApi.searchMusic(keyword, selectedSources);
    },
    onSuccess: (data) => {
      setSearched(true);
      const total = data.data.total;
      if (total > 0) {
        message.success(`找到 ${total} 首歌曲`);
      } else {
        message.warning('未找到匹配的歌曲，请尝试其他关键词或音乐源');
      }
    },
    onError: (err: any) => {
      const errorMsg = err.message || '搜索失败，请重试';
      setErrorInfo(errorMsg);
      message.error(errorMsg);
    },
    retry: 1, // 失败后重试1次
    retryDelay: 1000,
  });

  /**
   * 处理搜索
   */
  const handleSearch = () => {
    if (!keyword.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    if (selectedSources.length === 0) {
      message.warning('请至少选择一个音乐源');
      return;
    }

    searchMutation.mutate();
  };

  return (
    <div className="page">
      <Title level={2} className="page-title">
        单曲搜索
      </Title>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 使用提示 */}
        <Alert
          message="💡 使用建议"
          description={
            <div>
              <p>为获得最佳搜索体验：</p>
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                <li>优先使用 <Tag color="green">QQ音乐</Tag> 或 <Tag color="blue">酷狗</Tag>（响应快，10-20秒）</li>
                <li>避免单独使用 <Tag color="red">网易云</Tag>（响应慢，可能超时）</li>
                <li>搜索时请耐心等待，一般需要 10-30秒</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          closable
        />

        {/* 音乐源选择 */}
        <Card title="1. 选择音乐源">
          <SourceSelector />
        </Card>

        {/* 搜索输入 */}
        <Card title="2. 输入搜索关键词">
          <SearchInput
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onSearch={handleSearch}
            loading={searchMutation.isPending}
          />
        </Card>

        {/* 错误提示 */}
        {errorInfo && (
          <Alert
            message="搜索失败"
            description={
              <div>
                <p>{errorInfo}</p>
                <p style={{ marginTop: 8, marginBottom: 0 }}>
                  <strong>建议操作：</strong>
                </p>
                <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                  <li>仅选择"QQ音乐"或"酷狗"重试</li>
                  <li>减少选中的音乐源数量</li>
                  <li>尝试更换搜索关键词</li>
                </ul>
              </div>
            }
            type="error"
            closable
            onClose={() => setErrorInfo(null)}
            showIcon
          />
        )}

        {/* 搜索结果 */}
        {searched && !errorInfo && (
          <Card title="3. 搜索结果">
            <SearchResultsTable
              data={searchMutation.data?.data.songs || []}
              loading={searchMutation.isPending}
            />
          </Card>
        )}
      </Space>
    </div>
  );
}

export default SingleSearchPage;
