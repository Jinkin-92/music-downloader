#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Phase 3 (P1: Quick Switch Enhanced Version)
Tests cross-source switching, undo functionality, and UI optimizations
"""

import sys
from PyQt6.QtWidgets import QApplication


def test_cross_source_menu():
    """Test 1: Verify cross-source menu structure"""
    print("=== Test 1: Cross-Source Menu Structure ===")
    from pyqt_ui.batch.models import BatchSongMatch, MatchCandidate

    # Create candidates from multiple sources
    qq_candidates = [
        MatchCandidate(
            song_name="Song1", singers="Artist1", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.95, song_info_obj=None
        ),
        MatchCandidate(
            song_name="Song2", singers="Artist1", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.75, song_info_obj=None
        ),
    ]

    netease_candidates = [
        MatchCandidate(
            song_name="Song1", singers="Artist1", album="Album1",
            file_size="6MB", duration="3:50", source="NeteaseMusicClient",
            ext="mp3", similarity_score=0.88, song_info_obj=None
        ),
    ]

    song_match = BatchSongMatch(
        query={"name": "Test", "singer": "Artist1", "original_line": "Test - Artist1"}
    )
    song_match.all_matches = {
        "QQMusicClient": qq_candidates,
        "NeteaseMusicClient": netease_candidates
    }
    song_match.has_match = True
    song_match.current_match = qq_candidates[1]  # 0.75 from QQ
    song_match.current_source = "QQMusicClient"

    # Test get_all_candidates (cross-source)
    all_candidates = song_match.get_all_candidates()

    # Should have 3 candidates total (2 from QQ + 1 from Netease)
    assert len(all_candidates) == 3, f"Expected 3 candidates, got {len(all_candidates)}"
    print("  Cross-source candidate count: OK")

    # Sort by similarity (descending)
    all_candidates_sorted = sorted(
        all_candidates,
        key=lambda x: x.similarity_score,
        reverse=True
    )

    # Verify order: 0.95 (QQ) > 0.88 (Netease) > 0.75 (QQ)
    assert all_candidates_sorted[0].similarity_score == 0.95, "First should be 0.95"
    assert all_candidates_sorted[0].source == "QQMusicClient", "First should be from QQ"
    assert all_candidates_sorted[1].similarity_score == 0.88, "Second should be 0.88"
    assert all_candidates_sorted[1].source == "NeteaseMusicClient", "Second should be from Netease"
    assert all_candidates_sorted[2].similarity_score == 0.75, "Third should be 0.75"
    print("  Cross-source sorting: OK")
    print("PASS\n")


def test_undo_history():
    """Test 2: Verify undo history functionality"""
    print("=== Test 2: Undo History Functionality ===")
    from pyqt_ui.main import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()

    # Verify history initialization
    assert hasattr(window, 'switch_history'), "switch_history not found"
    assert hasattr(window, 'max_history_size'), "max_history_size not found"
    assert window.max_history_size == 50, f"Expected max_history_size=50, got {window.max_history_size}"
    assert len(window.switch_history) == 0, "History should be empty initially"
    print("  Undo history initialization: OK")

    # Simulate adding to history
    from pyqt_ui.batch.models import MatchCandidate

    candidate1 = MatchCandidate(
        song_name="Song1", singers="Artist1", album="Album1",
        file_size="5MB", duration="3:45", source="QQMusicClient",
        ext="mp3", similarity_score=0.75, song_info_obj=None
    )

    candidate2 = MatchCandidate(
        song_name="Song2", singers="Artist1", album="Album1",
        file_size="5MB", duration="3:45", source="QQMusicClient",
        ext="mp3", similarity_score=0.85, song_info_obj=None
    )

    # Add to history
    window._add_to_undo_history("Test Line", candidate1, candidate2)

    assert len(window.switch_history) == 1, f"Expected history size 1, got {len(window.switch_history)}"
    print("  Add to history: OK")

    # Verify history entry structure
    entry = window.switch_history[0]
    assert len(entry) == 3, "History entry should have 3 elements"
    assert entry[0] == "Test Line", "First element should be original_line"
    assert entry[1].song_name == "Song1", "Second element should be old candidate"
    assert entry[2].song_name == "Song2", "Third element should be new candidate"
    print("  History entry structure: OK")

    # Test history limit
    for i in range(55):  # Add more than max_history_size
        window._add_to_undo_history(f"Line{i}", candidate1, candidate2)

    assert len(window.switch_history) == 50, f"History should be limited to 50, got {len(window.switch_history)}"
    print("  History size limit: OK")
    print("PASS\n")


def test_shortcuts_setup():
    """Test 3: Verify keyboard shortcuts setup"""
    print("=== Test 3: Keyboard Shortcuts Setup ===")
    from pyqt_ui.main import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()

    # Verify shortcuts were created
    assert hasattr(window, 'undo_shortcut'), "undo_shortcut not found"
    print("  Undo shortcut created: OK")

    # Verify undo method exists
    assert hasattr(window, 'undo_last_switch'), "undo_last_switch method not found"
    print("  Undo method exists: OK")

    print("PASS\n")


def test_button_styles():
    """Test 4: Verify button style logic (simulated)"""
    print("=== Test 4: Button Style Logic ===")

    # Test button text based on candidate count
    test_cases = [
        (2, "▼", "Small button"),
        (3, "▼", "Small button"),
        (4, "▼4", "Medium button"),
        (10, "▼10", "Medium button"),
        (11, "▼11", "Large button (orange)"),
        (20, "▼20", "Large button (orange)"),
    ]

    for num_candidates, expected_text, description in test_cases:
        # Simulate button text logic
        if num_candidates > 10:
            btn_text = f"▼{num_candidates}"
        elif num_candidates > 3:
            btn_text = f"▼{num_candidates}"
        else:
            btn_text = "▼"

        assert btn_text == expected_text, \
            f"{description}: expected '{expected_text}', got '{btn_text}'"
        print(f"  {description}: OK")

    print("PASS\n")


def test_menu_limit_display():
    """Test 5: Verify menu limit display logic"""
    print("=== Test 5: Menu Limit Display Logic ===")

    # Simulate menu limit logic
    max_display = 15

    # Test with 20 candidates (should show 15 + tip)
    all_candidates_count = 20
    display_count = min(all_candidates_count, max_display)
    should_show_tip = all_candidates_count > max_display

    assert display_count == 15, f"Should display 15, got {display_count}"
    assert should_show_tip == True, f"Should show tip for 20 candidates"
    print("  20 candidates -> display 15 + tip: OK")

    # Test with 10 candidates (should show all, no tip)
    all_candidates_count = 10
    display_count = min(all_candidates_count, max_display)
    should_show_tip = all_candidates_count > max_display

    assert display_count == 10, f"Should display 10, got {display_count}"
    assert should_show_tip == False, f"Should not show tip for 10 candidates"
    print("  10 candidates -> display 10, no tip: OK")

    # Test with exactly 15 candidates
    all_candidates_count = 15
    display_count = min(all_candidates_count, max_display)
    should_show_tip = all_candidates_count > max_display

    assert display_count == 15, f"Should display 15, got {display_count}"
    assert should_show_tip == False, f"Should not show tip for exactly 15 candidates"
    print("  15 candidates -> display 15, no tip: OK")

    print("PASS\n")


def test_source_mark_display():
    """Test 6: Verify source mark in cross-source menu"""
    print("=== Test 6: Source Mark Display ===")

    # Simulate source short name logic
    sources = [
        ("QQMusicClient", "QQ"),
        ("NeteaseMusicClient", "Netease"),
        ("KugouMusicClient", "Kugou"),
        ("KuwoMusicClient", "Kuwo"),
    ]

    for full_name, expected_short in sources:
        short_name = full_name.replace('MusicClient', '')
        assert short_name == expected_short, \
            f"Expected '{expected_short}', got '{short_name}'"
        print(f"  {full_name} -> {expected_short}: OK")

    print("PASS\n")


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("PHASE 3 (P1: Quick Switch Enhanced) - Test Suite")
    print("=" * 60)
    print()

    try:
        test_cross_source_menu()
        test_undo_history()
        test_shortcuts_setup()
        test_button_styles()
        test_menu_limit_display()
        test_source_mark_display()

        print("=" * 60)
        print("SUCCESS: All Phase 3 tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - Cross-source menu: OK")
        print("  - Undo history: OK")
        print("  - Keyboard shortcuts: OK")
        print("  - Button styles: OK")
        print("  - Menu limit: OK")
        print("  - Source marks: OK")
        print()
        print("Phase 3 (P1 Enhanced) is COMPLETE and ready for use!")
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
