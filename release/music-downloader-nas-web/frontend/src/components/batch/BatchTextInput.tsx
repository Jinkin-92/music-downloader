/**
 * 批量文本输入组件
 *
 * 带格式示例的文本输入框
 */
import { Input } from 'antd';

interface BatchTextInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

function BatchTextInput({
  value,
  onChange,
  placeholder,
}: BatchTextInputProps) {
  const defaultPlaceholder = `每行一首歌曲，格式：歌名 - 歌手

示例：
夜曲 - 周杰伦
晴天 - 周杰伦
七里香 - 周杰伦
稻香 - 周杰伦

💡 提示：
- 每行一首歌曲
- 使用 "-" 分隔歌名和歌手
- 支持复制粘贴列表`;

  return (
    <Input.TextArea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder || defaultPlaceholder}
      autoSize={{ minRows: 10, maxRows: 20 }}
      style={{
        fontFamily: 'Consolas, Monaco, "Courier New", monospace',
        fontSize: 14,
        lineHeight: 1.8,
        borderRadius: 8,
        borderColor: value ? '#1890ff' : undefined,
      }}
      status={value ? '' : 'warning'}
    />
  );
}

export default BatchTextInput;
