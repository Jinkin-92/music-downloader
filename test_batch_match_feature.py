"""简单测试批量下载切换匹配功能"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyqt_ui.batch.models import (
    MatchCandidate,
    BatchSongMatch,
    BatchSearchResult,
    MatchSource,
)
from pyqt_ui.batch.matcher import SongMatcher
from pyqt_ui.batch.parser import BatchParser


def test_models():
    """测试数据模型"""
    print("=" * 50)
    print("测试数据模型...")
    print("=" * 50)

    # 创建MatchCandidate
    candidate = MatchCandidate(
        song_name="测试歌曲",
        singers="测试歌手",
        album="测试专辑",
        file_size="5.2MB",
        duration="3:45",
        source="QQMusicClient",
        ext="mp3",
        similarity_score=0.85,
        song_info_obj=None,
    )

    print(
        f"✓ 创建MatchCandidate: {candidate.song_name} - 相似度: {candidate.similarity_score:.2%}"
    )

    # 转换为字典
    candidate_dict = candidate.to_dict()
    print(f"✓ 转换为dict: {candidate_dict['song_name']}")

    # 创建BatchSongMatch
    song_match = BatchSongMatch(
        query={
            "name": "测试歌曲",
            "singer": "测试歌手",
            "original_line": "测试歌曲 - 测试歌手",
        },
        current_match=candidate,
        current_source="QQMusicClient",
        match_source_type=MatchSource.AUTO,
        all_matches={
            "QQMusicClient": [candidate],
            "NeteaseMusicClient": [
                MatchCandidate(
                    song_name="测试歌曲",
                    singers="测试歌手",
                    album="测试专辑",
                    file_size="4.8MB",
                    duration="3:42",
                    source="NeteaseMusicClient",
                    ext="flac",
                    similarity_score=0.78,
                    song_info_obj=None,
                )
            ],
        },
        has_match=True,
        searched_sources=["QQMusicClient", "NeteaseMusicClient"],
    )

    print(
        f"✓ 创建BatchSongMatch: {song_match.query['name']} - 候选数: {song_match.get_all_candidates_count()}个"
    )

    # 测试方法
    print(
        f"✓ 当前匹配: {song_match.current_match.song_name if song_match.current_match else 'None'}"
    )
    print(f"✓ 所有候选数: {len(song_match.get_all_candidates())}")

    print("\n" + "=" * 50)
    print("数据模型测试通过！✓")
    print("=" * 50)


def test_matcher():
    """测试匹配算法"""
    print("\n" + "=" * 50)
    print("测试匹配算法...")
    print("=" * 50)

    matcher = SongMatcher()

    # 测试1：完全匹配
    sim1 = matcher.calculate_similarity("告白气球", "告白气球")
    print(f"✓ 完全匹配相似度: {sim1:.2%}")
    assert sim1 > 0.95

    # 测试2：部分匹配
    sim2 = matcher.calculate_similarity("告白气球", "告白气球 live")
    print(f"✓ 部分匹配相似度: {sim2:.2%}")
    assert 0.8 < sim2 < 0.95

    # 测试3：不匹配
    sim3 = matcher.calculate_similarity("告白气球", "七里香")
    print(f"✓ 不匹配相似度: {sim3:.2%}")
    assert sim3 < 0.6

    # 测试4：判断匹配
    result1 = matcher.is_match("告白气球", "周杰伦", "告白气球", "周杰伦")
    print(f"✓ 匹配判断测试1: {result1}")
    assert result1 == True

    result2 = matcher.is_match("告白气球", "周杰伦", "告白气球 live", "林俊杰")
    print(f"✓ 匹配判断测试2: {result2}")
    assert result2 == False

    print("\n" + "=" * 50)
    print("匹配算法测试通过！✓")
    print("=" * 50)


def test_parser():
    """测试批量解析器"""
    print("\n" + "=" * 50)
    print("测试批量解析器...")
    print("=" * 50)

    parser = BatchParser()

    # 测试1：正常输入
    text1 = """告白气球 - 周杰伦
没关系 - 容祖儿
七里香 - 林俊杰"""
    songs1 = parser.parse(text1)
    print(f"✓ 解析{len(songs1)}首歌曲:")
    for song in songs1:
        print(f"  - {song['name']} - {song['singer']}")
    assert len(songs1) == 3

    # 测试2：空输入
    try:
        parser.parse("")
        print("❌ 空输入应该抛出异常")
        assert False
    except ValueError as e:
        print(f"✓ 空输入正确抛出异常: {e}")

    # 测试3：超过限制
    text3 = "\n".join([f"歌曲{i} - 歌手{i}" for i in range(1, 201)])
    try:
        parser.parse(text3)
        print("❌ 超过限制应该抛出异常")
        assert False
    except ValueError as e:
        print(f"✓ 超过限制正确抛出异常: {e}")

    print("\n" + "=" * 50)
    print("批量解析器测试通过！✓")
    print("=" * 50)


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("批量下载切换匹配功能 - 单元测试")
    print("=" * 50 + "\n")

    test_models()
    test_matcher()
    test_parser()

    print("\n" + "=" * 50)
    print("所有测试通过！✓")
    print("=" * 50)
    print("\n提示：UI功能需要在PyQt6环境中运行才能完整测试。")
