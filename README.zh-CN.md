# Music Downloader 中文说明

[English](README.md) | 简体中文

这是一个多音源中文音乐下载项目，当前以 Web 端为产品基准，同时保留 PyQt 桌面版作为兼容入口。

- Web 版：React + FastAPI，是当前主界面
- 桌面版：PyQt 本地窗口，用于兼容旧流程
- Docker 桌面模式：本质上仍是 PyQt 桌面版，只是通过 VNC 访问

## 当前架构

项目不是两套互相独立的实现，而是“共享核心能力 + 多个界面层”：

- `core/`
  负责搜索、匹配、下载、音源客户端、批量解析等核心逻辑
- `backend/`
  为 Web 版提供 FastAPI 接口、后台任务和下载历史服务
- `frontend/`
  React Web 界面，是当前主产品界面
- `pyqt_ui/`
  传统桌面界面，直接调用 `core/` 能力

这意味着：

- 搜索和下载核心能力是共享的
- Web 是当前应优先参考的界面基线
- 桌面版不再反向定义 Web 页面结构

## 当前产品基线

这次重新对齐后的原则是：

- 以 Web 端当前界面为准
- Web 主流程围绕：批量下载、歌单导入、下载历史
- PyQt 桌面端作为兼容入口保留
- 文档、启动脚本、说明都以 Web 为默认入口

## `START.bat` 现在做什么

之前的 `START.bat` 语义不清，而且还指向了仓库里不存在的 `docker-compose.web.yml`。现在已经重新明确：

```bat
START.bat
```

它默认启动 Web 主界面。

如果你要启动遗留桌面版，请使用：

- `START_DESKTOP.bat`
- `START_DOCKER_DESKTOP.bat`

因此现在的答案很明确：

- `START.bat`：启动 Web 版
- `START_DESKTOP.bat`：启动本地 PyQt 桌面版
- `START_DOCKER_DESKTOP.bat`：启动 Docker 里的 PyQt 桌面版

## 推荐启动方式

### 方式 1：默认入口

```powershell
START.bat
```

### 方式 2：显式启动 Web 版

```powershell
START_WEB.bat
```

默认地址：

- Web 前端：`http://localhost:5173`
- 后端文档：`http://localhost:8003/docs`

### 方式 3：启动遗留桌面版

```powershell
START_DESKTOP.bat
```

或：

```powershell
python -m pyqt_ui.main
```

### 方式 4：Docker 桌面模式

```powershell
START_DOCKER_DESKTOP.bat
```

注意：

- 当前仓库里的 `docker-compose.yml` 对应的是桌面版容器
- 它不是 React Web 版的 docker-compose

## 功能关系

当前应这样理解：

- Web 主界面当前聚焦：批量下载、歌单导入、下载历史
- 后端仍然保留单曲搜索 API 能力
- PyQt 桌面端保留一些旧交互，但不再作为 Web UI 的模板

## 目录说明

```text
backend/     Web 后端 API、任务管理、下载历史服务
core/        共享核心能力：搜索、匹配、下载、音源客户端
frontend/    React Web 前端（当前主界面）
pyqt_ui/     PyQt 桌面界面（兼容入口）
docs/        补充文档
```

补充：

- `docs/legacy/` 用来记录遗留入口和历史产物说明

## 建议阅读入口

- `frontend/src/pages/BatchDownloadPage.tsx`
- `frontend/src/pages/DownloadHistoryPage.tsx`
- `backend/api/playlist.py`
- `backend/api/download.py`
- `backend/api/search.py`
- `core/downloader.py`

## 常用命令

前端构建：

```powershell
npm --prefix frontend run build
```

前端 E2E：

```powershell
npm --prefix frontend run test:e2e
```

后端回归测试：

```powershell
python -m unittest backend.tests.test_playlist_batch_search_duplicate_regression
```

## 当前建议

日常使用请直接走 Web 版。

只有在核对旧流程、排查桌面端行为，或需要兼容历史使用习惯时，再使用 PyQt 版。
