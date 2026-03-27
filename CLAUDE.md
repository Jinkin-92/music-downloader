# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **desktop music downloader** built with Python, PyQt6, and musicdl - providing a graphical interface to search, batch download, and import playlists from multiple Chinese platforms (QQ Music, Netease, Kugou, Kuwo).

**Current Status**: Production-ready v1.1.0 with full-featured PyQt6 desktop UI

**Key Features**:
- Single song search across multiple platforms
- Batch download mode with intelligent matching
- Playlist import (Netease, QQ Music)
- Multi-source fallback for copyright protection
- Concurrent search and download (5x/4x speedup)

## Technology Stack

- **UI Framework**: PyQt6 (desktop application)
- **Music Engine**: musicdl (multi-platform music search and download)
- **Concurrency**: QThread, QThreadPool for background operations
- **Data Models**: dataclasses, type hints
- **Logging**: Python logging module with file and console handlers

## Architecture Overview

### High-Level Architecture

The application follows a **threaded MVC pattern** with modular design:

```
┌─────────────────────────────────────────────────────────────┐
│                      MainWindow (View/Controller)            │
│  ├─ Single Search Tab    ├─ Batch Download Tab          │
│  └─ Playlist Import Tab  └─ ...                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Signals/Slots
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Workers (Model)                          │
│  ├─ SearchWorker           │  ConcurrentSearchWorker      │
│  ├─ DownloadWorker         │  ConcurrentDownloadWorker    │
│  └─ PlaylistParseWorker    │  ...                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Services (Business Logic)                  │
│  ├─ MusicDownloader        │  BatchParser                │
│  ├─ SongMatcher            │  PlaylistParserFactory      │
│  └─ DuplicateChecker       │  ThreadSafeResultCollector   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Libraries                        │
│  └─ musicdl (MusicClient)                                   │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
pyqt_ui/
├── main.py                   # MainWindow - UI logic and event handling
├── workers.py                # QThread workers for async operations
├── music_downloader.py       # MusicDownloader - musicdl singleton wrapper
├── config.py                 # Configuration constants
│
├── batch/                    # Batch download module
│   ├── models.py             # BatchSongMatch, MatchCandidate, BatchSearchResult
│   ├── parser.py             # BatchParser - text parsing
│   ├── matcher.py            # SongMatcher - similarity scoring
│   └── duplicate_checker.py  # DuplicateChecker - song deduplication
│
├── playlist/                 # Playlist import module
│   ├── factory.py            # PlaylistParserFactory - parser selection
│   ├── base.py               # PlaylistSong dataclass, base parser
│   ├── netease.py            # NeteasePlaylistParser
│   └── workers.py            # PlaylistParseWorker
│
└── concurrent/               # Concurrent processing module
    ├── result_collector.py   # ThreadSafeResultCollector
    ├── search_runnable.py    # SingleSongSearchRunnable
    └── download_runnable.py  # SingleSongDownloadRunnable (with fallback)
```

## Critical Architecture Patterns

### 1. musicdl Integration (MusicDownloader)

**Core Principle**: musicdl returns `SongInfo` objects, NOT dicts

```python
# Correct pattern from music_downloader.py:60-88
def _songinfo_to_dict(self, song_info):
    return {
        'song_name': getattr(song_info, 'song_name', ''),
        'singers': getattr(song_info, 'singers', ''),
        'album': getattr(song_info, 'album', ''),
        # ... other fields
        'song_info_obj': song_info  # Critical: keep reference for download
    }
```

**Why This Matters**:
- Access properties with `getattr(song, 'property', default)` NOT `song.get('property')`
- Store original `SongInfo` in dict's `'song_info_obj'` key for later download
- Ensures musicdl can download using the correct object

### 2. Thread Safety with Singleton Pattern

`MusicDownloader` uses **double-checked locking**:

```python
# From music_downloader.py:17-30
_lock = Lock()

def __init__(self):
    if not hasattr(self, '_client'):
        with MusicDownloader._lock:
            if not hasattr(self, '_client'):
                self._client = MusicClient(...)
```

