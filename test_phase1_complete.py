#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for Phase 1 (P2: Adjustable Match Confidence)
Tests all components of the match filtering feature
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def test_config_module():
    """Test 1: Verify config module exports"""
    print("=== Test 1: Config Module ===")
    from pyqt_ui.config import (
        MatchMode, DEFAULT_MATCH_MODE, DEFAULT_MATCH_THRESHOLD,
        MATCH_THRESHOLDS, MATCH_MODE_LABELS
    )

    # Verify MatchMode enum
    assert MatchMode.STRICT.value == "strict"
    assert MatchMode.STANDARD.value == "standard"
    assert MatchMode.LOOSE.value == "loose"
    assert MatchMode.CUSTOM.value == "custom"
    print("  MatchMode enum: OK")

    # Verify default values
    assert DEFAULT_MATCH_MODE == MatchMode.STANDARD
    assert DEFAULT_MATCH_THRESHOLD == 0.60
    print("  Default values: OK")

    # Verify thresholds
    assert MATCH_THRESHOLDS[MatchMode.STRICT] == 0.90
    assert MATCH_THRESHOLDS[MatchMode.STANDARD] == 0.60
    assert MATCH_THRESHOLDS[MatchMode.LOOSE] == 0.40
    print("  Thresholds: OK")

    # Verify labels
    assert "90%" in MATCH_MODE_LABELS[MatchMode.STRICT]
    assert "60%" in MATCH_MODE_LABELS[MatchMode.STANDARD]
    assert "40%" in MATCH_MODE_LABELS[MatchMode.LOOSE]
    print("  Labels: OK")

    print("PASS\n")


def test_batch_song_match_filters():
    """Test 2: Verify BatchSongMatch filtering methods"""
    print("=== Test 2: BatchSongMatch Filtering Methods ===")
    from pyqt_ui.batch.models import BatchSongMatch, MatchCandidate, MatchSource

    # Create test candidates
    candidates = [
        MatchCandidate(
            song_name="Test1", singers="Artist1", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.95, song_info_obj=None
        ),
        MatchCandidate(
            song_name="Test2", singers="Artist1", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.75, song_info_obj=None
        ),
        MatchCandidate(
            song_name="Test3", singers="Artist1", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.55, song_info_obj=None
        ),
    ]

    song_match = BatchSongMatch(
        query={"name": "Test", "singer": "Artist1", "original_line": "Test - Artist1"}
    )
    song_match.all_matches = {"QQMusicClient": candidates}
    song_match.has_match = True
    song_match.current_match = candidates[0]  # 0.95
    song_match.current_source = "QQMusicClient"

    # Test filter_by_threshold
    filtered = song_match.filter_by_threshold(0.90)
    assert len(filtered) == 1
    assert filtered[0].similarity_score == 0.95
    print("  filter_by_threshold(0.90): OK")

    filtered = song_match.filter_by_threshold(0.60)
    assert len(filtered) == 2
    print("  filter_by_threshold(0.60): OK")

    # Test get_filtered_candidates with preserve_current
    song_match.current_match = candidates[2]  # 0.55 (below threshold)
    filtered = song_match.get_filtered_candidates(0.90, preserve_current=True)
    assert len(filtered) == 2  # Current (0.55) + filtered (0.95)
    assert filtered[0].similarity_score == 0.55  # Current first
    assert filtered[1].similarity_score == 0.95
    print("  get_filtered_candidates (preserve_current): OK")

    # Test auto_select_best_within_threshold
    song_match.current_match = candidates[2]  # 0.55
    best = song_match.auto_select_best_within_threshold(0.90)
    assert best.similarity_score == 0.95
    print("  auto_select_best_within_threshold: OK")

    # Test current match already meets threshold
    song_match.current_match = candidates[1]  # 0.75 (>= 0.60, < 0.90)
    best = song_match.auto_select_best_within_threshold(0.60)
    assert best.similarity_score == 0.75  # Keep current
    print("  auto_select_best (current meets threshold): OK")

    print("PASS\n")


def test_match_settings_ui():
    """Test 3: Verify match settings UI components"""
    print("=== Test 3: Match Settings UI Components ===")

    app = QApplication(sys.argv)
    from pyqt_ui.main import MainWindow

    # Clear any existing settings to get fresh state
    from PyQt6.QtCore import QSettings
    settings = QSettings("MusicDownloader", "BatchDownload")
    settings.remove("match_mode")
    settings.remove("custom_threshold")

    window = MainWindow()

    # Verify UI components exist
    assert hasattr(window, 'strict_btn')
    assert hasattr(window, 'standard_btn')
    assert hasattr(window, 'loose_btn')
    assert hasattr(window, 'threshold_slider')
    assert hasattr(window, 'threshold_label')
    assert hasattr(window, 'advanced_options_widget')
    assert hasattr(window, 'toggle_advanced_btn')
    print("  UI components exist: OK")

    # Verify buttons are checkable
    assert window.strict_btn.isCheckable()
    assert window.standard_btn.isCheckable()
    assert window.loose_btn.isCheckable()
    print("  Buttons are checkable: OK")

    # Verify default state
    assert window.standard_btn.isChecked()
    assert window.advanced_options_widget.isHidden()  # Use isHidden() instead of isVisible()
    print("  Default state (standard mode selected, advanced hidden): OK")

    # Verify toggle_advanced_options
    window.toggle_advanced_options()
    assert not window.advanced_options_widget.isHidden()  # Should be visible now
    print("  Toggle advanced options (show): OK")

    window.toggle_advanced_options()
    assert window.advanced_options_widget.isHidden()  # Should be hidden again
    print("  Toggle advanced options (hide): OK")

    print("PASS\n")


