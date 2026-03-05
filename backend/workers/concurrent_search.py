"""
异步并发搜索器 - asyncio版本

替代PyQt6的QThreadPool + QRunnable模式，使用asyncio实现并发搜索。
保持5x性能提升（100首歌80秒），同时提供更好的异步支持。

核心改造：
- QThreadPool(max_workers=5) → asyncio.Semaphore(5)
- QRunnable → asyncio.Task
- PyQt6信号 → 返回值 + SSE推送
"""
import asyncio
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from core import MusicDownloader, BatchParser, SongMatcher, BatchSongMatch, MatchCandidate, DEFAULT_SOURCES
from core.song_cache import song_info_cache

logger = logging.getLogger(__name__)


class AsyncConcurrentSearcher:
    """
    异步并发搜索器

    使用asyncio.Semaphore实现并发控制，替代PyQt6的QThreadPool。
    默认5个并发worker，保持5x性能提升。

    性能对比：
    - PyQt6 QThreadPool: 100首歌 ~80秒
    - asyncio: 100首歌 ~80秒（相同性能）
    - 优势: 更轻量，更好的异步支持，适合FastAPI
    """

    def __init__(self, concurrency: int = 5, similarity_threshold: Optional[float] = None):
        """
        初始化并发搜索器

        Args:
            concurrency: 并发搜索数量，默认5（保持原有性能）
            similarity_threshold: 相似度阈值 (0.0-1.0)，None使用默认值(0.6)
        """
        self.semaphore = asyncio.Semaphore(concurrency)
        self.downloader = MusicDownloader()
        self.matcher = SongMatcher()
        self.thread_pool = ThreadPoolExecutor(max_workers=concurrency)
        self.similarity_threshold = similarity_threshold

        logger.info(f"AsyncConcurrentSearcher initialized with concurrency={concurrency}, similarity_threshold={similarity_threshold}")

    async def search_single_song(
        self,
        parsed_song: Dict,
        sources: List[str]
    ) -> BatchSongMatch:
        """
        搜索单首歌（异步）

        并发搜索所有音乐源，然后匹配最佳结果。

        Args:
            parsed_song: 解析后的歌曲信息 {'name': '歌名', 'singer': '歌手'}
            sources: 要搜索的音乐源列表

        Returns:
            BatchSongMatch对象，包含最佳匹配和所有候选
        """
        async with self.semaphore:
            try:
                # 并发搜索所有源
                search_tasks = [
                    self._search_source(parsed_song, source)
                    for source in sources
                ]

                # 等待所有搜索完成
                results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

                # 处理结果和异常
                all_results = []
                for result in results_list:
                    if isinstance(result, Exception):
                        logger.warning(f"Search source failed: {result}")
                        continue
                    all_results.extend(result)

                # 匹配最佳结果（复用SongMatcher逻辑）
                return self._create_batch_song_match(parsed_song, all_results, sources)

            except Exception as e:
                logger.error(f"Error searching song {parsed_song}: {e}")
                # 返回无匹配结果
                return BatchSongMatch(
                    query=parsed_song,
                    all_matches={},
                    has_match=False
                )

    def _calculate_combined_similarity(self, parsed_song: Dict, result: Dict) -> float:
        """
        计算完整的相似度分数（歌名50% + 歌手40% + 专辑10%）

        Args:
            parsed_song: 解析后的歌曲信息 {'name': '歌名', 'singer': '歌手', 'album': '专辑'}
            result: 搜索结果字典

        Returns:
            相似度分数（0.0-1.0）
        """
        query_name = parsed_song.get('name', '')
        query_singer = parsed_song.get('singer', '')
        query_album = parsed_song.get('album', '')

        result_name = result.get('song_name', '')
        result_singer = result.get('singers', '')
        result_album = result.get('album', '')

        # 计算各部分相似度
        name_sim = self.matcher.calculate_similarity(query_name, result_name)
        singer_sim = self.matcher.calculate_similarity(query_singer, result_singer)
        album_sim = self.matcher.calculate_similarity(query_album, result_album) if query_album and result_album else 0.0

        # 组合相似度：歌名50% + 歌手40% + 专辑10%
        combined_score = (name_sim * 0.5) + (singer_sim * 0.4) + (album_sim * 0.1)

        return combined_score

    def _calculate_similarity_breakdown(self, parsed_song: Dict, result: Dict) -> Dict:
        """
        计算相似度分解（用于前端展示详细分解）

        Args:
            parsed_song: 解析后的歌曲信息
            result: 搜索结果字典

        Returns:
            包含 name_sim, singer_sim, album_sim, combined 的字典
        """
        query_name = parsed_song.get('name', '')
        query_singer = parsed_song.get('singer', '')
        query_album = parsed_song.get('album', '')

        result_name = result.get('song_name', '')
        result_singer = result.get('singers', '')
        result_album = result.get('album', '')

        # 计算各部分相似度
        name_sim = self.matcher.calculate_similarity(query_name, result_name)
        singer_sim = self.matcher.calculate_similarity(query_singer, result_singer)
        album_sim = self.matcher.calculate_similarity(query_album, result_album) if query_album and result_album else 0.0

        # 组合相似度：歌名50% + 歌手40% + 专辑10%
        combined_score = (name_sim * 0.5) + (singer_sim * 0.4) + (album_sim * 0.1)

        return {
            'name_sim': name_sim,
            'singer_sim': singer_sim,
            'album_sim': album_sim,
            'combined': combined_score
        }

    def _filter_by_duration(self, result: Dict, min_seconds: int = 35) -> bool:
        """
        过滤时长过短的结果（过滤试听片段）

        Args:
            result: 搜索结果字典
            min_seconds: 最小时长（秒），默认35秒

        Returns:
            True 表示保留，False 表示过滤掉
        """
        duration_str = result.get('duration', '')
        if not duration_str:
            return True  # 无时长信息，保留

        try:
            # 解析时长格式 "分:秒" 如 "3:45"
            parts = duration_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                total_seconds = minutes * 60 + seconds
                return total_seconds >= min_seconds
            elif len(parts) == 1:
                # 只有秒数的情况
                seconds = int(parts[0])
                return seconds >= min_seconds
        except (ValueError, IndexError):
            pass  # 解析失败，保留

        return True  # 默认保留

    async def _search_source(self, song: Dict, source: str) -> List:
        """
        搜索单个源（asyncio包装）

        MusicDownloader.search是同步的，需要在线程池中运行。
        使用run_in_executor避免阻塞事件循环。

        Args:
            song: 歌曲信息
            source: 音乐源名称

        Returns:
            该源的搜索结果列表
        """
        loop = asyncio.get_event_loop()
        keyword = f"{song['name']} {song['singer']}"

        try:
            # 在线程池中运行同步搜索
            results = await loop.run_in_executor(
                self.thread_pool,
                self.downloader.search_single_source,
                keyword,
                source
            )

            # search_single_source返回 {source: [songs]}
            return results.get(source, [])

        except Exception as e:
            logger.error(f"Error searching {source} for {keyword}: {e}")
            return []

    def _create_batch_song_match(
        self,
        parsed_song: Dict,
        all_results: List,
        sources_searched: List[str]
    ) -> BatchSongMatch:
        """
        创建BatchSongMatch对象

        复用SongMatcher的逻辑，匹配最佳结果并创建候选列表。

        Args:
            parsed_song: 原始查询
            all_results: 所有搜索结果
            sources_searched: 搜索的源列表

        Returns:
            BatchSongMatch对象
        """
        # 使用SongMatcher找到最佳匹配（传入自定义阈值）
        best_match = SongMatcher.find_best_match(
            parsed_song,
            all_results,
            threshold=self.similarity_threshold
        )

        # 记录搜索结果数量
        logger.info(f"[匹配] 查询: {parsed_song.get('name')} - {parsed_song.get('singer')}, 搜索结果数: {len(all_results)}")

        if best_match:
            # 创建候选列表（所有结果按相似度排序）
            candidates = []
            for result in all_results:
                # 时长过滤：排除35秒以下的试听片段
                if not self._filter_by_duration(result, min_seconds=35):
                    logger.debug(f"过滤短音频: {result.get('song_name')} - 时长 {result.get('duration')}")
                    continue

                # 计算相似度分解（包含各部分得分）
                breakdown = self._calculate_similarity_breakdown(parsed_song, result)

                # 将 SongInfo 对象存入缓存，生成 song_id
                song_info_obj = result.get('song_info_obj')
                song_id = None
                if song_info_obj is not None:
                    song_id = song_info_cache.store(
                        song_info_obj,
                        result.get('song_name', ''),
                        result.get('singers', ''),
                        result.get('source', '')
                    )

                candidates.append(MatchCandidate(
                    song_name=result.get('song_name', ''),
                    singers=result.get('singers', ''),
                    album=result.get('album', ''),
                    file_size=result.get('file_size', ''),
                    duration=result.get('duration', ''),
                    source=result.get('source', ''),
                    ext=result.get('ext', ''),
                    similarity_score=breakdown['combined'],
                    song_info_obj=song_info_obj,
                    # 相似度分解字段
                    name_similarity=breakdown['name_sim'],
                    singer_similarity=breakdown['singer_sim'],
                    album_similarity=breakdown['album_sim'],
                    # 下载相关字段
                    download_url=result.get('download_url'),
                    duration_s=result.get('duration_s') or 0,
                    # 缓存 ID（用于后续下载）
                    song_id=song_id
                ))

            # 按相似度排序
            candidates.sort(key=lambda c: c.similarity_score, reverse=True)

            # 获取最佳匹配的源
            best_source = best_match.get('source', 'Unknown')

            # 找到最佳匹配对应的候选（使用完整的相似度计算）
            best_similarity = 0.0
            best_name_sim = 0.0
            best_singer_sim = 0.0
            best_album_sim = 0.0
            for candidate in candidates:
                if candidate.song_name == best_match.get('song_name', '') and \
                   candidate.singers == best_match.get('singers', ''):
                    best_similarity = candidate.similarity_score
                    best_name_sim = candidate.name_similarity
                    best_singer_sim = candidate.singer_similarity
                    best_album_sim = candidate.album_similarity
                    break

            # 创建MatchCandidate对象作为current_match
            # 找到最佳匹配的候选
            best_candidate_from_list = None
            for candidate in candidates:
                if candidate.song_name == best_match.get('song_name', '') and \
                   candidate.singers == best_match.get('singers', ''):
                    best_candidate_from_list = candidate
                    break

            # 使用找到的候选或创建新的
            if best_candidate_from_list:
                best_candidate = best_candidate_from_list
            else:
                # 如果没找到，手动创建（存入缓存）
                song_info_obj = best_match.get('song_info_obj')
                song_id = None
                if song_info_obj is not None:
                    song_id = song_info_cache.store(
                        song_info_obj,
                        best_match.get('song_name', ''),
                        best_match.get('singers', ''),
                        best_match.get('source', '')
                    )

                best_candidate = MatchCandidate(
                    song_name=best_match.get('song_name', ''),
                    singers=best_match.get('singers', ''),
                    album=best_match.get('album', ''),
                    file_size=best_match.get('file_size', ''),
                    duration=best_match.get('duration', ''),
                    source=best_source,
                    ext=best_match.get('ext', ''),
                    similarity_score=best_similarity,
                    song_info_obj=song_info_obj,
                    # 相似度分解字段
                    name_similarity=best_name_sim,
                    singer_similarity=best_singer_sim,
                    album_similarity=best_album_sim,
                    # 下载相关字段
                    download_url=best_match.get('download_url'),
                    duration_s=best_match.get('duration_s') or 0,
                    # 缓存 ID
                    song_id=song_id
                )

            # 将候选按源分组存储
            all_matches = {}
            for candidate in candidates[:5]:
                source = candidate.source
                if source not in all_matches:
                    all_matches[source] = []
                all_matches[source].append(candidate)

            return BatchSongMatch(
                query=parsed_song,
                current_match=best_candidate,
                current_source=best_source,
                all_matches=all_matches,
                has_match=True
            )
        else:
            # 无匹配结果 - 记录详细原因
            query_name = parsed_song.get('name', '')
            query_singer = parsed_song.get('singer', '')
            if all_results:
                # 有搜索结果但相似度不足
                logger.warning(f"[匹配失败] {query_name} - {query_singer}: 搜索到 {len(all_results)} 个结果但相似度不足阈值 {self.similarity_threshold}")
                # 记录最高相似度
                if all_results:
                    best_score = 0
                    for r in all_results:
                        score = self._calculate_combined_similarity(parsed_song, r)
                        if score > best_score:
                            best_score = score
                    logger.warning(f"[匹配失败] 最高相似度: {best_score:.2f}")
            else:
                # 无搜索结果
                logger.warning(f"[匹配失败] {query_name} - {query_singer}: 无搜索结果")

            return BatchSongMatch(
                query=parsed_song,
                all_matches={},
                has_match=False
            )

    async def search_batch(
        self,
        batch_text: str,
        sources: Optional[List[str]] = None
    ) -> Dict:
        """
        批量搜索（主入口）

        解析批量文本，并发搜索所有歌曲。

        Args:
            batch_text: 批量文本，格式为"歌名 - 歌手"每行一首
            sources: 音乐源列表，None表示使用全部

        Returns:
            {
                'total': 总歌曲数,
                'matched': 匹配成功数,
                'matches': {原始行: BatchSongMatch},
                'sources_searched': 搜索的源列表
            }
        """
        sources = sources or DEFAULT_SOURCES
        logger.info(f"Starting batch search with {len(sources)} sources")

        # 解析批量文本
        parser = BatchParser()
        parsed_songs = parser.parse(batch_text)
        total_songs = len(parsed_songs)

        logger.info(f"Parsed {total_songs} songs from batch text")

        # 并发搜索所有歌
        search_tasks = [
            self.search_single_song(song, sources)
            for song in parsed_songs
        ]

        # 等待所有搜索完成
        matches_list = await asyncio.gather(*search_tasks)

        # 构建结果字典
        matches = {}
        matched_count = 0

        for parsed_song, match in zip(parsed_songs, matches_list):
            original_line = parsed_song.get('original_line', f"{parsed_song['name']} - {parsed_song['singer']}")
            matches[original_line] = match

            if match.current_match:
                matched_count += 1

        logger.info(f"Batch search completed: {matched_count}/{total_songs} matched")

        return {
            'total': total_songs,
            'matched': matched_count,
            'matches': matches,
            'sources_searched': sources
        }

    def close(self):
        """关闭线程池"""
        self.thread_pool.shutdown(wait=True)
        logger.info("AsyncConcurrentSearcher closed")


async def main():
    """测试入口"""
    searcher = AsyncConcurrentSearcher(concurrency=5)

    # 测试单歌搜索
    song = {'name': '夜曲', 'singer': '周杰伦'}
    result = await searcher.search_single_song(song, DEFAULT_SOURCES[:2])
    print(f"Best match: {result.current_match}")

    # 测试批量搜索
    batch_text = """夜曲 - 周杰伦
晴天 - 周杰伦
七里香 - 周杰伦"""

    batch_result = await searcher.search_batch(batch_text, DEFAULT_SOURCES[:2])
    print(f"Batch result: {batch_result['matched']}/{batch_result['total']} matched")

    searcher.close()


if __name__ == '__main__':
    asyncio.run(main())
