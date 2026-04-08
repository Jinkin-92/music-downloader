/**
 * 操作引导提示组件
 *
 * 为首次用户提供分步引导
 */
import React, { useState, useEffect } from 'react';
import { Tour, Button } from 'antd';

export interface TourStep {
  target: () => HTMLElement | null;
  title: string;
  description: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

interface GuidedTourProps {
  steps: TourStep[];
  onComplete?: () => void;
  onSkip?: () => void;
  storageKey?: string;
}

const GuidedTour: React.FC<GuidedTourProps> = ({
  steps,
  onComplete,
  onSkip,
  storageKey = 'music-downloader-tour-completed'
}) => {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // 检查是否已完成过引导
    const completed = localStorage.getItem(storageKey);
    if (!completed) {
      // 延迟1秒显示，让页面先渲染完成
      const timer = setTimeout(() => setOpen(true), 1000);
      return () => clearTimeout(timer);
    }
  }, [storageKey]);

  const handleComplete = () => {
    setOpen(false);
    localStorage.setItem(storageKey, 'true');
    onComplete?.();
  };

  const _handleSkip = () => {
    setOpen(false);
    localStorage.setItem(storageKey, 'true');
    onSkip?.();
  };
  void _handleSkip; // avoid unused warning

  // 转换 steps 类型以匹配 Tour 组件
  const tourSteps = steps.map(step => ({
    ...step,
    target: step.target as unknown as HTMLElement
  }));

  return (
    <>
      {/* 重置按钮（开发用） */}
      {process.env.NODE_ENV === 'development' && (
        <Button
          size="small"
          onClick={() => {
            localStorage.removeItem(storageKey);
            setOpen(true);
          }}
          style={{ position: 'fixed', bottom: 16, right: 16, zIndex: 9999 }}
        >
          重置引导
        </Button>
      )}

      <Tour
        open={open}
        onClose={handleComplete}
        steps={tourSteps}
        indicatorsRender={(current, total) => (
          <span>
            {current + 1} / {total}
          </span>
        )}
        scrollIntoViewOptions={{ block: 'center' }}
      />
    </>
  );
};

export default GuidedTour;
