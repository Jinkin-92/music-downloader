"""
Song Matcher - 相似度匹配算法

提供歌曲相似度计算和匹配功能。

优化版本 v2.0:
- 动态权重：专辑为空时重新分配权重
- 完全匹配加分：提高精确匹配的得分
- 更准确的相似度计算
"""

from difflib import SequenceMatcher
from typing import List, Dict, Optional, Any, Tuple

from core.config import (
    BATCH_MATCH_SIMILARITY_THRESHOLD,
    DEFAULT_SIMILARITY_WEIGHTS
)


class SongMatcher:
    """Song similarity matching - 优化版"""

    # 使用配置文件中的阈值
    SIMILARITY_THRESHOLD = BATCH_MATCH_SIMILARITY_THRESHOLD

    # 完全匹配加分
    EXACT_MATCH_BONUS = 0.15  # 完全匹配额外加分15%

    @staticmethod
    def calculate_similarity(query: str, result: str) -> float:
        """Calculate similarity between query and result"""
        query_norm = SongMatcher._normalize_text(query)
        result_norm = SongMatcher._normalize_text(result)

        if not query_norm or not result_norm:
            return 0.0

        return SequenceMatcher(None, query_norm, result_norm).ratio()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison

        Preserves Chinese characters, English letters, and numbers
        Removes only punctuation, spaces, and special characters
        """
        import re
        if not text:
            return ""
        text = text.lower()
        # 保留中文字符范围 (\u4e00-\u9fff)、英文字母、数字
        # 只移除标点符号、空格和特殊字符
        text = re.sub(r'[^\u4e00-\u9fff\w]', '', text)
        return text

    @staticmethod
    def _calculate_dynamic_weights(query_album: str, result_album: str) -> Dict[str, float]:
        """
        计算动态权重

        如果专辑为空，将专辑权重分配给歌名和歌手

        Args:
            query_album: 查询专辑
            result_album: 结果专辑

        Returns:
            权重字典
        """
        base_weights = DEFAULT_SIMILARITY_WEIGHTS.copy()

        # 如果查询或结果没有专辑信息，重新分配权重
        if not query_album or not result_album:
            # 将专辑权重分配给歌名和歌手（按比例）
            album_weight = base_weights['album']
            name_weight = base_weights['name']
            singer_weight = base_weights['singer']

            # 按原有比例分配
            total = name_weight + singer_weight
            base_weights['name'] = name_weight + (album_weight * name_weight / total)
            base_weights['singer'] = singer_weight + (album_weight * singer_weight / total)
            base_weights['album'] = 0.0

        return base_weights

    @staticmethod
    def _calculate_exact_match_bonus(query: str, result: str) -> float:
        """
        计算完全匹配加分

        Args:
            query: 查询文本
            result: 结果文本

        Returns:
            加分值
        """
        query_norm = SongMatcher._normalize_text(query)
        result_norm = SongMatcher._normalize_text(result)

        if not query_norm or not result_norm:
            return 0.0

        # 完全匹配
        if query_norm == result_norm:
            return SongMatcher.EXACT_MATCH_BONUS

        # 包含关系加分（较短文本完全包含在较长文本中）
        if query_norm in result_norm or result_norm in query_norm:
            return SongMatcher.EXACT_MATCH_BONUS * 0.5

        return 0.0

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

        优化版相似度计算：
        - 动态权重：专辑为空时重新分配
        - 完全匹配加分：提高精确匹配得分
        - 强制按相似度降序排序

        Args:
            parsed_song: 解析后的歌曲信息 {'name': '歌名', 'artist': '歌手', 'album': '专辑'}
            all_results: 所有搜索结果列表
            threshold: 相似度阈值 (0.0-1.0)，None使用默认值

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

        # 计算所有结果的相似度
        scored_results: List[Tuple[float, Any]] = []

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

            # 计算各部分相似度
            name_sim = SongMatcher.calculate_similarity(query_name, result_name)
            singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
            album_sim = SongMatcher.calculate_similarity(query_album, result_album) if query_album and result_album else 0.0

            # 动态权重
            weights = SongMatcher._calculate_dynamic_weights(query_album, result_album)
            combined_score = (
                name_sim * weights['name'] +
                singer_sim * weights['singer'] +
                album_sim * weights['album']
            )

            # 完全匹配加分
            name_bonus = SongMatcher._calculate_exact_match_bonus(query_name, result_name)
            singer_bonus = SongMatcher._calculate_exact_match_bonus(query_singer, result_singer)

            # 总加分不超过一定限度
            total_bonus = min(name_bonus + singer_bonus, 0.25)
            combined_score = min(combined_score + total_bonus, 1.0)

            scored_results.append((combined_score, result))

        # 按相似度降序排序
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # 返回最佳匹配（如果满足阈值）
        if scored_results and scored_results[0][0] >= similarity_threshold:
            return scored_results[0][1]

        return None

    @staticmethod
    def rank_all_matches(parsed_song: dict, all_results: list) -> List[Tuple[float, Any]]:
        """
        对所有匹配结果进行排序

        Args:
            parsed_song: 解析后的歌曲信息
            all_results: 所有搜索结果列表

        Returns:
            排序后的 [(相似度, 结果), ...] 列表
        """
        query_name = parsed_song.get('name', '')
        query_singer = parsed_song.get('singer') or parsed_song.get('artist', '')
        query_album = parsed_song.get('album', '')

        if not all_results:
            return []

        scored_results: List[Tuple[float, Any]] = []

        for result in all_results:
            if isinstance(result, dict):
                result_name = result.get("song_name", "")
                result_singer = result.get("singers", "")
                result_album = result.get("album", "")
            else:
                result_name = getattr(result, "song_name", "")
                result_singer = getattr(result, "singers", "")
                result_album = getattr(result, "album", "")

            # 计算各部分相似度
            name_sim = SongMatcher.calculate_similarity(query_name, result_name)
            singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
            album_sim = SongMatcher.calculate_similarity(query_album, result_album) if query_album and result_album else 0.0

            # 动态权重
            weights = SongMatcher._calculate_dynamic_weights(query_album, result_album)
            combined_score = (
                name_sim * weights['name'] +
                singer_sim * weights['singer'] +
                album_sim * weights['album']
            )

            # 完全匹配加分
            name_bonus = SongMatcher._calculate_exact_match_bonus(query_name, result_name)
            singer_bonus = SongMatcher._calculate_exact_match_bonus(query_singer, result_singer)
            total_bonus = min(name_bonus + singer_bonus, 0.25)
            combined_score = min(combined_score + total_bonus, 1.0)

            scored_results.append((combined_score, result))

        # 按相似度降序排序
        scored_results.sort(key=lambda x: x[0], reverse=True)

        return scored_results

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

        # 使用动态权重计算
        weights = SongMatcher._calculate_dynamic_weights(query_album, result_album)
        combined = (
            name_sim * weights['name'] +
            singer_sim * weights['singer'] +
            album_sim * weights['album']
        )

        # 完全匹配加分
        name_bonus = SongMatcher._calculate_exact_match_bonus(query_name, result_name)
        singer_bonus = SongMatcher._calculate_exact_match_bonus(query_singer, result_singer)
        total_bonus = min(name_bonus + singer_bonus, 0.25)
        combined = min(combined + total_bonus, 1.0)

        return {
            'name_similarity': name_sim,
            'singer_similarity': singer_sim,
            'album_similarity': album_sim,
            'combined': combined,
            'exact_match_bonus': total_bonus
        }