"""测试并发搜索功能"""
import sys
from pyqt_ui.workers import ConcurrentSearchWorker
from pyqt_ui.config import DEFAULT_SOURCES

# 测试数据
test_batch_text = """平凡之路 - 朴树
告白气球 - 周杰伦
稻香 - 周杰伦
"""

def test_concurrent_search():
    """测试并发搜索功能"""
    print(f"Testing concurrent search with {len(test_batch_text.splitlines())} songs...")

    # 创建Worker
    worker = ConcurrentSearchWorker(
        batch_text=test_batch_text,
        sources=["QQMusicClient"],  # 只测试一个源
        search_all_sources=False,
        max_candidates_per_source=3
    )

    # 连接信号
    worker.search_started.connect(lambda: print("Search started"))
    worker.search_progress.connect(lambda msg, cur, total: print(f"[{cur}/{total}] {msg}"))
    worker.search_finished.connect(on_search_finished)
    worker.search_error.connect(lambda err: print(f"Error: {err}"))

    # 运行
    worker.run()

def on_search_finished(result):
    """处理搜索完成"""
    print(f"\nSearch completed in {result.search_time:.2f}s")
    print(f"Matched: {result.get_match_count()}/{result.total_songs}")

    # 显示匹配结果
    for original_line, song_match in result.matches.items():
        if song_match.has_match:
            match = song_match.current_match
            print(f"  {original_line}")
            print(f"    -> {match.song_name} - {match.singers} ({match.source})")
            print(f"    Similarity: {match.similarity_score:.2f}")
        else:
            print(f"  {original_line}")
            print(f"    -> No match found")

if __name__ == "__main__":
    test_concurrent_search()
