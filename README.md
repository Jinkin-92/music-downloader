# Music Downloader

Multi-source Chinese music downloader with a modern web UI for single-song search, batch matching, playlist import, and download history management.

## What This Repo Is

This project started as a PyQt desktop downloader and now includes a web-first workflow built with FastAPI + React.

It is designed for these common use cases:

- Search one song across multiple Chinese music sources
- Paste a batch song list and match candidates in bulk
- Import playlists from NetEase Cloud Music and QQ Music
- Download matched songs with duplicate filtering and history tracking
- Fall back across sources when one platform fails or blocks a track

## Current Status

- Active branch model has been normalized back to `main`
- Current version: `2.0.0.0`
- Primary UI: web app
- Legacy UI: PyQt desktop code is still present in `pyqt_ui/`

## Main Features

- Multi-source search: QQ Music, NetEase, Kugou, Kuwo, Migu, and related source adapters in the codebase
- Batch download flow: text parsing, candidate switching, similarity scoring, bulk actions
- Playlist import: parse playlist links and turn them into batch-search inputs
- Download history: duplicate detection, file existence checks, reopen folder support
- Async backend tasks: long-running batch work continues in the background
- Regression coverage for recent QA fixes and batch-search edge cases

## Tech Stack

- Backend: FastAPI
- Frontend: React 18 + TypeScript + Vite + Ant Design
- Search/download engine: Python service layer in `core/`
- Testing: Playwright E2E + Python unittest
- Legacy desktop app: PyQt6

## Quick Start

### Option 1: Run frontend and backend locally

Backend:

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8003
```

Frontend:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

Open:

- Web UI: `http://localhost:5173`
- API docs: `http://localhost:8003/docs`

### Option 2: Build the frontend

```powershell
npm --prefix frontend install
npm --prefix frontend run build
```

### Option 3: Docker-based startup

The repo includes Docker assets and startup scripts for containerized runs.

Relevant files:

- `Dockerfile`
- `docker-compose.yml`
- `START.bat`

## Common Development Commands

Frontend build:

```powershell
npm --prefix frontend run build
```

Frontend E2E:

```powershell
npm --prefix frontend run test:e2e
```

Run a focused E2E spec:

```powershell
npm --prefix frontend run test:e2e -- text-input-search-enable.regression-3.spec.ts
```

Backend regression test:

```powershell
python -m unittest backend.tests.test_playlist_batch_search_duplicate_regression
```

## Project Structure

```text
backend/     FastAPI app, API routes, background task management
core/        Shared search, matching, downloader, parser, source clients
frontend/    React web application
pyqt_ui/     Legacy desktop client
docs/        Supporting technical notes
```

## Recommended Entry Points

If you are new to the repo, start with:

- `frontend/src/pages/BatchDownloadPage.tsx`
- `backend/api/playlist.py`
- `backend/api/download.py`
- `core/downloader.py`

## Docs You May Want

- `CHANGELOG.md` for shipped changes
- `TODOS.md` for active follow-up work
- `CLAUDE.md` for contributor-oriented architecture notes
- `DESIGN.md` for UI direction and design context

## Recent Improvements

Recent work shipped in this repo includes:

- Cleaner Git history by removing generated runtime artifacts from version control
- Restored frontend production build health
- Batch-search regression fixes for text input enablement
- Safer handling when duplicate filtering leaves no songs to search
- QA fixes for routing and deprecated UI API usage

## Notes

- Some legacy files and scripts remain because the project is evolving from desktop-first to web-first.
- The default branch is now `main`, and older feature branches remain available for history/reference.

