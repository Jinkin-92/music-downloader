"""
Song Matcher - 相似度匹配算法

提供歌曲相似度计算和匹配功能。
"""

from difflib import SequenceMatcher
from typing import List, Dict, Optional, Any

from core.config import (
    BATCH_MATCH_SIMILARITY_THRESHOLD,
    DEFAULT_SIMILARITY_WEIGHTS
)


class SongMatcher:
    """Song similarity matching"""

    # 使用配置文件中的阈值
    SIMILARITY_THRESHOLD = BATCH_MATCH_SIMILARITY_THRESHOLD

    @staticmethod
    def calculate_similarity(query: str, result: str) -> float:
        """Calculate similarity between query and result"""
        query_norm = SongMatcher._normalize_text(query)
        result_norm = SongMatcher._normalize_text(result)
        return SequenceMatcher(None, query_norm, result_norm).ratio()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison

        Preserves Chinese characters, English letters, and numbers
        Removes only punctuation, spaces, and special characters
        """
        import re
        text = text.lower()
        # 保留中文字符范围 (\u4e00-\u9fff)、英文字母、数字
        # 只移除标点符号、空格和特殊字符
        text = re.sub(r'[^\u4e00-\u9fff\w]', '', text)
        return text

    @staticmethod
    def is_match(name_query: str, singer_query: str,
                 name_result: str, singer_result: str) -> bool:
        """Check if query matches result"""
        name_sim = SongMatcher.calculate_similarity(name_query, name_result)
        singer_sim = SongMatcher.calculate_similarity(singer_query, singer_result)

        return (
            name_sim >= SongMatcher.SIMILARITY_THRESHOLD and
            singer_sim >= SongMatcher.SIMILARITY_THRESHOLD * 0.5
        )

    @staticmethod
    def find_best_match(parsed_song: dict, all_results: list, threshold: float = None):
        """Find the best matching song from search results

        相似度计算：歌名50% + 歌手40% + 专辑10%

        Args:
            parsed_song: 解析后的歌曲信息 {'name': '歌名', 'artist': '歌手', 'album': '专辑'}
            all_results: 所有搜索结果列表
            threshold: 相似度阈值 (0.0-1.0)，None使用默认值(0.4)

        Returns:
            最佳匹配结果，如果没有满足阈值的匹配则返回None
        """
        # 兼容 'singer' 和 'artist' 两种键名
        query_name = parsed_song.get('name', '')
        query_singer = parsed_song.get('singer') or parsed_song.get('artist', '')
        query_album = parsed_song.get('album', '')

        if not all_results:
            return None

        # 使用传入的阈值或默认阈值
        similarity_threshold = threshold if threshold is not None else SongMatcher.SIMILARITY_THRESHOLD

        best_match = None
        best_score = 0.0

        for result in all_results:
            # Handle both dict and SongInfo objects
            if isinstance(result, dict):
                result_name = result.get("song_name", "")
                result_singer = result.get("singers", "")
                result_album = result.get("album", "")
            else:
                result_name = getattr(result, "song_name", "")
                result_singer = getattr(result, "singers", "")
                result_album = getattr(result, "album", "")

            name_sim = SongMatcher.calculate_similarity(query_name, result_name)
            singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
            album_sim = SongMatcher.calculate_similarity(query_album, result_album) if query_album and result_album else 0.0

            # 使用配置文件中的权重
            weights = DEFAULT_SIMILARITY_WEIGHTS
            combined_score = (name_sim * weights['name']) + (singer_sim * weights['singer']) + (album_sim * weights['album'])

            if combined_score > best_score:
                best_score = combined_score
                best_match = result

        if best_score >= similarity_threshold:
            return best_match

        return None

    @staticmethod
    def calculate_similarity_breakdown(query_name: str, query_singer: str, query_album: str,
                                        result_name: str, result_singer: str, result_album: str) -> Dict[str, float]:
        """计算相似度分解（用于前端展示详细分解）

        Args:
            query_name: 查询歌名
            query_singer: 查询歌手
            query_album: 查询专辑
            result_name: 结果歌名
            result_singer: 结果歌手
            result_album: 结果专辑

        Returns:
            包含 name_similarity, singer_similarity, album_similarity, combined 的字典
        """
        name_sim = SongMatcher.calculate_similarity(query_name, result_name)
        singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
        album_sim = SongMatcher.calculate_similarity(query_album, result_album) if query_album and result_album else 0.0

        combined = (name_sim * 0.5) + (singer_sim * 0.4) + (album_sim * 0.1)

        return {
            'name_similarity': name_sim,
            'singer_similarity': singer_sim,
            'album_similarity': album_sim,
            'combined': combined
        }