**Benefits**:
- Thread-safe singleton initialization
- Workers create own instances but share underlying `_client`
- Prevents race conditions during concurrent searches/downloads

### 3. Concurrent Search Architecture (v1.1.0)

**ConcurrentSearchWorker** uses QThreadPool for parallel searches:

```
Parse Batch Text (159 songs)
        │
        ▼
Create ThreadSafeResultCollector
        │
        ▼
QThreadPool (max_workers=5)
        │
        ├─ Thread 1: Search song 1
        ├─ Thread 2: Search song 2
        ├─ Thread 3: Search song 3
        ├─ Thread 4: Search song 4
        └─ Thread 5: Search song 5
        │
        ▼ (repeat for all songs)
        │
        ▼
waitForDone() → Collect Results → Return BatchSearchResult
```

**Performance**: 5x speedup (400s → 80s for 100 songs)

### 4. Multi-Source Fallback Architecture (v1.1.0)

**Problem**: 403 Forbidden errors (copyright protection) caused 70% failure rate

**Solution**: Automatic source switching on 403 errors

```
Download 'Song X' from NeteaseMusicClient
        │
        ▼
    403 Error?
        │
        ├─ YES → Check fallback_candidates
        │        │
        │        ├─ Has candidates?
        │        │   │
        │        │   ├─ YES → Switch to next source (QQMusicClient)
        │        │   │         └─ Reset retry counter → Download
        │        │   │
        │        │   └─ NO → Mark as failed
        │        │
        │        └─ Continue normal retry
        │
        └─ NO → Download complete
```

**Implementation**:
- `populate_batch_results_table()`: Stores `_fallback_candidates` in song_dict
- `SingleSongDownloadRunnable`: Detects 403, switches source, resets retry counter
- **Result**: 30% → 70-80% success rate (2.3-2.7x improvement)

### 5. Data Flow Patterns

#### Search Flow (Single Song)
```
User Input → MainWindow.on_search_clicked()
    ↓
SearchWorker QThread created
    ↓
MusicDownloader.search(keyword, sources)
    ↓
musicdl returns {platform: [SongInfo, ...]}
    ↓
Convert to dicts via _songinfo_to_dict()
    ↓
Emit search_finished signal
    ↓
MainWindow.populate_results_table()
```

#### Batch Search Flow (v1.1.0)
```
User Input → BatchParseWorker.parse()
    ↓
Extract songs from text/playlist
    ↓
ConcurrentSearchWorker (QThreadPool, 5 workers)
    ↓
SingleSongSearchRunnable per song
    ↓
ThreadSafeResultCollector collects results
    ↓
Return BatchSearchResult
    ↓
MainWindow.populate_batch_results_table()
    ├─ Display similarity scores with colors
    ├─ Add ▼ buttons for candidate switching
    └─ Store _fallback_candidates for 403 handling
```

#### Download Flow with Fallback (v1.1.0)
```
User Selects Songs → get_checked_batch_songs()
    ↓
Extract song_dict with _fallback_candidates
    ↓
ConcurrentDownloadWorker (QThreadPool, 4 workers)
    ↓
SingleSongDownloadRunnable per song
    ├─ Try primary source
    ├─ 403 error?
    │   ├─ YES → Try fallback_candidates[0]
    │   ├─ 403 error again?
    │   │   └─ Try fallback_candidates[1]
    │   └─ Continue until success or no candidates
    └─ Emit success/error signal
    ↓
MainWindow.on_download_finished()
```

## Important Implementation Details

### UI Table Data Storage (main.py)

**Single Search Table**:
- Stores song data in column 0 (checkbox column) using `UserRole`
- `checkbox_item.setData(Qt.ItemDataRole.UserRole, song_dict)`
- Columns: ☐ | # | Name | Singer | Album | Size | Duration | Source

**Batch Results Table** (v1.1.0):
- Same storage pattern
- **Additional**: `_fallback_candidates` list in song_dict
- Similarity widget with ▼ button for candidate switching
- Color-coded similarity scores (green≥80%, yellow 60-79%, red<60%)

