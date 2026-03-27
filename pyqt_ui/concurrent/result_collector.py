"""线程安全的搜索结果收集器"""
from PyQt6.QtCore import QMutex, QMutexLocker
from typing import Dict
from core.models import BatchSongMatch
import logging

logger = logging.getLogger(__name__)


class ThreadSafeResultCollector:
    """线程安全地收集批量搜索结果

    在多线程并发搜索场景下，多个线程需要同时写入搜索结果。
    此类使用QMutex确保线程安全，避免竞态条件。
    """

    def __init__(self, total_songs: int):
        """初始化结果收集器

        Args:
            total_songs: 总歌曲数（用于进度计算）
        """
        self._mutex = QMutex()
        self._matches: Dict[str, BatchSongMatch] = {}
        self._completed_count = 0
        self._total_songs = total_songs

        logger.debug(f"ThreadSafeResultCollector initialized for {total_songs} songs")

    def add_match(self, original_line: str, song_match: BatchSongMatch):
        """线程安全地添加匹配结果

        Args:
            original_line: 原始行文本（作为key）
            song_match: 匹配结果对象
        """
        with QMutexLocker(self._mutex):
            self._matches[original_line] = song_match
            self._completed_count += 1

            logger.debug(
                f"Added match for '{original_line}' "
                f"({self._completed_count}/{self._total_songs} completed)"
            )

    def get_result(self) -> Dict[str, BatchSongMatch]:
        """获取所有结果（线程安全）

        Returns:
            匹配结果字典的副本（避免外部修改影响内部状态）
        """
        with QMutexLocker(self._mutex):
            return dict(self._matches)

    def get_progress(self) -> tuple:
        """获取当前进度（线程安全）

        Returns:
            (completed_count, total_songs) 元组
        """
        with QMutexLocker(self._mutex):
            return self._completed_count, self._total_songs

    def get_match_count(self) -> int:
        """获取已匹配数量（线程安全）

        Returns:
            has_match=True 的歌曲数量
        """
        with QMutexLocker(self._mutex):
            return sum(1 for match in self._matches.values() if match.has_match)
