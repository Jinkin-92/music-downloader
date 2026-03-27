# Design System - Music Downloader

> 项目设计系统文档，确保双平台（Web/React + Desktop/PyQt6）视觉一致性

---

## 1. 设计原则

### 1.1 核心理念
- **功能驱动**：每个设计决策服务于用户体验和操作效率
- **双平台一致**：Web 和 Desktop 保持相同的视觉语言和交互模式
- **专业可信**：传达可靠的音乐下载工具形象

### 1.2 平台差异策略
| 维度 | Web (React+AntD) | Desktop (PyQt6) |
|------|------------------|-----------------|
| 基础组件 | Ant Design 组件库 | Qt Widgets 原生组件 |
| 样式系统 | CSS + AntD Tokens | QSS + 内联样式 |
| 动画实现 | CSS Transitions | QPropertyAnimation |
| 响应式 | 断点适配 | 固定窗口尺寸 |

---

## 2. 色彩系统

### 2.1 音乐源品牌色

每个音乐平台对应一个固定的品牌色，双平台统一使用：

| 平台 | 中文名 | 色值 | 色板角色 | 用途 |
|------|--------|------|----------|------|
| QQMusicClient | QQ音乐 | `#52c41a` | success | 来源标签、统计卡片 |
| NeteaseMusicClient | 网易云 | `#ff4d4f` | primary | 来源标签、统计卡片 |
| KugouMusicClient | 酷狗 | `#1890ff` | info | 来源标签、统计卡片 |
| KuwoMusicClient | 酷我 | `#fa8c16` | warning | 来源标签、统计卡片 |
| MiguMusicClient | 咪咕 | `#722ed1` | purple | 来源标签、统计卡片 |

### 2.2 相似度阈值色

用于表示歌曲匹配质量的语义化颜色：

| 相似度范围 | 色值 | 语义 | 应用场景 |
|------------|------|------|----------|
| ≥80% | `#52c41a` | success | 高质量匹配，自动选中 |
| ≥60% | `#faad14` | warning | 中等质量，需要确认 |
| <60% | `#f5222d` | error | 低质量，需人工选择 |

### 2.3 语义色彩系统

| 语义 | 色值 | 用途 |
|------|------|------|
| Primary | `#1890ff` | 主按钮、链接、激活状态 |
| Success | `#52c41a` | 成功状态、完成提示 |
| Warning | `#faad14` | 警告状态、需要关注 |
| Error | `#f5222d` | 错误状态、失败提示 |
| Text Primary | `rgba(0, 0, 0, 0.88)` | 主要文字 |
| Text Secondary | `rgba(0, 0, 0, 0.65)` | 次要文字 |
| Text Tertiary | `rgba(0, 0, 0, 0.45)` | 辅助文字、禁用状态 |
| Border | `#d9d9d9` | 边框、分割线 |
| Background | `#f5f5f5` | 页面背景、表头背景 |
| Surface | `#ffffff` | 卡片背景、弹窗背景 |

### 2.4 PyQt6 色彩应用

```python
# 相似度评分颜色映射
SIMILARITY_COLORS = {
    'high': '#52c41a',    # >= 80%
    'medium': '#faad14',  # >= 60%
    'low': '#f5222d',     # < 60%
}

# 音乐源颜色映射
SOURCE_COLORS = {
    'QQMusicClient': '#52c41a',
    'NeteaseMusicClient': '#ff4d4f',
    'KugouMusicClient': '#1890ff',
    'KuwoMusicClient': '#fa8c16',
    'MiguMusicClient': '#722ed1',
}

# 统计状态色
STATS_COLORS = {
    'valid': 'green',
    'missing_high': 'red',    # 缺失率 > 10%
    'missing_low': 'orange',  # 有缺失但 <= 10%
}
```

---

## 3. 字体排版

### 3.1 字体栈