### Similarity Matching Algorithm (batch/matcher.py:42-84)

**Formula**: `(name_sim * 0.6) + (singer_sim * 0.3) + (album_sim * 0.1)`

```python
def find_best_match(parsed_song, all_results):
    name_sim = calculate_similarity(query_name, result_name)
    singer_sim = calculate_similarity(query_singer, result_singer)
    album_sim = calculate_similarity(query_album, result_album) if query_album else 0.0

    combined_score = (name_sim * 0.6) + (singer_sim * 0.3) + (album_sim * 0.1)

    return best_match if combined_score >= SIMILARITY_THRESHOLD else None
```

**Threshold**: 60% (configurable in `SongMatcher.SIMILARITY_THRESHOLD`)

### Playlist Import Architecture (playlist/)

**Factory Pattern** for parser selection:

```python
# From factory.py
class PlaylistParserFactory:
    @staticmethod
    def get_parser(url):
        if 'music.163.com' in url:
            return NeteasePlaylistParser()
        elif 'y.qq.com' in url:
            return QQMusicPlaylistParser()
        else:
            raise ValueError(f"Unsupported playlist URL: {url}")
```

**Data Flow**:
```
User Pastes URL → PlaylistParseWorker
    ↓
PlaylistParserFactory.get_parser(url)
    ↓
parser.parse() → Returns [PlaylistSong, ...]
    ↓
MainWindow.populate_playlist_table()
    ↓
User clicks "批量搜索" → ConcurrentSearchWorker
    ↓
MainWindow.populate_batch_results_table()
```

### Signal/Slot Connections (main.py + workers.py)

**SearchWorker** (workers.py:16-51):
- `search_started` → on_search_started()
- `search_progress(str)` → on_search_progress()
- `search_finished(dict)` → on_search_finished()
- `search_error(str)` → on_search_error()

**ConcurrentSearchWorker** (workers.py:264-402):
- `search_started` → on_batch_search_started()
- `search_progress(str, int, int)` → on_batch_search_progress()
- `search_finished(BatchSearchResult)` → on_batch_search_finished()
- `search_error(str)` → on_batch_search_error()

**ConcurrentDownloadWorker** (workers.py:404-522):
- `download_started` → on_download_started()
- `download_progress(str, int)` → on_download_progress()
- `download_finished(list)` → on_download_finished()
- `download_error(str)` → on_download_error()

## Configuration

### Music Sources (config.py)

**Supported Platforms**:
```python
DEFAULT_SOURCES = [
    'QQMusicClient',
    'NeteaseMusicClient',
    'KugouMusicClient',
    'KuwoMusicClient',
]

SOURCE_LABELS = {
    'QQMusicClient': 'QQ音乐',
    'NeteaseMusicClient': '网易云',
    'KugouMusicClient': '酷狗',
    'KuwoMusicClient': '酷我',
}
```

**Adding a New Source**:
1. Add to `DEFAULT_SOURCES` and `SOURCE_LABELS` in `config.py`
2. Ensure musicdl supports the source
3. Update UI checkboxes in `main.py`
4. Test search and download functionality

### Download Directory (config.py)

```python
BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / 'musicdl_outputs'
```

**File Naming**: `{song_name} - {singers}.{ext}`

### Concurrency Settings (v1.1.0)

**ConcurrentSearchWorker** (workers.py:299):
```python
self.search_concurrency = 5  # 5 parallel searches
```

**ConcurrentDownloadWorker** (workers.py:430):
```python
self.download_concurrency = 4  # 4 parallel downloads
```

**Tuning Guidelines**:
- Too high → API rate limiting, network congestion
- Too low → Slower performance
- Current values optimized for typical broadband connections

## Running the Application

### Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run application (module form - preferred)
python -m pyqt_ui.main

# Run application (direct form)
python pyqt_ui/main.py

# Run with batch launcher (Windows)
启动音乐下载器.bat
```

### Viewing Logs

Logs are written to `logs/app.log` (auto-created on first run):
```bash
# Windows
type logs\app.log

