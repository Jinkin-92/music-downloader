"""DuplicateChecker tests"""
import pytest


class TestDuplicateChecker:
    """Test duplicate file detection"""

    def test_check_duplicates_with_files(self, tmp_path):
        """Test detecting existing files in download directory"""
        from pyqt_ui.batch import DuplicateChecker

        # Create test files
        (tmp_path / "Song1 - Singer1.mp3").touch()
        (tmp_path / "Song2 - Singer2.ogg").touch()

        songs = [
            {"name": "Song1", "singer": "Singer1"},
            {"name": "Song2", "singer": "Singer2"},
            {"name": "Song3", "singer": "Singer3"}
        ]

        duplicates = DuplicateChecker.check_duplicates(songs, tmp_path)

        assert 0 in duplicates
        assert 1 in duplicates
        assert 2 not in duplicates

    def test_check_duplicates_nonexistent_dir(self):
        """Test checking duplicates in non-existent directory"""
        from pyqt_ui.batch import DuplicateChecker
        from pathlib import Path

        songs = [{"name": "Song1", "singer": "Singer1"}]
        fake_dir = Path("/nonexistent/path")
        duplicates = DuplicateChecker.check_duplicates(songs, fake_dir)
        assert len(duplicates) == 0

    def test_check_duplicates_case_insensitive(self, tmp_path):
        """Test case-insensitive filename matching"""
        from pyqt_ui.batch import DuplicateChecker

        # Create file with uppercase name
        (tmp_path / "SONG1 - SINGER1.MP3").touch()

        songs = [{"name": "Song1", "singer": "Singer1"}]
        duplicates = DuplicateChecker.check_duplicates(songs, tmp_path)

        assert 0 in duplicates
