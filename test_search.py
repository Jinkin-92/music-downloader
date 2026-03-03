#!/usr/bin/env python
"""测试搜索功能"""
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backend.workers.concurrent_search import AsyncConcurrentSearcher

async def test_search():
    """测试搜索"""
    searcher = AsyncConcurrentSearcher(concurrency=2, similarity_threshold=0.3)

    # 测试周杰伦夜曲
    result = await searcher.search_single_song(
        {'name': '夜曲', 'artist': '周杰伦', 'album': ''},
        ['KugouMusicClient', 'KuwoMusicClient']
    )

    print(f'搜索结果: has_match={result.has_match}')
    if result.current_match:
        print(f'最佳匹配: {result.current_match.song_name} - {result.current_match.singers}')
        print(f'相似度: {result.current_match.similarity_score}')
    print(f'所有源: {list(result.all_matches.keys())}')
    for source, candidates in result.all_matches.items():
        print(f'  {source}: {len(candidates)} 个候选')

    searcher.close()

if __name__ == '__main__':
    asyncio.run(test_search())
