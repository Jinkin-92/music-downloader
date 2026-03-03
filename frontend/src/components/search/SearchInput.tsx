/**
 * 搜索输入框组件
 *
 * 带示例提示的搜索输入框
 */
import { Input, Button, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { ChangeEvent } from 'react';

interface SearchInputProps {
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onSearch: () => void;
  loading?: boolean;
}

function SearchInput({ value, onChange, onSearch, loading }: SearchInputProps) {
  return (
    <Space.Compact style={{ width: '100%' }}>
      <Input
        placeholder="输入歌曲名或歌手，例如：周杰伦 晴天"
        value={value}
        onChange={onChange}
        onPressEnter={onSearch}
        size="large"
        allowClear
        disabled={loading}
      />
      <Button
        type="primary"
        icon={<SearchOutlined />}
        onClick={onSearch}
        loading={loading}
        size="large"
      >
        搜索
      </Button>
    </Space.Compact>
  );
}

export default SearchInput;
