"""Configuration tests"""
import pytest


def test_project_structure():
    """Verify project directories exist"""
    from pyqt_ui.config import DOWNLOAD_DIR, LOG_DIR

    assert DOWNLOAD_DIR.exists()
    assert LOG_DIR.exists()
    assert DOWNLOAD_DIR.is_dir()
    assert LOG_DIR.is_dir()


def test_default_sources():
    """Verify default music sources configured"""
    from pyqt_ui.config import DEFAULT_SOURCES, SOURCE_LABELS

    assert len(DEFAULT_SOURCES) == 4
    assert "QQMusicClient" in DEFAULT_SOURCES
    assert all(src in SOURCE_LABELS for src in DEFAULT_SOURCES)


def test_batch_config_exists():
    """Verify batch download configuration constants exist"""
    from pyqt_ui.config import (
        BATCH_MAX_SONGS,
        BATCH_MATCH_SIMILARITY_THRESHOLD,
        BATCH_STATUS_LABELS
    )
    assert BATCH_MAX_SONGS == 200
    assert BATCH_MATCH_SIMILARITY_THRESHOLD == 0.6
    assert isinstance(BATCH_STATUS_LABELS, dict)


def test_batch_status_labels_complete():
    """Verify all required status labels are present"""
    from pyqt_ui.config import BATCH_STATUS_LABELS

    required_keys = ["found", "not_found", "duplicate", "downloading", "completed", "failed"]
    for key in required_keys:
        assert key in BATCH_STATUS_LABELS
        assert isinstance(BATCH_STATUS_LABELS[key], str)
        assert len(BATCH_STATUS_LABELS[key]) > 0