**Web 端 (Ant Design 默认)**:
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
```

**PyQt6 端 (系统默认)**:
```python
# 使用 Qt 默认系统字体
# 如需指定，可使用:
font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
```

### 3.2 字号层级

| 层级 | 字号 | 行高 | 字重 | 用途 |
|------|------|------|------|------|
| H1 | 38px | 1.4 | 600 | 页面主标题 |
| H2 | 30px | 1.4 | 600 | 区块标题 |
| H3 | 24px | 1.4 | 600 | 子区块标题 |
| H4 | 20px | 1.5 | 600 | 卡片标题 |
| Body | 14px | 1.5 | 400 | 正文内容 |
| Small | 12px | 1.5 | 400 | 辅助文字、标签 |
| Caption | 12px | 1.5 | 400 | 图表说明、脚注 |

### 3.3 PyQt6 字号映射

```python
# QLabel 字号设置
TITLE_FONT = QFont()
TITLE_FONT.setPointSize(16)  # ~24px
TITLE_FONT.setBold(True)

BODY_FONT = QFont()
BODY_FONT.setPointSize(10)   # ~14px

SMALL_FONT = QFont()
SMALL_FONT.setPointSize(9)   # ~12px
```

---

## 4. 间距系统

### 4.1 基础单位

以 **8px** 为基础单位，构建统一的间距系统。

| Token | 值 | 用途 |
|-------|-----|------|
| xs | 4px | 紧凑间距、图标内部 |
| sm | 8px | 小组件间距 |
| md | 16px | 标准间距 |
| lg | 24px | 大间距 |
| xl | 32px | 区块间距 |
| xxl | 48px | 页面间距 |

### 4.2 Web 端 (AntD)

```tsx
// Space 组件 size prop
size="small"    // 8px
size="middle"   // 16px
size="large"    // 24px

// 常用布局间距
{ margin: '24px 0' }      // 区块上下间距
{ padding: '24px' }       // 卡片内边距
{ gap: '16px' }           // 栅格间距
```

### 4.3 PyQt6 端

```python
# 标准布局间距
LAYOUT_SPACING = 10           # 控件间距 ~16px
LAYOUT_MARGIN = 20            # 边距 ~24px

# 应用示例
layout.setSpacing(10)
layout.setContentsMargins(20, 20, 20, 20)
```

---

## 5. 组件规范

### 5.1 StatCard 统计卡片

**用途**: 显示下载历史的统计摘要（总计/有效/缺失）

**Web 端 (AntD)**:
```tsx
<Card>
  <Statistic
    title="总计"
    value={total}
    valueStyle={{ color: '#1890ff' }}
  />
</Card>
```

**PyQt6 端**:
```python
# QLabel + 样式表实现
stats_label.setStyleSheet("color: green;")  # 根据状态变化
```

### 5.2 SimilarityBadge 相似度徽章

**用途**: 在搜索结果中显示匹配相似度

**样式规则**:
- ≥80%: 绿色背景 + 白色文字
- ≥60%: 橙色背景 + 白色文字
- <60%: 红色背景 + 白色文字

**Web 端**:
```tsx
<Badge
  count={`${similarity}%`}
  style={{
    backgroundColor: similarity >= 0.8 ? '#52c41a' :
                     similarity >= 0.6 ? '#faad14' : '#f5222d'
  }}
/>
```

**PyQt6 端**:
```python
# QProgressBar 或 QLabel + 自定义样式
similarity_label.setStyleSheet(f"color: {get_similarity_color(score)};")
```

### 5.3 SourceTag 来源标签

**用途**: 标识音乐来源平台

**Web 端**:
```tsx
<Tag color={SOURCE_COLORS[source]}>{label}</Tag>
```

**PyQt6 端**:
```python
# QPushButton 或 QLabel 样式化
source_btn.setStyleSheet(f"background-color: {SOURCE_COLORS[source]}; color: white;")
```

### 5.4 EmptyState 空状态

**用途**: 当表格/列表无数据时显示

**内容规范**:
- 图标（可选）: 音乐图标或空箱图标
- 主文案: "暂无下载记录"
- 辅助文案: "下载歌曲后将自动记录"
- 操作按钮（可选）: 引导用户开始操作

**Web 端 (AntD)**:
```tsx
<Empty
  description={
    <>
      <p>暂无下载记录</p>
      <p style={{ color: 'rgba(0,0,0,0.45)' }}>
        下载歌曲后将自动记录
      </p>
    </>
  }
