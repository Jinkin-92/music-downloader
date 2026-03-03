"""
测试单首歌4个源的搜索时间
诊断批量搜索慢的问题
"""
import asyncio
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入并发搜索器
import sys
sys.path.insert(0, 'backend')
from backend.workers.concurrent_search import AsyncConcurrentSearcher

async def test_single_song():
    """测试单首歌搜索所有源的时间"""

    # 测试歌曲
    test_song = {
        'name': '夜曲',
        'singer': '周杰伦',
        'album': '叶惠美'
    }

    # 4个音乐源
    sources = ['NeteaseMusicClient', 'QQMusicClient', 'KugouMusicClient', 'KuwoMusicClient']

    logger.info("=" * 60)
    logger.info(f"开始测试单首歌: {test_song['name']} - {test_song['singer']}")
    logger.info(f"音乐源: {sources}")
    logger.info("=" * 60)

    # 创建搜索器
    searcher = AsyncConcurrentSearcher(
        concurrency=8,  # 使用8并发
        similarity_threshold=0.3
    )

    # 计时搜索
    start_time = time.time()

    result = await searcher.search_single_song(test_song, sources)

    end_time = time.time()
    elapsed = end_time - start_time

    logger.info("=" * 60)
    logger.info(f"搜索完成! 耗时: {elapsed:.2f}秒 ({elapsed/60:.2f}分钟)")
    logger.info(f"匹配成功: {result.has_match}")
    logger.info(f"匹配源: {result.current_source if result.has_match else 'N/A'}")

    if result.has_match and result.current_match:
        logger.info(f"匹配歌曲: {result.current_match.song_name} - {result.current_match.singers}")
        logger.info(f"相似度: {result.current_match.similarity_score:.2%}")

    logger.info(f"候选源数量: {len(result.all_matches)}")
    for source, candidates in result.all_matches.items():
        logger.info(f"  - {source}: {len(candidates)} 个候选")

    searcher.close()

    # 性能分析
    logger.info("=" * 60)
    logger.info("性能分析:")
    logger.info(f"总耗时: {elapsed:.2f}秒")

    if elapsed < 30:
        logger.info("✅ 性能良好 - 单首歌搜索正常")
    elif elapsed < 60:
        logger.info("⚠️ 性能偏慢 - 建议检查网络或API")
    else:
        logger.info("❌ 性能很差 - 可能有API限流或网络问题")

    logger.info("=" * 60)

    return elapsed

if __name__ == '__main__':
    elapsed = asyncio.run(test_single_song())
    print(f"\n总结: 单首歌4源搜索耗时 {elapsed:.2f}秒")
    print(f"预计20首歌耗时: {elapsed * 20 / 60:.1f} 分钟 (无并发)")
    print(f"预计20首歌耗时(8并发): {elapsed * 20 / 8 / 60:.1f} 分钟 (理论值)")