# Unix
cat logs/app.log
```

**Log Levels**:
- INFO: Normal operations (search, download, progress)
- WARNING: Non-critical issues (403 errors, retries)
- ERROR: Critical failures (download failed, parsing errors)
- DEBUG: Detailed diagnostics (enable in main.py:18)

## Common Tasks

### Adding a New Music Source

1. Edit `config.py`: Add to `DEFAULT_SOURCES` and `SOURCE_LABELS`
2. Restart application - no other code changes needed
3. Test search and download functionality

### Modifying Similarity Threshold

Edit `pyqt_ui/batch/matcher.py`:
```python
SIMILARITY_THRESHOLD = 0.60  # Default: 60%
```

**Guidelines**:
- Higher (0.70-0.80): More strict, fewer false positives
- Lower (0.50-0.60): More lenient, more matches but lower accuracy

### Adjusting Concurrency

**Search Concurrency**: Edit `workers.py:299`
```python
self.search_concurrency = 5  # Try 3-8 for different results
```

**Download Concurrency**: Edit `workers.py:430`
```python
self.download_concurrency = 4  # Try 2-6 for different results
```

**Performance Impact**:
- Search: 5 workers → 80s for 100 songs
- Download: 4 workers → 375s for 100 songs

## Windows-Specific Considerations

### Path Encoding

Uses `pathlib.Path` for cross-platform compatibility:
```python
BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / 'musicdl_outputs'
```

**Avoid**: `os.getcwd()` or relative paths

### Logging Setup

File handler uses UTF-8 encoding for Chinese characters:
```python
logging.FileHandler(LOG_DIR / 'app.log', encoding='utf-8')
```

### Batch Launcher

`启动音乐下载器.bat` sets UTF-8 code page:
```batch
chcp 65001 >nul
python -m pyqt_ui.main
```

## Debugging

### Enable Verbose Logging

Change log level in `main.py:18`:
```python
level=logging.DEBUG  # More detailed output
```

### Check musicdl Directly

```python
from musicdl.musicdl import MusicClient
client = MusicClient()
results = client.search("test song")
# Returns dict of {platform: [SongInfo, ...]}
```

### Common Issues

**Problem**: Search returns no results
- Check network connection
- Try different keywords
- Verify selected sources in UI
- Check `logs/app.log` for API errors

**Problem**: Download fails with 403
- **Expected behavior**: Auto-switch to other sources (v1.1.0)
- Check if fallback candidates exist
- Verify `_fallback_candidates` in song_dict
- All sources failed → Song likely under copyright protection

**Problem**: Batch search inaccurate matching
- Adjust similarity threshold
- Use ▼ button to switch candidates
- Try selecting more music sources
- Check input format (use `歌名 - 歌手`)

**Problem**: UI freezes during operations
- Workers should prevent this - verify QThread is running
- Check if worker signals are properly connected
- Look for blocking operations in main thread

**Problem**: Playlist parsing fails
- Verify URL format is correct
- Check if playlist is public (not private)
- Confirm platform is supported (Netease, QQ Music)
- Check `logs/app.log` for parsing errors

## Performance Optimizations

### Concurrent Search (v1.1.0)

**Before**: Sequential search, ~400s for 100 songs
**After**: Parallel search (5 workers), ~80s for 100 songs
**Speedup**: 5x

**Implementation**: `ConcurrentSearchWorker` using QThreadPool

### Concurrent Download (v1.1.0)

**Before**: Sequential download, ~1500s for 100 songs
**After**: Parallel download (4 workers), ~375s for 100 songs
**Speedup**: 4x

**Implementation**: `ConcurrentDownloadWorker` using QThreadPool

### Multi-Source Fallback (v1.1.0)

**Before**: 30% success rate (45/150 songs)
**After**: 70-80% success rate (105-120/150 songs)
**Improvement**: 2.3-2.7x

**Implementation**: `_fallback_candidates` + 403 detection in `SingleSongDownloadRunnable`

## Development Notes

### Completed Features

- [x] Phase 1: Batch download architecture (parser, matcher, duplicate checker)
- [x] Phase 2: Batch download UI components
- [x] Phase 3: Playlist import (Netease, QQ Music)
- [x] Phase 4: Concurrent search and download optimization
- [x] Phase 5: Playlist import UI integration
- [x] Multi-source fallback mechanism (403 error handling)

### Known Limitations

1. **Playlist Support**: Only Netease and QQ Music (plan to add Kugou, Kuwo)
2. **Copyright Protection**: Some songs unavailable on all platforms
3. **Match Accuracy**: Similarity scoring may not be perfect for edge cases
4. **Network Dependency**: Requires active internet connection
5. **Platform Limits**: Some platforms may have rate limits

### Testing

**Unit Tests**: Located in `tests/`
- `tests/batch/` - Batch download module tests
- `tests/playlist/` - Playlist import tests
- `tests/ui/` - UI component tests

**Manual Testing Checklist**:
- [ ] Single song search on all platforms
- [ ] Batch download with text input
- [ ] Playlist import (Netease, QQ Music)
- [ ] Similarity matching accuracy
- [ ] Candidate switching (▼ button)
- [ ] Multi-source fallback (403 errors)
- [ ] Concurrent performance
- [ ] Error handling and recovery

## Future Enhancements

See `README.md` roadmap section:
- v1.2.0: Spotify support, download history, lyrics
- v1.3.0: Docker support, more playlist platforms, tag editing

---

## Testing Guidelines

### IMPORTANT: Web端E2E测试要求

**测试原则**：
- **必须使用真实浏览器进行Web UI测试**
- **禁止仅测试后端API而跳过前端交互**
- **所有用户报告的问题必须通过Web UI验证修复**

### E2E测试标准

**运行完整的Web端测试**：
```bash
# 确保前后端都在运行
# 后端: http://localhost:8003
# 前端: http://localhost:5173

