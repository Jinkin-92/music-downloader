"""Song matching algorithms"""
from difflib import SequenceMatcher


class SongMatcher:
    """Song similarity matching"""

    SIMILARITY_THRESHOLD = 0.6

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
        # ✅ 保留中文字符范围 (\u4e00-\u9fff)、英文字母、数字
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
    def find_best_match(parsed_song: dict, all_results: list):
        """Find the best matching song from search results"""
        query_name = parsed_song.get('name', '')
        query_singer = parsed_song.get('singer', '')
        
        if not all_results:
            return None
        
        best_match = None
        best_score = 0.0
        
        for result in all_results:
            # Handle both dict and SongInfo objects
            if isinstance(result, dict):
                result_name = result.get("song_name", "")
                result_singer = result.get("singers", "")
            else:
                result_name = getattr(result, "song_name", "")
                result_singer = getattr(result, "singers", "")
            
            name_sim = SongMatcher.calculate_similarity(query_name, result_name)
            singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
            
            combined_score = (name_sim * 0.7) + (singer_sim * 0.3)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = result
        
        if best_score >= SongMatcher.SIMILARITY_THRESHOLD:
            return best_match
        
        return None
