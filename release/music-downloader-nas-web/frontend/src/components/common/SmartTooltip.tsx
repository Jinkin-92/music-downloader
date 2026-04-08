/**
 * 智能提示组件
 *
 * 为用户提供上下文相关的帮助提示
 */
import React, { useState } from 'react';
import { Tooltip, Button } from 'antd';
import { QuestionCircleOutlined, InfoCircleOutlined, WarningOutlined } from '@ant-design/icons';
import type { TooltipProps } from 'antd/es/tooltip';

export interface SmartTooltipProps {
  type?: 'info' | 'warning' | 'question';
  title: string;
  description?: string;
  placement?: TooltipProps['placement'];
  children?: React.ReactNode;
  showIcon?: boolean;
  onLearnMore?: () => void;
}

const SmartTooltip: React.FC<SmartTooltipProps> = ({
  type = 'info',
  title,
  description,
  placement = 'top',
  children,
  showIcon = true,
  onLearnMore
}) => {
  const [visible, setVisible] = useState(false);

  const iconMap = {
    info: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
    warning: <WarningOutlined style={{ color: '#faad14' }} />,
    question: <QuestionCircleOutlined style={{ color: '#8c8c8c' }} />
  };

  const content = (
    <div style={{ maxWidth: 300 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>
      {description && (
        <div style={{ fontSize: 13, color: '#666', lineHeight: 1.6 }}>
          {description}
        </div>
      )}
      {onLearnMore && (
        <div style={{ marginTop: 12, textAlign: 'right' }}>
          <Button
            type="link"
            size="small"
            onClick={onLearnMore}
            style={{ padding: 0 }}
          >
            了解更多
          </Button>
        </div>
      )}
    </div>
  );

  if (children) {
    return (
      <Tooltip
        title={content}
        placement={placement}
        visible={visible}
        onVisibleChange={setVisible}
      >
        <span
          style={{ cursor: 'help', display: 'inline-flex', alignItems: 'center' }}
          onClick={() => setVisible(!visible)}
        >
          {children}
          {showIcon && <span style={{ marginLeft: 4 }}>{iconMap[type]}</span>}
        </span>
      </Tooltip>
    );
  }

  return (
    <Tooltip
      title={content}
      placement={placement}
      visible={visible}
      onVisibleChange={setVisible}
    >
      <span
        style={{ cursor: 'help', display: 'inline-flex', alignItems: 'center' }}
        onClick={() => setVisible(!visible)}
      >
        {showIcon && iconMap[type]}
      </span>
    </Tooltip>
  );
};

export default SmartTooltip;
