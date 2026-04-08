"""
SongInfo 缓存模块

解决 SongInfo 对象无法 JSON 序列化的问题：
- 搜索时生成唯一 song_id，缓存 SongInfo 对象
- 返回给前端的数据包含 song_id
- 下载时通过 song_id 从缓存获取原始 SongInfo 对象
"""
import threading
import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class SongInfoCache:
    """
    SongInfo 对象缓存

    线程安全的 LRU 缓存，存储搜索结果中的 SongInfo 对象。
    支持过期清理，默认保留 2 小时。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache: Dict[str, Dict[str, Any]] = {}
                    cls._instance._max_size = 1000
                    cls._instance._ttl_seconds = 2 * 60 * 60  # 2小时
        return cls._instance

    def _generate_id(self, song_name: str, singers: str, source: str) -> str:
        """生成唯一 ID"""
        key = f"{song_name}|{singers}|{source}|{time.time()}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def store(self, song_info_obj: Any, song_name: str, singers: str, source: str) -> str:
        """
        存储 SongInfo 对象

        Args:
            song_info_obj: SongInfo 对象
            song_name: 歌曲名
            singers: 歌手
            source: 来源

        Returns:
            song_id: 用于后续检索的唯一 ID
        """
        song_id = self._generate_id(song_name, singers, source)

        with self._lock:
            # 清理过期条目
            self._cleanup_expired()

            # 限制缓存大小
            if len(self._cache) >= self._max_size:
                self._evict_oldest()

            self._cache[song_id] = {
                'song_info_obj': song_info_obj,
                'song_name': song_name,
                'singers': singers,
                'source': source,
                'stored_at': time.time()
            }

        logger.debug(f"[SongInfoCache] 存储: {song_id} - {song_name} - {singers}")
        return song_id

    def get(self, song_id: str) -> Optional[Any]:
        """
        获取 SongInfo 对象

        Args:
            song_id: 存储时返回的唯一 ID

        Returns:
            SongInfo 对象，如果不存在或已过期则返回 None
        """
        with self._lock:
            entry = self._cache.get(song_id)

            if entry is None:
                logger.warning(f"[SongInfoCache] 未找到: {song_id}")
                return None

            # 检查是否过期
            if time.time() - entry['stored_at'] > self._ttl_seconds:
                del self._cache[song_id]
                logger.warning(f"[SongInfoCache] 已过期: {song_id}")
                return None

            logger.debug(f"[SongInfoCache] 命中: {song_id} - {entry['song_name']}")
            return entry['song_info_obj']

    def get_info(self, song_id: str) -> Optional[Dict[str, Any]]:
        """
        获取完整信息（包括元数据）

        Args:
            song_id: 存储 ID

        Returns:
            包含 song_info_obj 和元数据的字典
        """
        with self._lock:
            entry = self._cache.get(song_id)

            if entry is None:
                return None

            if time.time() - entry['stored_at'] > self._ttl_seconds:
                del self._cache[song_id]
                return None

            return entry.copy()

    def _cleanup_expired(self):
        """清理过期条目"""
        current_time = time.time()
        expired = [
            song_id for song_id, entry in self._cache.items()
            if current_time - entry['stored_at'] > self._ttl_seconds
        ]

        for song_id in expired:
            del self._cache[song_id]

        if expired:
            logger.info(f"[SongInfoCache] 清理 {len(expired)} 个过期条目")

    def _evict_oldest(self):
        """驱逐最旧的条目"""
        if not self._cache:
            return

        oldest_id = min(
            self._cache.keys(),
            key=lambda x: self._cache[x]['stored_at']
        )
        del self._cache[oldest_id]
        logger.debug(f"[SongInfoCache] 驱逐最旧条目: {oldest_id}")

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("[SongInfoCache] 缓存已清空")

    def size(self) -> int:
        """返回缓存大小"""
        return len(self._cache)


# 全局单例
song_info_cache = SongInfoCache()