"""Test batch similarity calculation fix"""
import pytest
from pyqt_ui.batch.matcher import SongMatcher
from pyqt_ui.batch.models import MatchCandidate


class TestBatchSimilarityFix:
    """Test similarity calculation improvements"""

    def test_separate_name_singer_similarity(self):
        """Test that similarity is calculated separately for name and singer"""
        # 测试用例：正确的歌曲应该有较高相似度
        query_name = "还你"
        query_singer = "新学校废物合唱团"

        result_name = "还你"
        result_singer = "新学校废物合唱团"

        # 分别计算相似度
        name_sim = SongMatcher.calculate_similarity(query_name, result_name)
        singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)

        # 组合分数（歌名70%，歌手30%）
        combined_sim = (name_sim * 0.7) + (singer_sim * 0.3)

        # 完全匹配应该得到1.0
        assert name_sim == 1.0, f"Name similarity should be 1.0, got {name_sim}"
        assert singer_sim == 1.0, f"Singer similarity should be 1.0, got {singer_sim}"
        assert combined_sim == 1.0, f"Combined similarity should be 1.0, got {combined_sim}"

    def test_partial_match_similarity(self):
        """Test partial matching with slight differences"""
        # 测试部分匹配的情况
        query_name = "还你"
        query_singer = "新学校废物合唱团"

        result_name = "还你！(Live)"
        result_singer = "新学校废物合唱团"

        # 分别计算相似度
        name_sim = SongMatcher.calculate_similarity(query_name, result_name)
        singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
        combined_sim = (name_sim * 0.7) + (singer_sim * 0.3)

        # 歌手完全匹配（1.0）
        assert singer_sim == 1.0, f"Singer similarity should be 1.0, got {singer_sim}"
        # ✅ 修复后：中文被保留，"还你" vs "还你live" 相似度为 0.5 是合理的
        # 因为 "还你" (2字符) vs "还你live" (6字符)，最长公共子序列是2
        # SequenceMatcher 比率 = 2*2/(2+6) = 0.5
        assert name_sim == 0.5, f"Name similarity should be 0.5, got {name_sim}"
        # ✅ 关键：组合分数应该通过0.6阈值（歌手权重30%弥补了歌名差异）
        assert combined_sim >= 0.6, f"Combined similarity {combined_sim} should pass 0.6 threshold"

    def test_similarity_above_threshold(self):
        """Test that correct songs pass the 0.6 threshold"""
        # 这个测试确保修复后的相似度计算能让正确的歌通过阈值
        query_name = "还你"
        query_singer = "新学校废物合唱团"

        result_name = "还你"
        result_singer = "新学校废物合唱团"

        name_sim = SongMatcher.calculate_similarity(query_name, result_name)
        singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
        combined_sim = (name_sim * 0.7) + (singer_sim * 0.3)

        # 应该通过0.6阈值
        assert combined_sim >= 0.6, f"Combined similarity {combined_sim} should pass 0.6 threshold"

    def test_weight_calculation(self):
        """Test that name has 70% weight and singer has 30% weight"""
        # 测试权重计算
        name_sim = 0.8
        singer_sim = 0.5
        combined = (name_sim * 0.7) + (singer_sim * 0.3)

        expected = 0.8 * 0.7 + 0.5 * 0.3
        assert combined == expected, f"Weight calculation incorrect: {combined} vs {expected}"
        assert combined == 0.71, f"Combined should be 0.71, got {combined}"

    def test_different_name_same_singer(self):
        """Test different song name but same singer"""
        # 不同歌名，同一歌手
        query_name = "还你"
        query_singer = "新学校废物合唱团"

        result_name = "别等了"
        result_singer = "新学校废物合唱团"

        name_sim = SongMatcher.calculate_similarity(query_name, result_name)
        singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
        combined_sim = (name_sim * 0.7) + (singer_sim * 0.3)

        # 歌手完全匹配（1.0），歌名不匹配（低）
        assert singer_sim == 1.0, f"Singer similarity should be 1.0"
        assert name_sim < 0.5, f"Name similarity should be low"
        # 组合分数应该主要由歌手贡献（30%权重）
        assert 0.2 < combined_sim < 0.5, f"Combined similarity should be in mid-range: {combined_sim}"

    def test_same_name_different_singer(self):
        """Test same song name but different singer"""
        # 同歌名，不同歌手
        query_name = "还你"
        query_singer = "新学校废物合唱团"

        result_name = "还你"
        result_singer = "其他歌手"

        name_sim = SongMatcher.calculate_similarity(query_name, result_name)
        singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
        combined_sim = (name_sim * 0.7) + (singer_sim * 0.3)

        # 歌名完全匹配（1.0），歌手不匹配（低）
        assert name_sim == 1.0, f"Name similarity should be 1.0"
        assert singer_sim < 0.5, f"Singer similarity should be low"
        # 组合分数应该主要由歌名贡献（70%权重）
        assert combined_sim > 0.65, f"Combined similarity should be > 0.65: {combined_sim}"

    def test_candidate_creation_with_new_similarity(self):
        """Test MatchCandidate creation with new similarity calculation"""
        # 验证MatchCandidate可以使用新的相似度计算
        query_name = "还你"
        query_singer = "新学校废物合唱团"

        result_name = "还你"
        result_singer = "新学校废物合唱团"

        name_sim = SongMatcher.calculate_similarity(query_name, result_name)
        singer_sim = SongMatcher.calculate_similarity(query_singer, result_singer)
        similarity = (name_sim * 0.7) + (singer_sim * 0.3)

        # 创建候选对象
        candidate = MatchCandidate(
            song_name=result_name,
            singers=result_singer,
            album="专辑名",
            file_size="5.2MB",
            duration="3:45",
            source="KugouMusicClient",
            ext="mp3",
            similarity_score=similarity,
            song_info_obj=None
        )

        assert candidate.song_name == result_name
        assert candidate.singers == result_singer
        assert candidate.similarity_score == 1.0

    def test_normalization_works_correctly(self):
        """Test that text normalization works correctly"""
        # 测试文本规范化
        text1 = "还你"
        text2 = "还你！(Live)"
        text3 = "新学校废物合唱团"

        # 规范化应该去除标点符号和特殊字符，但保留中文
        norm1 = SongMatcher._normalize_text(text1)
        norm2 = SongMatcher._normalize_text(text2)
        norm3 = SongMatcher._normalize_text(text3)

        # ✅ 修复后：中文被正确保留
        assert len(norm1) == 2, f"Normalization should preserve 2 Chinese characters: '{norm1}'"
        assert len(norm3) == 8, f"Normalization should preserve 8 Chinese characters: '{norm3}'"
        assert "live" in norm2.lower(), f"Normalization should preserve 'live' in '{norm2}'"

        # ✅ 完全相同的文本应该有1.0相似度
        assert SongMatcher.calculate_similarity(text3, text3) == 1.0

        # ✅ text1 和 text2 的相似度应该是 0.5（因为多了"live"后缀）
        sim = SongMatcher.calculate_similarity(text1, text2)
        assert sim == 0.5, f"'{text1}' vs '{text2}' similarity should be 0.5, got {sim}"
