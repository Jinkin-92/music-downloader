# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **desktop music downloader** built with Python, PyQt6, and musicdl - providing a graphical interface to search and download music from multiple Chinese platforms (QQ Music, Netease, Kugou, Kuwo).

**Current Status**: Production-ready v1.0.0 with full-featured PyQt6 desktop UI

## Technology Stack

- **UI Framework**: PyQt6 (desktop application)
- **Music Engine**: musicdl (multi-platform music search and download)
- **Concurrency**: QThread for background operations
- **Logging**: Python logging module with file and console handlers

## Architecture

### Core Components

The application follows a **threaded MVC pattern** with three main layers:

```
pyqt_ui/
├── main.py              # MainWindow (View/Controller) - UI logic and event handling
├── workers.py           # QThread workers (Model) - Async search/download operations
├── music_downloader.py  # MusicDownloader (Service) - musicdl singleton wrapper
└── config.py            # Configuration constants
```

### Data Flow

1. **Search Flow**:
   - User input → MainWindow.on_search_clicked()
   - SearchWorker thread created → MusicDownloader.search()
   - musicdl returns SongInfo objects → converted to dicts via _songinfo_to_dict()
   - Results emitted via pyqtSignal → MainWindow.populate_results_table()

2. **Download Flow**:
   - User selects songs → MainWindow.start_download()
   - DownloadWorker thread created → MusicDownloader.download()
   - SongInfo objects extracted from dicts → musicdl.download()
   - Progress signals emitted → MainWindow updates progress bar

### Critical Architecture Pattern: musicdl Integration

**musicdl returns SongInfo objects, NOT dicts**:
- Search returns: `{platform: [SongInfo, ...]}`
- Access properties with `getattr(song, 'property', default)` NOT `song.get('property')`
- Store original SongInfo in dict's `'song_info_obj'` key for later download

```python
# Correct pattern from music_downloader.py:77-88
def _songinfo_to_dict(self, song_info):
    return {
        'song_name': getattr(song_info, 'song_name', ''),
        'singers': getattr(song_info, 'singers', ''),
        # ... other fields
        'song_info_obj': song_info  # Critical: keep reference for download
    }
```

### Thread Safety with Singleton Pattern

`MusicDownloader` uses **double-checked locking** to ensure only one MusicClient instance exists:
- Thread-safe singleton initialization via `_lock` (lines 17-23)
- Workers create own instances but share underlying `_client`
- Prevents race conditions during concurrent searches/downloads

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

### Testing Commands

```bash
# Test search functionality directly
python test_simple_search.py

# Test search and download
python test_search_download.py

# Test download only
python test_download.py

# Verify GUI launch
python verify_gui.py
```

### Viewing Logs

Logs are written to `logs/app.log` (auto-created on first run):
```bash
# Windows
type logs\app.log

# Unix
cat logs/app.log
```

## Important Implementation Details

### UI Table Data Storage (main.py:219-275)

The QTableWidget stores song data in column 0 (checkbox column) using `UserRole`:
- `checkbox_item.setData(Qt.ItemDataRole.UserRole, song_dict)`
- Retrieve later with `item.data(Qt.ItemDataRole.UserRole)`
- Each row represents one song with columns: ☐ | # | Name | Singer | Album | Size | Duration | Source

### Checkbox Batch Operations (main.py:442-543)

The application supports sophisticated checkbox-based batch selection:
- `get_checked_count()`: Count checked rows
- `get_checked_songs()`: Extract all checked song dictionaries
- `select_all()`: Check all rows
- `uncheck_all()`: Uncheck all rows
- `on_invert_selection()`: Toggle all checkboxes
- `on_header_clicked()`: Toggle all when clicking header ☐

### Progress Tracking (main.py:360-429)

Download progress uses a simple percentage-based system:
- Progress bar shows 0-100% based on `(i / total_songs) * 100`
- **Limitation**: Actual musicdl download progress is not exposed - the bar updates per song, not per byte
- Status message shows current song being downloaded

### Signal/Slot Connections (main.py + workers.py)

PyQt6 signals connect worker threads to UI:

**SearchWorker** (workers.py:9-43):
- `search_started` → on_search_started()
- `search_progress(str)` → on_search_progress() - updates status label
- `search_finished(dict)` → on_search_finished() - populates table
- `search_error(str)` → on_search_error() - shows error message

**DownloadWorker** (workers.py:46-82):
- `download_started` → on_download_started()
- `download_progress(str, int)` → on_download_progress() - updates progress bar
- `download_finished(list)` → on_download_finished() - shows completion dialog
- `download_error(str)` → on_download_error() - shows error dialog

## Configuration

### Music Sources (config.py:15-20)

Four platforms supported:
- `QQMusicClient`: QQ Music (腾讯音乐)
- `NeteaseMusicClient`: Netease Cloud Music (网易云音乐)
- `KugouMusicClient`: Kugou Music (酷狗音乐)
- `KuwoMusicClient`: Kuwo Music (酷我音乐)

Users can toggle sources via checkboxes in the UI.

### Download Directory (config.py:6-7)

Default: `musicdl_outputs/` (created automatically in project root)
- Absolute path used to avoid Windows encoding issues
- File naming: `{song_name} - {singers}.{ext}`

## Windows-Specific Considerations

### Path Encoding (config.py:5-12)

Uses `pathlib.Path` for cross-platform compatibility:
```python
BASE_DIR = Path(__file__).parent.parent  # Auto-detects project root
DOWNLOAD_DIR = BASE_DIR / 'musicdl_outputs'
```

