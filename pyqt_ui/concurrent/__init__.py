"""并发模块 - 支持并发搜索和下载"""

from .result_collector import ThreadSafeResultCollector
from .search_runnable import SingleSongSearchRunnable, SearchRunnableSignals
from .download_runnable import SingleSongDownloadRunnable, DownloadRunnableSignals

__all__ = [
    'ThreadSafeResultCollector',
    'SingleSongSearchRunnable',
    'SearchRunnableSignals',
    'SingleSongDownloadRunnable',
    'DownloadRunnableSignals',
]