def test_mode_switching():
    """Test 4: Verify match mode switching"""
    print("=== Test 4: Match Mode Switching ===")

    app = QApplication(sys.argv)
    from pyqt_ui.main import MainWindow
    from pyqt_ui.config import MatchMode

    window = MainWindow()

    # Test switching to STRICT mode
    window.set_match_mode(MatchMode.STRICT)
    assert window.current_match_mode == MatchMode.STRICT
    assert window.current_threshold == 0.90
    assert window.strict_btn.isChecked()
    print("  Switch to STRICT mode: OK")

    # Test switching to LOOSE mode
    window.set_match_mode(MatchMode.LOOSE)
    assert window.current_match_mode == MatchMode.LOOSE
    assert window.current_threshold == 0.40
    assert window.loose_btn.isChecked()
    print("  Switch to LOOSE mode: OK")

    # Test switching to STANDARD mode
    window.set_match_mode(MatchMode.STANDARD)
    assert window.current_match_mode == MatchMode.STANDARD
    assert window.current_threshold == 0.60
    assert window.standard_btn.isChecked()
    print("  Switch to STANDARD mode: OK")

    # Test custom threshold
    window.threshold_slider.setValue(75)
    assert window.current_threshold == 0.75
    assert window.current_match_mode == MatchMode.CUSTOM
    assert window.threshold_label.text() == "75%"
    print("  Custom threshold (75%): OK")

    print("PASS\n")


def test_persistence():
    """Test 5: Verify QSettings persistence"""
    print("=== Test 5: QSettings Persistence ===")
    from PyQt6.QtCore import QSettings
    from pyqt_ui.config import MatchMode

    settings = QSettings("MusicDownloader", "BatchDownload")

    # Save test values
    settings.setValue("match_mode", "strict")
    settings.setValue("custom_threshold", 0.90)

    # Load test values
    mode_str = settings.value("match_mode", "standard")
    threshold = settings.value("custom_threshold", 0.60)

    assert mode_str == "strict"
    assert float(threshold) == 0.90
    print("  Save/Load preferences: OK")

    # Test with MainWindow
    app = QApplication(sys.argv)
    from pyqt_ui.main import MainWindow

    # Create window and set preferences
    window1 = MainWindow()
    window1.set_match_mode(MatchMode.LOOSE)

    # Create second window (simulates restart)
    window2 = MainWindow()

    # Verify preferences persisted
    assert window2.current_match_mode == MatchMode.LOOSE
    assert window2.current_threshold == 0.40
    print("  Preferences persist across MainWindow instances: OK")

    # Cleanup - restore defaults
    settings.setValue("match_mode", "standard")
    settings.setValue("custom_threshold", 0.60)

    print("PASS\n")


def test_application_startup():
    """Test 6: Verify application can start without errors"""
    print("=== Test 6: Application Startup ===")

    app = QApplication(sys.argv)

    try:
        from pyqt_ui.main import MainWindow
        window = MainWindow()

        # Verify window was created
        assert window.windowTitle() != ""
        print("  Window creation: OK")

        # Verify batch download tab exists
        assert window.mode_tab_widget.count() >= 1
        print("  Batch download tab: OK")

        # Verify match settings group exists
        assert hasattr(window, 'strict_btn')
        assert hasattr(window, 'standard_btn')
        assert hasattr(window, 'loose_btn')
        print("  Match settings UI: OK")

        print("PASS\n")

    except Exception as e:
        print(f"FAILED: Application startup failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("PHASE 1 (P2: Adjustable Match Confidence) - Comprehensive Test")
    print("=" * 60)
    print()

    try:
        test_config_module()
        test_batch_song_match_filters()
        test_match_settings_ui()
        test_mode_switching()
        test_persistence()
        test_application_startup()

        print("=" * 60)
        print("SUCCESS: All Phase 1 tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - Config module: OK")
        print("  - BatchSongMatch filtering: OK")
        print("  - Match settings UI: OK")
        print("  - Mode switching: OK")
        print("  - QSettings persistence: OK")
        print("  - Application startup: OK")
        print()
        print("Phase 1 (P2) is COMPLETE and ready for use!")
        print("=" * 60)

        return True

    except AssertionError as e:
        print(f"\n{'=' * 60}")
        print(f"FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
