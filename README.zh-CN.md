# Music Downloader 音乐下载器

多音源中文音乐下载器，提供现代化的 Web 界面。

[English](README.md) | 简体中文

---

## 功能特点

- **多源搜索**：同时搜索 6 个中文音乐平台
- **批量下载**：粘贴歌曲列表，智能匹配后批量下载
- **歌单导入**：支持从网易云音乐和 QQ 音乐导入歌单
- **下载历史**：记录所有下载历史，支持去重和文件管理
- **高性能**：并发搜索和下载，自动切换音源

## 支持的音乐源

| 音乐源 | 类型 | 状态 |
| ------ | ---- | ---- |
| 网易云音乐 | HTTP API | 正常 |
| QQ 音乐 | HTTP API | 正常 |
| 酷狗音乐 | HTTP API | 正常 |
| 酷我音乐 | HTTP API | 正常 |
| 咪咕音乐 | HTTP API | 正常 |
| PJMP3 | HTTP API | 正常 |

## 快速开始

### 方式一：使用启动脚本

```powershell
START.bat
```

### 方式二：本地运行

**后端：**

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8003
```

**前端：**

```powershell
cd frontend
npm install
npm run dev
```

打开浏览器：

- Web 界面：`http://localhost:5173`
- API 文档：`http://localhost:8003/docs`

### 方式三：Docker 部署

```powershell
docker compose up -d --build
```

打开浏览器：

- Web 界面：`http://localhost:8080`
- API 文档：`http://localhost:8003/docs`

## 技术栈

- **前端**：React 18 + TypeScript + Vite + Ant Design
- **后端**：FastAPI (Python)
- **搜索引擎**：musicdl + 自定义音源适配器
- **测试**：Playwright E2E + pytest

## 项目结构

```
music-downloader/
├── backend/           # FastAPI 后端
│   └── api/          # API 接口
├── core/              # 共享搜索下载引擎
├── frontend/          # React Web 应用
└── docs/              # 文档
```

## 许可证

MIT License
