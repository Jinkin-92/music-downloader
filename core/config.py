"""
Core Configuration - 核心配置常量

此文件只包含与UI无关的核心配置。
UI相关配置保留在 pyqt_ui/config.py 中。
"""

import os
from pathlib import Path
from enum import Enum

# Paths - 使用项目根目录
BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / "musicdl_outputs"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
DOWNLOAD_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Music sources - 支持的音乐源
DEFAULT_SOURCES = [
    "QQMusicClient",
    "NeteaseMusicClient",
    "KugouMusicClient",
    "KuwoMusicClient",
    "MiguMusicClient",
    "Pjmp3Client",    # 新增：pjmp3.com 备用源
]

# Source labels for display
SOURCE_LABELS = {
    "QQMusicClient": "QQ音乐",
    "NeteaseMusicClient": "网易云",
    "KugouMusicClient": "酷狗",
    "KuwoMusicClient": "酷我",
    "MiguMusicClient": "咪咕",
    "Pjmp3Client": "pjmp3",
}

# Batch Download Configuration
BATCH_MAX_SONGS = 200
BATCH_MATCH_SIMILARITY_THRESHOLD = 0.6

# Duration Filter Configuration - 过滤试听片段
MIN_DURATION_SECONDS = 35  # 最小时长（秒），过滤35秒以下的试听片段

# Download History Database Configuration
HISTORY_DB_PATH = BASE_DIR / "data" / "download_history.db"

# Batch Search Configuration
BATCH_SEARCH_ALL_SOURCES = True
BATCH_MAX_CANDIDATES_PER_SOURCE = 5


class MatchMode(Enum):
    """匹配模式枚举"""
    STRICT = "strict"      # ≥90%
    STANDARD = "standard"  # ≥60%
    LOOSE = "loose"        # ≥40%
    CUSTOM = "custom"      # 自定义


# Default Match Configuration
DEFAULT_MATCH_MODE = MatchMode.STANDARD
DEFAULT_MATCH_THRESHOLD = 0.60
DEFAULT_SIMILARITY_WEIGHTS = {"name": 0.5, "singer": 0.4, "album": 0.1}

# Preset Thresholds for Each Mode
MATCH_THRESHOLDS = {
    MatchMode.STRICT: 0.90,
    MatchMode.STANDARD: 0.60,
    MatchMode.LOOSE: 0.40,
}

# Status labels for batch download
BATCH_STATUS_LABELS = {
    "found": "已找到",
    "not_found": "未找到",
    "duplicate": "重复",
    "downloading": "下载中",
    "completed": "已完成",
    "failed": "失败",
}