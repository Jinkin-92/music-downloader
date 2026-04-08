# Music Downloader

Multi-source Chinese music downloader with a modern web UI.

[English](README.md) | [简体中文](README.zh-CN.md)

---

## Features

- **Multi-source Search**: Search across 6 Chinese music platforms simultaneously
- **Batch Download**: Paste a list of songs and download them in bulk with intelligent matching
- **Playlist Import**: Import playlists from NetEase Cloud Music and QQ Music
- **Download History**: Track all downloads with duplicate detection and file management
- **High Performance**: Concurrent search and download with automatic source fallback

## Supported Music Sources

| Source | Type | Status |
| ------ | ---- | ------ |
| NetEase Cloud Music | HTTP API | Active |
| QQ Music | HTTP API | Active |
| Kugou | HTTP API | Active |
| Kuwo | HTTP API | Active |
| Migu | HTTP API | Active |
| PJMP3 | HTTP API | Active |

## Quick Start

### Option 1: Use the Launcher

```powershell
START.bat
```

### Option 2: Run Locally

**Backend:**

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8003
```

**Frontend:**

```powershell
cd frontend
npm install
npm run dev
```

Open:

- Web UI: `http://localhost:5173`
- API Docs: `http://localhost:8003/docs`

### Option 3: Docker

```powershell
docker compose up -d --build
```

Open:

- Web UI: `http://localhost:8080`
- API Docs: `http://localhost:8003/docs`

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite + Ant Design
- **Backend**: FastAPI (Python)
- **Search Engine**: musicdl with custom source adapters
- **Testing**: Playwright E2E + pytest

## Project Structure

```
music-downloader/
├── backend/           # FastAPI backend
│   └── api/          # API endpoints
├── core/              # Shared search & download engine
├── frontend/          # React web application
└── docs/              # Documentation
```

## License

MIT License
