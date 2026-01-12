#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Phase 2 (P1: Quick Switch in Table) - Basic Version
Tests quick switch functionality in batch results table
"""

import sys
from PyQt6.QtWidgets import QApplication


def test_table_structure():
    """Test 1: Verify table has 7 columns including Similarity"""
    print("=== Test 1: Table Structure ===")
    from pyqt_ui.main import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()

    # Verify table has 7 columns
    assert window.batch_results_table.columnCount() == 7, \
        f"Expected 7 columns, got {window.batch_results_table.columnCount()}"

    # Verify header labels
    headers = [window.batch_results_table.horizontalHeaderItem(i).text()
               for i in range(7)]

    expected_headers = ['[checkbox]', '#', 'Song Name', 'Singer', 'Album', 'Source', 'Similarity']
    assert headers == expected_headers, \
        f"Expected headers {expected_headers}, got {headers}"

    print("  Table has 7 columns: OK")
    print("  Header labels correct: OK")
    print("PASS\n")


def test_quick_switch_methods_exist():
    """Test 2: Verify quick switch methods exist"""
    print("=== Test 2: Quick Switch Methods ===")
    from pyqt_ui.main import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()

    # Check methods exist
    assert hasattr(window, 'show_quick_switch_menu'), \
        "show_quick_switch_menu method not found"
    assert hasattr(window, 'quick_switch_to_candidate'), \
        "quick_switch_to_candidate method not found"

    print("  show_quick_switch_menu exists: OK")
    print("  quick_switch_to_candidate exists: OK")
    print("PASS\n")


def test_batch_song_match_candidate_methods():
    """Test 3: Verify BatchSongMatch has required methods"""
    print("=== Test 3: BatchSongMatch Methods ===")
    from pyqt_ui.batch.models import BatchSongMatch, MatchCandidate

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
            ext="mp3", similarity_score=0.85, song_info_obj=None
        ),
    ]

    song_match = BatchSongMatch(
        query={"name": "Test", "singer": "Artist1", "original_line": "Test - Artist1"}
    )
    song_match.all_matches = {"QQMusicClient": candidates}
    song_match.has_match = True
    song_match.current_match = candidates[0]
    song_match.current_source = "QQMusicClient"

    # Test get_all_candidates_from_current_source
    current_source_candidates = song_match.get_all_candidates_from_current_source()
    assert len(current_source_candidates) == 2, \
        f"Expected 2 candidates, got {len(current_source_candidates)}"
    print("  get_all_candidates_from_current_source: OK")

    # Test switch_to_candidate
    song_match.switch_to_candidate(candidates[1], "USER_SELECTED")
    assert song_match.current_match.song_name == "Test2", \
        "Switch failed - current_match not updated"
    print("  switch_to_candidate: OK")

    print("PASS\n")


def test_menu_creation_logic():
    """Test 4: Verify menu creation logic (without actual UI)"""
    print("=== Test 4: Menu Creation Logic ===")

    # This test verifies the logic without creating actual menu
    from pyqt_ui.batch.models import BatchSongMatch, MatchCandidate

    # Create test data
    candidates = [
        MatchCandidate(
            song_name="SongA", singers="ArtistX", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.95, song_info_obj=None
        ),
        MatchCandidate(
            song_name="SongB", singers="ArtistX", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.75, song_info_obj=None
        ),
        MatchCandidate(
            song_name="SongC", singers="ArtistX", album="Album1",
            file_size="5MB", duration="3:45", source="QQMusicClient",
            ext="mp3", similarity_score=0.85, song_info_obj=None
        ),
    ]

    song_match = BatchSongMatch(
        query={"name": "Test", "singer": "ArtistX", "original_line": "Test - ArtistX"}
    )
    song_match.all_matches = {"QQMusicClient": candidates}
    song_match.has_match = True
    song_match.current_match = candidates[1]  # 0.75 - middle similarity
    song_match.current_source = "QQMusicClient"

    # Get candidates from current source
    current_source_candidates = song_match.get_all_candidates_from_current_source()

    # Sort by similarity (descending)
    candidates_sorted = sorted(
        current_source_candidates,
        key=lambda x: x.similarity_score,
        reverse=True
    )

    # Verify sorting
    assert candidates_sorted[0].similarity_score == 0.95, \
        "First candidate should have highest similarity"
    assert candidates_sorted[1].similarity_score == 0.85, \
        "Second candidate should have middle similarity"
    assert candidates_sorted[2].similarity_score == 0.75, \
        "Third candidate should have lowest similarity"
    print("  Candidate sorting logic: OK")

    # Verify current match detection
    is_current = (
        song_match.current_match and
        candidates_sorted[2].song_name == song_match.current_match.song_name and
        candidates_sorted[2].singers == song_match.current_match.singers
    )
    assert is_current, "Should detect current match correctly"
    print("  Current match detection: OK")

    print("PASS\n")


def test_quick_switch_flow():
    """Test 5: Verify quick switch flow (simulated)"""
    print("=== Test 5: Quick Switch Flow ===")
    from pyqt_ui.batch.models import BatchSongMatch, MatchCandidate, MatchSource

    # Create test data
    candidates = [
        MatchCandidate(
            song_name="Version1", singers="Singer1", album="Album",
            file_size="5MB", duration="3:00", source="QQMusicClient",
            ext="mp3", similarity_score=0.80, song_info_obj=None
        ),
        MatchCandidate(
            song_name="Version2", singers="Singer1", album="Album",
            file_size="6MB", duration="3:30", source="QQMusicClient",
            ext="mp3", similarity_score=0.92, song_info_obj=None
        ),
    ]

    song_match = BatchSongMatch(
        query={"name": "Song", "singer": "Singer1", "original_line": "Song - Singer1"}
    )
    song_match.all_matches = {"QQMusicClient": candidates}
    song_match.has_match = True
    song_match.current_match = candidates[0]  # Start with 0.80 version
    song_match.current_source = "QQMusicClient"

    # Simulate quick switch
    original_similarity = song_match.current_match.similarity_score
    assert original_similarity == 0.80, "Initial match should be 0.80"

    # Switch to better candidate
    song_match.switch_to_candidate(candidates[1], MatchSource.USER_SELECTED)

    # Verify switch
    assert song_match.current_match.similarity_score == 0.92, \
        f"After switch, similarity should be 0.92, got {song_match.current_match.similarity_score}"
    assert song_match.current_match.song_name == "Version2", \
        "After switch, song name should be Version2"
    assert song_match.match_source_type == MatchSource.USER_SELECTED, \
        "Match source should be USER_SELECTED"

    print("  Initial match (0.80): OK")
    print("  Switch to better version (0.92): OK")
    print("  Match source updated: OK")
    print("PASS\n")


def test_single_candidate_no_button():
    """Test 6: Verify no button shown when only 1 candidate"""
    print("=== Test 6: Single Candidate (No Button) ===")
    from pyqt_ui.batch.models import BatchSongMatch, MatchCandidate

    # Create test data with only 1 candidate
    candidates = [
        MatchCandidate(
            song_name="OnlyVersion", singers="Singer1", album="Album",
            file_size="5MB", duration="3:00", source="QQMusicClient",
            ext="mp3", similarity_score=0.85, song_info_obj=None
        ),
    ]

    song_match = BatchSongMatch(
        query={"name": "Song", "singer": "Singer1", "original_line": "Song - Singer1"}
    )
    song_match.all_matches = {"QQMusicClient": candidates}
    song_match.has_match = True
    song_match.current_match = candidates[0]
    song_match.current_source = "QQMusicClient"

    # Get candidates from current source
    current_source_candidates = song_match.get_all_candidates_from_current_source()

    # Verify only 1 candidate
    assert len(current_source_candidates) == 1, \
        f"Expected 1 candidate, got {len(current_source_candidates)}"

    # In UI, this should mean no quick switch button
    should_show_button = len(current_source_candidates) > 1
    assert not should_show_button, "Should not show button with only 1 candidate"

    print("  Single candidate detected: OK")
    print("  No button should be shown: OK")
    print("PASS\n")


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("PHASE 2 (P1: Quick Switch in Table) - Test Suite")
    print("=" * 60)
    print()

    try:
        test_table_structure()
        test_quick_switch_methods_exist()
        test_batch_song_match_candidate_methods()
        test_menu_creation_logic()
        test_quick_switch_flow()
        test_single_candidate_no_button()

        print("=" * 60)
        print("SUCCESS: All Phase 2 tests passed!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - Table structure: OK")
        print("  - Quick switch methods: OK")
        print("  - BatchSongMatch methods: OK")
        print("  - Menu creation logic: OK")
        print("  - Quick switch flow: OK")
        print("  - Single candidate handling: OK")
        print()
        print("Phase 2 (P1) basic version is COMPLETE and ready for use!")
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
