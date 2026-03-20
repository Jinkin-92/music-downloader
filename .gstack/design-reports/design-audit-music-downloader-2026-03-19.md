# Design Audit: music-downloader

| Field | Value |
|-------|-------|
| **Date** | 2026-03-19 |
| **URL** | feature/ui-optimization branch (code-based review) |
| **Scope** | Web (React+AntD) + PyQt6 Desktop UI |
| **Pages reviewed** | 4 components (code analysis) |
| **DESIGN.md** | Not found — inferred from code |

## Design Score: B  |  AI Slop Score: A

> 功能驱动的专业设计，双平台保持一致的体验模式，缺少系统设计文档但实现质量扎实。

| Category | Grade | Notes |
|----------|-------|-------|
| Visual Hierarchy | B | 表格布局清晰，统计信息层次分明 |
| Typography | C | 无明确字体系统，依赖 AntD/Qt 默认值 |
| Spacing & Layout | B | AntD 间距系统 + Qt 布局管理器，双平台各自一致 |
| Color & Contrast | A | 音乐源色彩映射一致，相似度阈值统一 |
| Interaction States | B | 加载/成功/错误状态完整，PyQt 缺省状态可加强 |
| Responsive | B | Web 端 AntD 响应式，PyQt 固定窗口最小尺寸 |
| Motion | C | Web 端有基础过渡，PyQt 无明显动画 |
| Content Quality | B | 文案清晰专业，缺少数占位符处理说明 |
| AI Slop | A | 无模板化设计模式，功能导向 |
| Performance Feel | B | 异步操作 + 进度反馈良好 |

## First Impression

**The site communicates** 专业的音乐下载工具形象，双平台（Web/PyQt）保持一致的视觉语言和功能组织。

**I notice** 音乐源色彩编码系统设计精细（QQ 音乐=绿、网易云=红、酷狗=蓝、酷我=橙、咪咕=紫），相似度颜色阈值统一（≥80% 绿、≥60% 橙、<60% 红）。

**The first 3 things my eye goes to:**
1. 统计卡片（总计/有效/缺失）— 色彩编码（绿/红）直观
2. 表格数据密度 — 信息量大但组织清晰
3. 操作按钮组 — 图标 + 文字，功能清晰

**If I had to describe this in one word:** 务实 (Pragmatic)

## Top 5 Design Improvements

1. **创建设计系统文档 (DESIGN.md)** — 记录字体、色彩、间距规范，确保未来扩展一致性
2. **统一 PyQt 与 Web 的视觉细节** — 相似颜色阈值一致，但 PyQt 可增加色彩反馈
3. **加强空状态设计** — 当前空表格处理较简单，可增加引导性文案和操作提示
4. **添加加载状态动画** — PyQt 端的 VerifyWorker 只有进度条，可增加更友好的视觉反馈
5. **完善键盘快捷键系统** — PyQt 有 Ctrl+H，Web 端应同步快捷键支持

## Inferred Design System

### Typography
- **Web 端**: 依赖 Ant Design 默认字体栈 (系统字体)
- **PyQt 端**: 使用 Qt 默认系统字体
- **问题**: 无自定义字体配置，无层级比例定义

### Colors
**音乐源色彩映射 (双平台一致):**
```
QQ 音乐   → #52c41a (绿色/success)
网易云    → #ff4d4f (红色/primary)
酷狗      → #1890ff (蓝色/info)
酷我      → #fa8c16 (橙色/warning)
咪咕      → #722ed1 (紫色)
```

**相似度状态色:**
```
≥80%  → success (绿色)
≥60%  → warning (橙色)
<60%  → error (红色)
```

**统计状态色:**
```
有效    → blue (Web) / default (PyQt)
缺失    → red (Web) / gray foreground (PyQt)
```

### Spacing
- **Web 端**: AntD 8px 基准间距系统 (`size="small" | "middle" | "large"`)
- **PyQt 端**: Qt 布局管理器，`layout.setSpacing(10)`, `layout.setContentsMargins(20, 20, 20, 20)`

### Heading Scale
- **Web 端**: AntD Typography.Title 层级
- **PyQt 端**: QLabel with HTML (`<h2>下载历史记录</h2>`)

## Findings

### [MEDIUM] Typography — 无自定义字体系统
**Page:** All components
**Impact:** 依赖第三方默认字体，缺少品牌识别度

**问题**: 两处实现均未定义自定义字体，完全依赖 AntD 和 Qt 的默认字体系统。

**理想状态**: DESIGN.md 中定义主字体、等宽字体、字号层级（h1-h6、body、caption）。

---

### [LOW] Spacing — PyQt 与 Web 间距策略不同
**Page:** DownloadHistoryDialog vs DownloadHistoryPage
**Impact:** 双平台视觉密度略有差异

