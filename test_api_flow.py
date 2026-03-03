#!/usr/bin/env python
"""测试API搜索流程"""
import asyncio
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backend.workers.concurrent_search import AsyncConcurrentSearcher
from pyqt_ui.batch.parser import BatchParser

async def test_api_flow():
    """模拟API搜索流程"""
    # 模拟API接收到的数据
    songs_data = [{'name': '证据', 'artist': '杨乃文', 'album': ''}]

    # 构建批量文本（与API代码相同）
    batch_text = '\n'.join([f"{s['name']} - {(s.get('singer') or s.get('artist', ''))}" for s in songs_data])
    print(f'Batch text: {batch_text}')
    print(f'Batch text bytes: {batch_text.encode("utf-8")}')

    # 解析
    parser = BatchParser()
    parsed_songs = parser.parse(batch_text)
    print(f'Parsed: {len(parsed_songs)} songs')
    for song in parsed_songs:
        print(f"  name bytes: {song['name'].encode('utf-8')}")
        print(f"  singer bytes: {song['singer'].encode('utf-8')}")

    # 搜索
    searcher = AsyncConcurrentSearcher(concurrency=2, similarity_threshold=0.3)
    result = await searcher.search_single_song(parsed_songs[0], ['KugouMusicClient', 'KuwoMusicClient'])

    print(f'Result: has_match={result.has_match}')
    if result.current_match:
        print(f'  Match: {result.current_match.song_name} - {result.current_match.singers}')
        print(f'  Similarity: {result.current_match.similarity_score}')

    # 显示所有候选
    print(f'All candidates: {len(result.all_matches)} sources')
    for source, candidates in result.all_matches.items():
        print(f'  {source}: {len(candidates)} candidates')
        for c in candidates[:3]:  # 只显示前3个
            print(f'    - {c.song_name} - {c.singers} (similarity: {c.similarity_score})')

    searcher.close()

if __name__ == '__main__':
    asyncio.run(test_api_flow())
