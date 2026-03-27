# Legacy 说明

这个目录用于记录仍保留在仓库中的遗留入口和历史产物，避免它们继续和当前 Web 主产品界面混淆。

## 当前遗留保留项

### 1. `pyqt_ui/`

这是旧的 PyQt 桌面界面。

保留原因：

- 兼容历史使用方式
- 排查旧桌面端流程
- 某些本地单窗口调试仍然可能用到

当前定位：

- 兼容入口
- 不是产品基线
- 不再反向决定 Web 页面结构

### 2. `START_DESKTOP.bat`

用于启动本地 PyQt 桌面版。

### 3. `START_DOCKER_DESKTOP.bat`

用于启动 Docker 中的 PyQt 桌面版。

### 4. `backend/static/index.html`

这是更早期的静态调试页面。

当前定位：

- 旧版静态页面
- 仅作兼容保留
- 不代表当前 React Web 主界面

## 当前主入口

当前应默认使用：

- `START.bat`
- `START_WEB.bat`
- `frontend/` + `backend/` 对应的 React/FastAPI Web 方案

## 维护原则

以后遇到遗留内容时，优先按以下顺序处理：

1. 如果会误导主产品方向，先加 `legacy` 标记
2. 如果仅用于历史参考，迁到 `docs/legacy/`
3. 如果既不运行也无参考价值，再考虑删除