**Web 端**:
```tsx
<Space direction="vertical" size="large" style={{ width: '100%' }}>
```

**PyQt 端**:
```python
layout.setSpacing(10)
layout.setContentsMargins(20, 20, 20, 20)
```

**建议**: 在 DESIGN.md 中记录双平台统一的间距基准值。

---

### [LOW] Interaction States — PyQt 缺少数按钮禁用状态
**Page:** pyqt_ui/history_dialog.py
**Impact:** 用户可能在验证过程中重复点击

**问题**: `on_verify_clicked()` 只禁用了 `verify_btn`，但 `clean_btn` 和 `refresh_btn` 未禁用。

**当前代码**:
```python
@pyqtSlot()
def on_verify_clicked(self):
    self.verify_btn.setEnabled(False)  # ✓
    # clean_btn 和 refresh_btn 未处理
```

**理想状态**: 验证进行时，所有相关操作按钮应禁用，防止状态冲突。

---

### [POLISH] Color — 统计信息色彩可加强
**Page:** DownloadHistoryDialog
**Impact:** 缺失文件比例高时视觉警示不足

**当前代码**:
```python
if missing > 0:
    self.stats_label.setStyleSheet("color: orange;")
else:
    self.stats_label.setStyleSheet("color: green;")
```

**Web 端对比**: 使用 AntD `<Statistic>` 组件，自带色彩和数值放大效果。

**建议**: PyQt 端可考虑使用红色 (`color: red;`) 当缺失比例 > 10% 时加强警示。

---

### [POLISH] Content — 空状态文案缺失
**Page:** DownloadHistoryDialog
**Impact:** 首次打开无历史记录时，用户可能困惑

**问题**: 当前表格为空时，无任何提示文案。

**理想状态**:
```python
if self.history_table.rowCount() == 0:
    self.statusBar_label.setText("💡 暂无下载记录，下载歌曲后将自动记录")
```

---

### [POLISH] Motion — 表格行切换无过渡动画
**Page:** BatchResultsTable (both Web & PyQt)
**Impact:** 候选切换时视觉跳变

**Web 端**: AntD Table 有基础过渡，但自定义候选切换无动画。

**PyQt 端**: QTableWidget 无过渡动画。

**建议**: Web 端可添加 CSS transition，PyQt 端可考虑使用 QPropertyAnimation。

---

## Responsive Summary

| Component | Mobile | Tablet | Desktop |
|-----------|--------|--------|---------|
| DownloadHistoryPage (Web) | AntD 自动响应 | AntD 自动响应 | ✓ 完整布局 |
| DownloadHistoryDialog (PyQt) | N/A | N/A | ✓ 最小尺寸 1000x600 |
| BatchResultsTable (Web) | 横向滚动 | 横向滚动 | ✓ 完整列 |
| MatchSettingsPanel (Web) | 堆叠布局 | 堆叠布局 | ✓ 多列布局 |

**Note:** PyQt 桌面应用不针对移动端优化，固定窗口尺寸策略合理。

## Quick Wins (< 30 min each)

### 1. PyQt 验证期间禁用所有操作按钮
**File:** `pyqt_ui/history_dialog.py:233-244`
**Fix:**
```python
@pyqtSlot()
def on_verify_clicked(self):
    self.verify_btn.setEnabled(False)
    self.clean_btn.setEnabled(False)    # 新增
    self.refresh_btn.setEnabled(False)  # 新增
    # ... 验证完成后恢复
```

### 2. 空状态提示文案
**File:** `pyqt_ui/history_dialog.py:163-166`
**Fix:**
```python
def populate_table(self):
    self.history_table.setRowCount(0)
    if len(self.current_records) == 0:
        self.statusBar_label.setText("💡 暂无下载记录")
```

### 3. 统计信息红色警示阈值
**File:** `pyqt_ui/history_dialog.py:219-230`
**Fix:**
```python
def update_stats(self):
    missing_rate = missing / total if total > 0 else 0
    if missing_rate > 0.1:
        self.stats_label.setStyleSheet("color: red;")
    elif missing > 0:
        self.stats_label.setStyleSheet("color: orange;")
    else:
        self.stats_label.setStyleSheet("color: green;")
```

---

## Review Readiness Dashboard

```bash
echo '{"skill":"plan-design-review","timestamp":"2026-03-19T12:00:00+08:00","status":"issues_open","design_score":"B","ai_slop_score":"A","mode":"Diff-aware (code-based)"}' >> ~/.gstack/projects/Jinkin-92-music-downloader/feature-ui-optimization-reviews.jsonl
```

**Design Review: (LITE) — Code-based audit, no browser screenshots**