**Avoid**: `os.getcwd()` or relative paths that can break with different working directories

### Logging Setup (main.py:17-26)

File handler uses UTF-8 encoding to handle Chinese characters:
```python
logging.FileHandler(LOG_DIR / 'app.log', encoding='utf-8')
```

### Batch Launcher (启动音乐下载器.bat)

Sets UTF-8 code page for proper Chinese character display:
```batch
chcp 65001 >nul
```

## Common Tasks

### Adding a New Music Source

1. Edit `config.py`: Add to `DEFAULT_SOURCES` and `SOURCE_LABELS`
2. Restart application - no other code changes needed

### Modifying Table Columns

1. Update column count in `main.py:106`: `self.results_table.setColumnCount(N)`
2. Update header labels in `main.py:107-109`
3. Update `populate_results_table()` to populate new column
4. Adjust column widths in `main.py:114-115`

### Changing Download Directory

Edit `config.py:7`:
```python
DOWNLOAD_DIR = BASE_DIR / 'your_custom_dir'
```

### Customizing MusicClient Initialization

Edit `music_downloader.py:30-44` to pass additional config to musicdl:
```python
self._client = MusicClient(
    music_sources=DEFAULT_SOURCES,
    init_music_clients_cfg={
        source: {'work_dir': str(DOWNLOAD_DIR), 'your_option': value}
        for source in DEFAULT_SOURCES
    }
)
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

**Problem**: Download fails silently
- Check `logs/app.log` for errors
- Verify disk space
- Some songs have copyright protection

**Problem**: UI freezes during search/download
- Workers should prevent this - verify QThread is running
- Check if worker signals are properly connected

## Development Notes

### No Flask/Web Components

The current CLAUDE.md mentions Flask and web architecture - **this is outdated**. The project is a pure PyQt6 desktop application with no web server.

### Batch Download Feature (pyqt_ui/batch/)

A `batch/` subdirectory exists but is not integrated into the main UI. This may be experimental or planned functionality for parsing batch download lists.

### Git Status Context

The repository shows many deleted files (app/, templates/, old test files). These were likely from an earlier Flask/web version that was replaced with the PyQt6 desktop UI.

---

## Phase 2: 批量下载 UI 组件实施状态

### 当前进度：Cycle 1 - Green阶段受阻

**已完成工作**：
- ✅ Phase 1: 基础架构（BatchParser, SongMatcher, DuplicateChecker, 配置）- 100%测试覆盖
- ✅ Cycle 1 - Red阶段：创建测试 `tests/ui/test_main_window_tabs.py`
  - 测试检查：`assert hasattr(window, 'mode_tab_widget')`
  - 测试已确认失败：`AssertionError: assert False`

**当前任务**：
- 🔄 Cycle 1 - Green阶段：需要实现 `self.mode_tab_widget = QTabWidget()`
  - 位置：`pyqt_ui/main.py` 的 `setup_ui()` 方法（第54行 main_layout 创建之后）
  - 需要添加的代码：
    ```python
    self.mode_tab_widget = QTabWidget()
    main_layout.addWidget(self.mode_tab_widget)
    ```

**遇到的问题 - TDD Guard阻塞**：

```
问题：Edit工具被TDD guard hook反复阻止
错误信息：Premature implementation - adding new UI component (mode_tab_widget) without evidence of a failing test

实际情况：
1. ✅ 测试文件已创建：tests/ui/test_main_window_tabs.py
2. ✅ 测试已运行并确认失败（多次运行pytest）
3. ✅ 测试失败原因明确：hasattr(window, 'mode_tab_widget') 返回 False
4. ❌ 但TDD guard仍然阻止编辑，声称"没有测试输出显示失败"

尝试的解决方法：
- 多次运行测试显示失败输出
- 在Edit前立即运行pytest
- 使用TodoWrite记录TDD状态
- 检查测试文件内容
- 所有尝试均被guard阻止
```

**下次继续时请先询问用户**：

> ⚠️ **继续Phase 2实施前，请先向用户确认以下问题**：
>
> 1. TDD guard hook是否需要调整配置或临时禁用？
> 2. 是否应该尝试其他方法绕过guard限制（如创建外部脚本修改代码）？
> 3. 还是应该继续尝试满足guard的要求（尽管已经证明测试存在且失败）？
>
> **上下文**：测试已创建并确认失败，但guard无法识别测试输出，导致无法进入Green阶段实施最小代码。

**实施计划文件**：
- 详细计划：`C:\Users\DELL\.claude\plans\happy-snuggling-kettle.md`
- 包含8个TDD cycles的完整规格

**下一步任务**（Cycle 1完成后）：
1. Cycle 2: 重构单曲模式到标签页内容 (40分钟)
2. Cycle 3: 批量模式基础UI组件 (45分钟)
3. Cycle 4: 共享音乐源选择 (30分钟)
4. Cycle 5-8: 批量表格、Worker线程、集成、操作

**文件结构**：
```
pyqt_ui/
├── main.py              # 需要修改：添加QTabWidget
├── workers.py           # 需要修改：Cycle 6添加BatchSearchWorker
└── config.py            # 可能需要修改：添加标签页常量

tests/ui/
├── __init__.py          # ✅ 已创建
└── test_main_window_tabs.py  # ✅ 已创建（第一个断言）
```

---
**文档版本**: 2.1
**最后更新**: 2025-12-26 (Phase 2 Cycle 1 Green阶段受阻)
**暂停原因**: TDD guard阻止代码编辑
