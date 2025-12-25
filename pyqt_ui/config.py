"""Application Configuration"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / 'musicdl_outputs'
LOG_DIR = BASE_DIR / 'logs'

# Ensure directories exist
DOWNLOAD_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Music sources
DEFAULT_SOURCES = [
    'QQMusicClient',
    'NeteaseMusicClient',
    'KugouMusicClient',
    'KuwoMusicClient'
]

SOURCE_LABELS = {
    'QQMusicClient': 'QQ Music',
    'NeteaseMusicClient': 'Netease',
    'KugouMusicClient': 'Kugou',
    'KuwoMusicClient': 'Kuwo'
}

# UI Settings
WINDOW_TITLE = 'Music Downloader'
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700
