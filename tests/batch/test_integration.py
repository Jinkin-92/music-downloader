"""Integration tests for batch download workflow"""
import pytest


class TestBatchWorkflow:
    """Test complete batch download workflow"""

    def test_full_workflow(self, tmp_path):
        """Test complete parse -> match -> check duplicates workflow"""
        from pyqt_ui.batch import BatchParser, SongMatcher, DuplicateChecker

        # Step 1: Parse
        text = "告白气球 - 周杰伦"
        songs = BatchParser.parse(text)
        assert len(songs) == 1
        assert songs[0]["name"] == "告白气球"
        assert songs[0]["singer"] == "周杰伦"

        # Step 2: Match
        mock_result = {"song_name": "告白气球 (live版)", "singers": "周杰伦"}
        is_match = SongMatcher.is_match(
            songs[0]["name"], songs[0]["singer"],
            mock_result["song_name"], mock_result["singers"]
        )
        assert is_match is True

        # Step 3: Check duplicates
        (tmp_path / "告白气球 - 周杰伦.mp3").touch()
        duplicates = DuplicateChecker.check_duplicates(songs[:1], tmp_path)
        assert 0 in duplicates

    def test_constants_consistency(self):
        """Verify constants are consistent across modules"""
        from pyqt_ui.batch import BatchParser, SongMatcher
        from pyqt_ui.config import BATCH_MAX_SONGS, BATCH_MATCH_SIMILARITY_THRESHOLD

        assert BatchParser.MAX_SONGS == BATCH_MAX_SONGS
        assert SongMatcher.SIMILARITY_THRESHOLD == BATCH_MATCH_SIMILARITY_THRESHOLD
