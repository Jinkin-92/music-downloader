"""SongMatcher tests"""
import pytest


class TestSongMatcher:
    """Test song matching algorithms"""

    def test_calculate_similarity_identical(self):
        """Test similarity of identical strings"""
        from pyqt_ui.batch import SongMatcher

        score = SongMatcher.calculate_similarity("Hello", "Hello")
        assert score == 1.0

    def test_is_match_perfect_match(self):
        """Test perfect name and singer match"""
        from pyqt_ui.batch import SongMatcher

        result = SongMatcher.is_match(
            "告白气球", "周杰伦",
            "告白气球", "周杰伦"
        )
        assert result is True

    def test_find_best_match_method_exists(self):
        """Test that find_best_match method exists"""
        from pyqt_ui.batch import SongMatcher

        # Test that method can be called
        result = SongMatcher.find_best_match({'name': 'test', 'singer': 'test'}, [])
        # Should not raise AttributeError
        assert result is None  # Empty list should return None
