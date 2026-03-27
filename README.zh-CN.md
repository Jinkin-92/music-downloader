# Music Downloader 中文说明

[English](README.md) | 简体中文

这是一个多音源中文音乐下载项目，同时保留了两套用户界面：

- Web 版：React + FastAPI
- 桌面版：PyQt 本地窗口

另外仓库还保留了一套 Docker 桌面模式，它本质上运行的仍然是 PyQt 桌面版，只是放进容器后通过 VNC 访问。

## 当前架构

项目现在不是“两套完全独立实现”，而是“共享核心能力 + 两个界面层”：

- `core/`
  负责搜索、匹配、下载、音源客户端、批量解析等核心逻辑
- `backend/`
  为 Web 版提供 FastAPI 接口、后台任务和下载历史服务
- `frontend/`
  React Web 界面，负责单曲搜索、批量下载、歌单导入、历史管理
- `pyqt_ui/`
  传统桌面界面，直接调用 `core/` 能力

这意味着：

- 搜索和下载能力的核心逻辑是共享的
- Web 和桌面并不需要完全复制实现方式
- 但用户层面应该尽量做到主流程功能一致

## 目前功能对齐情况

主流程已经按当前架构重新梳理：

- 单曲搜索：PyQt 有，Web 现在也已恢复入口
- 批量文本搜索：PyQt 有，Web 有
- 歌单导入：PyQt 有，Web 有
- 批量下载：PyQt 有，Web 有
- 下载历史查看：PyQt 有，Web 有
- 打开文件夹：PyQt 有，Web 有
- 清理失效记录：PyQt 有，Web 有
- 删除历史记录：PyQt 有，Web 现在也补上了

说明：

- Web 版是当前推荐入口
- 桌面版仍可运行，但更适合兼容旧流程或本地单机使用

## `START.bat` 现在做什么

以前的 `START.bat` 名称和实际行为不清楚，而且还指向了仓库里不存在的 `docker-compose.web.yml`。现在已经重新整理成一个统一启动菜单：

```bat
START.bat
```

它会给出 3 个启动选项：

1. `START_WEB.bat`
   启动 Web 前端和 FastAPI 后端
2. `START_DESKTOP.bat`
   启动本地 PyQt 桌面窗口
3. `START_DOCKER_DESKTOP.bat`
   启动 Docker 里的 PyQt 桌面版

因此，答案是：

- 旧的 `START.bat` 本意想启动 Web
- 但脚本当时是坏的
- 现在的 `START.bat` 不再含糊，而是作为总入口菜单

## 推荐启动方式

### 方式 1：直接用总入口

```powershell
START.bat
```

### 方式 2：只启动 Web 版

```powershell
START_WEB.bat
```

默认地址：

- Web 前端：`http://localhost:5173`
- 后端文档：`http://localhost:8003/docs`

### 方式 3：只启动桌面版

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

## 目录说明

```text
backend/     Web 后端 API、任务管理、下载历史服务
core/        共享核心能力：搜索、匹配、下载、音源客户端
frontend/    React Web 前端
pyqt_ui/     PyQt 桌面界面
docs/        补充文档
```

## 建议阅读入口

- `frontend/src/pages/SingleSearchPage.tsx`
- `frontend/src/pages/BatchDownloadPage.tsx`
- `frontend/src/pages/DownloadHistoryPage.tsx`
- `backend/api/search.py`
- `backend/api/playlist.py`
- `backend/api/download.py`
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

如果你是自己日常使用，优先走 Web 版。

如果你是在核对旧功能、排查桌面端行为，或者某些本地操作更适合桌面窗口，再使用 PyQt 版。