# 运行完整E2E测试
node e2e_test_playlist.js
```

**E2E测试验证项**：
1. ✓ 音乐源默认选择（网易云、QQ音乐、酷狗、酷我全部选中）
2. ✓ 相似度显示正常（无NaN%）
3. ✓ 下载按钮在匹配结果表格下方
4. ✓ 下载路径输入框存在且可用
5. ✓ 完整下载流程可执行

### 测试文件类型

| 文件类型 | 用途 | 是否验证Web UI |
|---------|------|-----------------|
| `e2e_test_playlist.js` | **完整E2E测试** | ✅ 是 |
| `test_full_flow.py` | 后端API测试 | ❌ 否 |
| `test_sse_stream.py` | SSE流测试 | ❌ 否 |

**只有 `e2e_test_playlist.js` 的结果才算作正式测试通过**

### 修复验证流程

**用户报告问题时**：
1. 在 `e2e_test_playlist.js` 中添加测试用例
2. 运行测试确认问题
3. 修复代码
4. **再次运行E2E测试确认修复**
5. 只有E2E测试通过才算修复完成

### 测试闭环要求

**所有修复必须满足**：
```bash
# 1. 修复代码
# 2. 重启服务
# 3. 运行E2E测试
node e2e_test_playlist.js

# 4. 确认所有测试通过
# 5. 标记任务完成
```

**违反测试闭环的示例**：
- ❌ "后端API测试通过" → 前端UI未验证
- ❌ "手动测试看起来OK" → 无自动化测试
- ❌ "逻辑应该没问题" → 未实际验证

---

**Document Version**: 3.1
**Last Updated**: 2026-02-09 (Web E2E Testing Requirements Added)

<!-- gitnexus:start -->
# GitNexus MCP

This project is indexed by GitNexus as **music-downloader** (2102 symbols, 5193 relationships, 160 execution flows).

## Always Start Here

1. **Read `gitnexus://repo/{name}/context`** — codebase overview + check index freshness
2. **Match your task to a skill below** and **read that skill file**
3. **Follow the skill's workflow and checklist**

> If step 1 warns the index is stale, run `npx gitnexus analyze` in the terminal first.

## Skills

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
