"""
PyQt UI Configuration

此文件包含 PyQt 桌面端特定的配置。
核心共享配置从 core 模块导入，避免重复定义。
"""

import os
from pathlib import Path
from enum import Enum

# 从 core 导入共享配置
from core import (
    DEFAULT_SOURCES,
    SOURCE_LABELS,
    DOWNLOAD_DIR,
    LOG_DIR,
    BATCH_MAX_SONGS,
    BATCH_MATCH_SIMILARITY_THRESHOLD,
    BATCH_SEARCH_ALL_SOURCES,
    BATCH_MAX_CANDIDATES_PER_SOURCE,
    BATCH_STATUS_LABELS,
    MatchMode,
    MATCH_THRESHOLDS,
    DEFAULT_MATCH_THRESHOLD,
)

# 计算路径（用于 UI 显示等）
BASE_DIR = Path(__file__).parent.parent

# UI Settings
WINDOW_TITLE = "Music下载器"
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700

# Default Match Configuration (UI 特定)
DEFAULT_MATCH_MODE = MatchMode.STANDARD
DEFAULT_SIMILARITY_WEIGHTS = {"name": 0.5, "singer": 0.4, "album": 0.1}

# Match Mode Labels (for UI display)
MATCH_MODE_LABELS = {
    MatchMode.STRICT: "严格(≥90%)",
    MatchMode.STANDARD: "标准(≥60%)",
    MatchMode.LOOSE: "宽松(≥40%)",
    MatchMode.CUSTOM: "自定义",
}

# UI Style Constants
SIMILARITY_COLORS = {
    "high": "darkgreen",      # ≥80%
    "medium": "darkorange",   # 60-79%
    "low": "red",             # <60%
}

SIMILARITY_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.6,
}

BUTTON_STYLES = {
    "many_candidates": """
        QPushButton {
            background: #ff9800;
            color: white;
            border: 1px solid #f57c00;
            border-radius: 4px;
            padding: 2px 6px;
            font-weight: bold;
            font-size: 11px;
        }
        QPushButton:hover {
            background: #fb8c00;
            border: 1px solid #ef6c00;
        }
        QPushButton:pressed {
            background: #f57c00;
        }
    """,
    "medium_candidates": """
        QPushButton {
            border: 1px solid #2196F3;
            border-radius: 4px;
            padding: 2px 5px;
            background: #E3F2FD;
            color: #1976D2;
            font-size: 11px;
        }
        QPushButton:hover {
            background: #BBDEFB;
            border: 1px solid #1976D2;
        }
        QPushButton:pressed {
            background: #90CAF9;
        }
    """,
    "few_candidates": """
        QPushButton {
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 0px;
            background: #f5f5f5;
        }
        QPushButton:hover {
            background: #e0e0e0;
            border: 1px solid #999;
        }
        QPushButton:pressed {
            background: #d0d0d0;
        }
    """,
}

MENU_STYLES = """
    QMenu {
        border: 1px solid #ccc;
        padding: 5px;
    }
    QMenu::item {
        padding: 5px 30px 5px 20px;
        border: 1px solid transparent;
    }
    QMenu::item:selected {
        border-color: #3399ff;
        background: #e6f2ff;
    }
    QMenu::item:checked {
        font-weight: bold;
        color: #0066cc;
    }
"""

# Table Constants
BATCH_TABLE_HEADERS = ['☐', '#', '歌曲名', '歌手', '专辑', '源', '相似度']
SINGLE_TABLE_HEADERS = ['☐', '#', 'Song Name', 'Singer', 'Album', 'Size', 'Duration', 'Source']

# Checkbox Column Index
CHECKBOX_COL = 0
INDEX_COL = 1