/>
```

**PyQt6 端**:
```python
# 表格为空时显示提示
if len(records) == 0:
    status_label.setText("💡 暂无下载记录，下载歌曲后将自动记录")
```

### 5.5 LoadingIndicator 加载指示器

**用途**: 表示异步操作进行中

**Web 端**:
```tsx
<Spin tip="正在验证文件状态..." />
```

**PyQt6 端**:
```python
# QProgressBar 不确定模式 + 状态文本
progress_bar.setRange(0, 0)  # 不确定进度
status_label.setText("正在验证文件是否存在...")
```

---

## 6. 动效系统

### 6.1 动效原则

- **目的性**: 每个动画都应有明确目的（引导注意、提供反馈、解释变化）
- **适度**: 避免过度动画干扰操作
- **性能**: 60fps 流畅度，优先使用 GPU 加速属性

### 6.2 时长规范

| 场景 | 时长 | 说明 |
|------|------|------|
| 微交互 | 150ms | 按钮点击、开关切换 |
| 标准过渡 | 300ms | 弹窗、提示出现消失 |
| 复杂动画 | 500ms | 页面切换、数据加载 |

### 6.3 缓动函数

| 名称 | CSS | 用途 |
|------|-----|------|
| ease-out | `cubic-bezier(0, 0, 0.2, 1)` | 元素进入 |
| ease-in | `cubic-bezier(0.4, 0, 1, 1)` | 元素退出 |
| ease-in-out | `cubic-bezier(0.4, 0, 0.2, 1)` | 状态切换 |

### 6.4 Web 端实现

```css
/* 标准过渡 */
.element {
  transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* 表格行悬停 */
.table-row:hover {
  transition: background-color 150ms ease-out;
}
```

### 6.5 PyQt6 端实现

```python
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

# 属性动画示例
animation = QPropertyAnimation(widget, b"geometry")
animation.setDuration(300)
animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
animation.setStartValue(start_rect)
animation.setEndValue(end_rect)
animation.start()
```

---

## 7. 交互规范

### 7.1 键盘快捷键

| 快捷键 | 功能 | 平台 |
|--------|------|------|
| Ctrl+H | 打开下载历史 | PyQt6 |
| Ctrl+Enter | 执行搜索 | Web |
| Ctrl+D | 开始下载 | Web |

### 7.2 按钮状态

**禁用状态规则**:
- 异步操作进行中，相关操作按钮应禁用
- 验证文件时：禁用"验证"、"清理"、"刷新"按钮
- 搜索/下载进行中：禁用对应的启动按钮

### 7.3 表格交互

**PyQt6 QTableWidget**:
- 行选择: `SelectionBehavior.SelectRows`
- 多选: `SelectionMode.ExtendedSelection`
- 右键菜单: 提供快捷操作（打开文件夹、删除等）

---

## 8. 平台特定实现

### 8.1 PyQt6 样式示例

```python
# 相似度评分样式
def get_similarity_style(score: float) -> str:
    if score >= 0.8:
        return "color: #52c41a; font-weight: bold;"
    elif score >= 0.6:
        return "color: #faad14;"
    else:
        return "color: #f5222d;"

# 统计标签样式
def get_stats_style(missing_rate: float) -> str:
    if missing_rate > 0.1:
        return "color: red;"
    elif missing_rate > 0:
        return "color: orange;"
    return "color: green;"
```

### 8.2 Web 端样式示例

```tsx
// 相似度显示组件
const SimilarityDisplay = ({ score }: { score: number }) => {
  const color = score >= 0.8 ? 'success' :
                score >= 0.6 ? 'warning' : 'error';
  return <Tag color={color}>{(score * 100).toFixed(0)}%</Tag>;
};
```

---

## 9. 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-03-19 | 1.0.0 | 初始版本，基于设计审计创建 |

---

## 10. 参考

- 设计审计报告属于本地 QA 产物，不再纳入 GitHub 仓库版本控制
- [Ant Design 设计系统](https://ant.design/docs/spec/introduce)
- [PyQt6 文档](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
