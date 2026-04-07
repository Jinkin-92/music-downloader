"""
Core模块 - 音乐下载核心业务逻辑

此模块包含与UI无关的核心业务逻辑，可被后端(FastAPI)和桌面端(PyQt6)共同使用。

模块结构:
- config.py: 配置常量
- downloader.py: 音乐下载器
- models.py: 数据模型
- parser.py: 批量文本解析器
- matcher.py: 相似度匹配算法
- playlist.py: 歌单解析（重导出）
"""

from .config import (
    DEFAULT_SOURCES,
    SOURCE_LABELS,
    DOWNLOAD_DIR,
    LOG_DIR,
    MatchMode,
    MATCH_THRESHOLDS,
    DEFAULT_MATCH_THRESHOLD,
    DEFAULT_SIMILARITY_WEIGHTS,
    BATCH_MAX_SONGS,
    BATCH_MATCH_SIMILARITY_THRESHOLD,
    BATCH_SEARCH_ALL_SOURCES,
    BATCH_MAX_CANDIDATES_PER_SOURCE,
    BATCH_STATUS_LABELS,
    CDP_SOURCES,
)
from .models import MatchCandidate, BatchSongMatch, BatchSearchResult, MatchSource
from .parser import BatchParser
from .matcher import SongMatcher
from .downloader import MusicDownloader
from .playlist import PlaylistParserFactory, PlaylistSong, BasePlaylistParser

__all__ = [
    # Config
    "DEFAULT_SOURCES",
    "SOURCE_LABELS",
    "DOWNLOAD_DIR",
    "LOG_DIR",
    "MatchMode",
    "MATCH_THRESHOLDS",
    "DEFAULT_MATCH_THRESHOLD",
    "BATCH_MAX_SONGS",
    "BATCH_MATCH_SIMILARITY_THRESHOLD",
    "BATCH_SEARCH_ALL_SOURCES",
    "BATCH_MAX_CANDIDATES_PER_SOURCE",
    "BATCH_STATUS_LABELS",
    "CDP_SOURCES",
    # Models
    "MatchCandidate",
    "BatchSongMatch",
    "BatchSearchResult",
    "MatchSource",
    # Services
    "BatchParser",
    "SongMatcher",
    "MusicDownloader",
    # Playlist
    "PlaylistParserFactory",
    "PlaylistSong",
    "BasePlaylistParser",
]