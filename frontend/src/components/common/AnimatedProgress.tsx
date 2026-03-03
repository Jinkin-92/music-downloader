/**
 * 流体动画进度条组件
 *
 * 特性：
 * - 渐变色进度条
 * - 流动动画效果
 * - 平滑过渡
 * - 可配置颜色主题
 */
import React, { useEffect, useState } from 'react';
import { Progress } from 'antd';
import './AnimatedProgress.css';

export interface AnimatedProgressProps {
  percent: number;
  status?: 'normal' | 'active' | 'success' | 'exception';
  theme?: 'blue' | 'green' | 'purple' | 'orange' | 'pink';
  showInfo?: boolean;
  strokeWidth?: number;
  trailColor?: string;
  animated?: boolean;
  children?: React.ReactNode;
}

const AnimatedProgress: React.FC<AnimatedProgressProps> = ({
  percent,
  status = 'active',
  theme = 'blue',
  showInfo = true,
  strokeWidth = 12,
  trailColor = '#f0f0f0',
  animated = true,
  children,
}) => {
  const [displayPercent, setDisplayPercent] = useState(0);

  // 平滑过渡动画
  useEffect(() => {
    if (animated) {
      const duration = 800; // 动画持续时间
      const steps = 60; // 帧数
      const increment = percent / steps;
      let current = 0;

      const timer = setInterval(() => {
        current += increment;
        if (current >= percent) {
          setDisplayPercent(percent);
          clearInterval(timer);
        } else {
          setDisplayPercent(Math.floor(current));
        }
      }, duration / steps);

      return () => clearInterval(timer);
    } else {
      setDisplayPercent(percent);
    }
  }, [percent, animated]);

  // 主题配色
  const getThemeClass = () => {
    return `animated-progress-${theme}`;
  };

  return (
    <div className={`animated-progress-container ${getThemeClass()}`}>
      <Progress
        percent={displayPercent}
        status={status}
        strokeWidth={strokeWidth}
        trailColor={trailColor}
        showInfo={showInfo}
        className="animated-progress-bar"
      />
      {children && (
        <div className="animated-progress-children">
          {children}
        </div>
      )}
    </div>
  );
};

export default AnimatedProgress;
