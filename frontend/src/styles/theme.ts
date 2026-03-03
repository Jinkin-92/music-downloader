/**
 * Apple风格设计系统
 *
 * 基于Apple Human Interface Guidelines设计
 * 使用iOS系统色彩和设计令牌
 */

/**
 * iOS系统色彩
 */
export const appleColors = {
  // 主要色
  primary: '#007AFF',      // iOS Blue
  success: '#34C759',      // iOS Green
  warning: '#FF9500',      // iOS Orange
  error: '#FF3B30',        // iOS Red

  // 相似度颜色（用于批量匹配）
  similarityHigh: '#34C759',   // ≥80% 绿色
  similarityMedium: '#FF9500', // 60-79% 黄色
  similarityLow: '#FF3B30',    // <60% 红色

  // 中性色
  background: '#F2F2F7',   // iOS浅灰背景
  surface: '#FFFFFF',      // 白色卡片
  text: '#000000',         // 纯黑文字
  textSecondary: '#8E8E93', // 灰色次要文字
  textTertiary: '#C7C7CC', // 浅灰色文字

  // 边框
  border: '#E5E5EA',       // iOS边框色
  divider: '#C6C6C8',      // iOS分割线

  // 阴影（Apple风格）
  boxShadowSM: '0 1px 2px rgba(0,0,0,0.05)',
};

/**
 * Ant Design主题定制
 * 用于ConfigProvider的theme配置
 */
export const antDesignTheme = {
  token: {
    // 主色
    colorPrimary: appleColors.primary,
    colorSuccess: appleColors.success,
    colorWarning: appleColors.warning,
    colorError: appleColors.error,

    // 圆角（Apple风格）
    borderRadius: 12,
    borderRadiusLG: 16,
    borderRadiusSM: 8,
    borderRadiusXS: 4,

    // 字体（Apple系统字体）
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif',
    fontSize: 14,
    fontSizeHeading1: 28,
    fontSizeHeading2: 24,
    fontSizeHeading3: 20,
    fontSizeHeading4: 18,
    fontSizeHeading5: 16,

    // 间距
    paddingXS: 8,
    paddingSM: 12,
    paddingMD: 16,
    paddingLG: 24,
    paddingXL: 32,

    // 阴影（Apple风格）
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
    boxShadowSM: '0 1px 2px rgba(0,0,0,0.05)',
    boxShadowMD: '0 4px 6px rgba(0,0,0,0.07)',
    boxShadowLG: '0 10px 15px rgba(0,0,0,0.1)',
  },

  // 组件级定制
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 40,        // Apple触控友好的44px变体
      paddingInline: 20,
      fontWeight: 500,
    },

    Input: {
      borderRadius: 8,
      controlHeight: 40,
      paddingInline: 12,
    },

    TextArea: {
      borderRadius: 8,
      paddingInline: 12,
      paddingBlock: 8,
    },

    Select: {
      borderRadius: 8,
      controlHeight: 40,
    },

    Table: {
      borderRadiusLG: 12,
      headerBg: appleColors.background,
    },

    Card: {
      borderRadiusLG: 12,
      boxShadowSM: appleColors.boxShadowSM,
    },

    Modal: {
      borderRadiusLG: 12,
    },

    Tag: {
      borderRadiusSM: 4,
    },
  },
};

/**
 * 间距系统
 */
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 40,
};

/**
 * 断点（响应式）
 */
export const breakpoints = {
  sm: '576px',
  md: '768px',
  lg: '992px',
  xl: '1200px',
  xxl: '1600px',
};

/**
 * Z-index层级
 */
export const zIndices = {
  dropdown: 1050,
  sticky: 1020,
  fixed: 1030,
  modalMask: 1000,
  modal: 1050,
  popover: 1060,
};

/**
 * 工具函数
 */

/**
 * 根据相似度分数获取颜色
 */
export const getSimilarityColor = (similarity: number): string => {
  if (similarity >= 0.8) return appleColors.similarityHigh;   // 绿色
  if (similarity >= 0.6) return appleColors.similarityMedium; // 黄色
  return appleColors.similarityLow;                          // 红色
};

/**
 * 根据相似度分数获取Ant Design Tag颜色
 */
export const getSimilarityTagColor = (similarity: number): string => {
  if (similarity >= 0.8) return 'success';
  if (similarity >= 0.6) return 'warning';
  return 'error';
};

/**
 * 转换字节为可读大小
 */
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 转换秒数为可读时长
 */
export const formatDuration = (seconds: number): string => {
  if (!seconds || seconds === 0) return '--:--';
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  return `${min}:${sec.toString().padStart(2, '0')}`;
};
