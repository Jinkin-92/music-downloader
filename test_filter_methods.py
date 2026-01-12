#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速验证BatchSongMatch过滤方法"""

from pyqt_ui.batch.models import BatchSongMatch, MatchCandidate, MatchSource


def test_filter_methods():
    """测试过滤方法"""

    # 创建测试候选
    candidates = [
        MatchCandidate(
            song_name="Test1",
            singers="Artist1",
            album="Album1",
            file_size="5MB",
            duration="3:45",
            source="QQMusicClient",
            ext="mp3",
            similarity_score=0.95,
            song_info_obj=None,
        ),
        MatchCandidate(
            song_name="Test2",
            singers="Artist1",
            album="Album1",
            file_size="5MB",
            duration="3:45",
            source="QQMusicClient",
            ext="mp3",
            similarity_score=0.85,
            song_info_obj=None,
        ),
        MatchCandidate(
            song_name="Test3",
            singers="Artist1",
            album="Album1",
            file_size="5MB",
            duration="3:45",
            source="QQMusicClient",
            ext="mp3",
            similarity_score=0.75,
            song_info_obj=None,
        ),
        MatchCandidate(
            song_name="Test4",
            singers="Artist1",
            album="Album1",
            file_size="5MB",
            duration="3:45",
            source="QQMusicClient",
            ext="mp3",
            similarity_score=0.55,
            song_info_obj=None,
        ),
    ]

    # 创建BatchSongMatch
    song_match = BatchSongMatch(
        query={"name": "Test", "singer": "Artist1", "original_line": "Test - Artist1"}
    )
    song_match.all_matches = {"QQMusicClient": candidates}
    song_match.has_match = True
    song_match.current_match = candidates[0]  # 0.95
    song_match.current_source = "QQMusicClient"

    print("=== Test 1: filter_by_threshold(0.90) ===")
    filtered = song_match.filter_by_threshold(0.90)
    print(f"Filtered count: {len(filtered)}")
    print(f"Similarities: {[c.similarity_score for c in filtered]}")
    assert len(filtered) == 1, "Should have only 1 candidate >= 90%"
    assert filtered[0].similarity_score == 0.95
    print("PASS Test 1\n")

    print("=== Test 2: filter_by_threshold(0.60) ===")
    filtered = song_match.filter_by_threshold(0.60)
    print(f"Filtered count: {len(filtered)}")
    print(f"Similarities: {[c.similarity_score for c in filtered]}")
    assert len(filtered) == 3, "Should have 3 candidates >= 60%"
    print("PASS Test 2\n")

    print("=== Test 3: get_filtered_candidates(0.90, preserve_current=True) ===")
    # 先设置当前选中为低相似度
    song_match.current_match = candidates[3]  # 0.55
    filtered = song_match.get_filtered_candidates(0.90, preserve_current=True)
    print(f"Filtered count: {len(filtered)}")
    print(f"Similarities: {[c.similarity_score for c in filtered]}")
    # 应该包含当前选中(0.55) + 过滤结果(0.95)
    assert len(filtered) == 2, "Should preserve current even if below threshold"
    assert filtered[0].similarity_score == 0.55, "First should be current"
    assert filtered[1].similarity_score == 0.95, "Second should be filtered"
    print("PASS Test 3\n")

    print("=== Test 4: auto_select_best_within_threshold(0.90) ===")
    # 当前选中0.55，应该自动选择0.95
    best = song_match.auto_select_best_within_threshold(0.90)
    print(f"Best similarity: {best.similarity_score if best else None}")
    assert best is not None, "Should find candidate"
    assert best.similarity_score == 0.95, "Should select 0.95 candidate"
    print("PASS Test 4\n")

    print("=== Test 5: auto_select_best_within_threshold(0.50) - current already meets ===")
    # 设置当前选中为0.75，已经>=0.50
    song_match.current_match = candidates[2]  # 0.75
    best = song_match.auto_select_best_within_threshold(0.50)
    print(f"Best similarity: {best.similarity_score if best else None}")
    assert best.similarity_score == 0.75, "Should keep current"
    print("PASS Test 5\n")

    print("=== Test 6: filter_by_threshold(0.99) - all below threshold ===")
    filtered = song_match.filter_by_threshold(0.99)
    print(f"Filtered count: {len(filtered)}")
    assert len(filtered) == 0, "Should have no candidates >= 99%"
    print("PASS Test 6\n")

    print("=" * 50)
    print("All filter method tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    test_filter_methods()
