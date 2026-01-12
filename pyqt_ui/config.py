"""Application Configuration"""

import os
from pathlib import Path
from enum import Enum

# Paths
BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / "musicdl_outputs"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
DOWNLOAD_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Music sources
DEFAULT_SOURCES = [
    "QQMusicClient",
    "NeteaseMusicClient",
    "KugouMusicClient",
    "KuwoMusicClient",
]

SOURCE_LABELS = {
    "QQMusicClient": "QQ Music",
    "NeteaseMusicClient": "Netease",
    "KugouMusicClient": "Kugou",
    "KuwoMusicClient": "Kuwo",
}

# UI Settings
WINDOW_TITLE = "Music下载器"
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700

# Batch Download Configuration
BATCH_MAX_SONGS = 200
BATCH_MATCH_SIMILARITY_THRESHOLD = 0.6

# 新增：批量搜索配置
BATCH_SEARCH_ALL_SOURCES = True
BATCH_MAX_CANDIDATES_PER_SOURCE = 5

BATCH_STATUS_LABELS = {
    "found": "已找到",
    "not_found": "未找到",
    "duplicate": "重复",
    "downloading": "下载中",
    "completed": "已完成",
    "failed": "失败",
}

# Match Mode Configuration
class MatchMode(Enum):
    """匹配模式枚举"""
    STRICT = "strict"      # ≥90%
    STANDARD = "standard"  # ≥60%
    LOOSE = "loose"        # ≥40%
    CUSTOM = "custom"      # 自定义

# Default Match Configuration
DEFAULT_MATCH_MODE = MatchMode.STANDARD
DEFAULT_MATCH_THRESHOLD = 0.60
DEFAULT_SIMILARITY_WEIGHTS = {"name": 0.7, "singer": 0.3}

# Preset Thresholds for Each Mode
MATCH_THRESHOLDS = {
    MatchMode.STRICT: 0.90,
    MatchMode.STANDARD: 0.60,
    MatchMode.LOOSE: 0.40,
}

# Match Mode Labels (for UI display)
MATCH_MODE_LABELS = {
    MatchMode.STRICT: "严格(≥90%)",
    MatchMode.STANDARD: "标准(≥60%)",
    MatchMode.LOOSE: "宽松(≥40%)",
    MatchMode.CUSTOM: "自定义",
}
