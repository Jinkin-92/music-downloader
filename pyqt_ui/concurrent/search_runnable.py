"""单首歌搜索任务"""
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
from ..music_downloader import MusicDownloader
from core.matcher import SongMatcher
from core.models import BatchSongMatch, MatchCandidate
import logging

logger = logging.getLogger(__name__)


class SearchRunnableSignals(QObject):
    """SearchRunnable的信号类"""

    progress = pyqtSignal(str)  # status message
    error = pyqtSignal(str)  # error message


class SingleSongSearchRunnable(QRunnable):
    """单首歌的搜索任务（在QThreadPool中执行）

    此类封装了单首歌的完整搜索流程：
    1. 串行搜索所有音乐源
    2. 计算相似度并排序
    3. 自动选择最佳匹配
    4. 线程安全地存储结果
    """

    def __init__(
        self,
        parsed_song: dict,
        sources: list,
        result_collector,
        search_all_sources: bool = True,
        max_candidates: int = 5,
    ):
        """初始化搜索任务

        Args:
            parsed_song: 解析后的歌曲信息 {name, singer, original_line}
            sources: 要搜索的音乐源列表
            result_collector: 线程安全的结果收集器
            search_all_sources: 是否搜索所有源（False表示找到匹配就停止）
            max_candidates: 每个源最多保留的候选数量
        """
        super().__init__()
        self.parsed_song = parsed_song
        self.sources = sources
        self.result_collector = result_collector
        self.search_all_sources = search_all_sources
        self.max_candidates = max_candidates

        self.downloader = MusicDownloader()
        self.matcher = SongMatcher()
        self.signals = SearchRunnableSignals()

        logger.debug(f"SingleSongSearchRunnable created for: {parsed_song}")

    def run(self):
        """执行搜索（在后台线程中）"""
        song_name = self.parsed_song.get("name", "")
        singer = self.parsed_song.get("singer", "")
        original_line = self.parsed_song.get("original_line", "")

        try:
            logger.info(f"Searching for '{song_name} - {singer}'")

            # 创建匹配对象
            song_match = BatchSongMatch(
                query=self.parsed_song, all_matches={}, has_match=False
            )

            # 分离 pjmp3 和其他源（pjmp3 作为兜底方案）
            non_pjmp3_sources = [s for s in self.sources if s != "Pjmp3Client"]
            pjmp3_sources = [s for s in self.sources if s == "Pjmp3Client"]

            # 第一步：搜索其他源（非 pjmp3）
            for source in non_pjmp3_sources:
                self.signals.progress.emit(f"正在搜索 {source}: {song_name} - {singer}")

                logger.debug(f"Searching source '{source}' for '{song_name}'")

                # 调用单源搜索
                results = self.downloader.search_single_source(
                    f"{song_name} {singer}", source
                )

                # 处理搜索结果
                if source not in results or not results[source]:
                    logger.debug(f"No results from '{source}'")
                    continue

                song_info_list = results[source]
                logger.debug(f"Got {len(song_info_list)} results from '{source}'")

                # 计算相似度
                candidates = []
                for song_dict in song_info_list:
                    name_sim = self.matcher.calculate_similarity(
                        song_name,
                        song_dict['song_name']
                    )
                    singer_sim = self.matcher.calculate_similarity(
                        singer,
                        song_dict['singers']
                    )

                    # 组合分数（歌名70%，歌手30%）
                    similarity = (name_sim * 0.7) + (singer_sim * 0.3)

                    candidates.append(
                        MatchCandidate(
                            song_name=song_dict["song_name"],
                            singers=song_dict["singers"],
                            album=song_dict.get("album", ""),
                            file_size=song_dict.get("file_size", ""),
                            duration=song_dict.get("duration", ""),
                            source=source,
                            ext=song_dict.get("ext", ""),
                            similarity_score=similarity,
                            song_info_obj=song_dict.get("song_info_obj"),
                        )
                    )

                # 保存前N个最佳候选
                if candidates:
                    candidates.sort(key=lambda x: x.similarity_score, reverse=True)
                    top_candidates = candidates[: self.max_candidates]
                    song_match.all_matches[source] = top_candidates
                    song_match.searched_sources.append(source)

                    best_match = top_candidates[0]
                    logger.debug(
                        f"Best match from '{source}': '{best_match.song_name} - {best_match.singers}' "
                        f"(similarity: {best_match.similarity_score:.2f})"
                    )

            # 第二步：计算其他源的最佳匹配
            best_similarity_from_other_sources = 0.0
            for candidates in song_match.all_matches.values():
                if candidates:
                    best_similarity_from_other_sources = max(
                        best_similarity_from_other_sources,
                        candidates[0].similarity_score
                    )

            # 第三步：判断是否需要搜索 pjmp3（兜底方案）
            # 当其他源的最佳匹配相似度 < 0.7 时，启用 pjmp3
            should_search_pjmp3 = (
                pjmp3_sources and
                best_similarity_from_other_sources < 0.7
            )

            if should_search_pjmp3:
                logger.info(
                    f"其他源最佳匹配相似度 {best_similarity_from_other_sources:.2f} < 0.7，"
                    f"启用 pjmp3 兜底搜索"
                )
                self.signals.progress.emit(
                    f"其他源匹配度较低，尝试 pjmp3: {song_name} - {singer}"
                )

                # 搜索 pjmp3（使用精准匹配）
                from core.pjmp3_client import get_pjmp3_client

                pjmp3 = get_pjmp3_client()
                if pjmp3 and pjmp3.enabled:
                    pjmp3_results = pjmp3.search_with_artist_filter(
                        song_name, singer, limit=self.max_candidates
                    )

                    if pjmp3_results:
                        logger.info(f"pjmp3 找到 {len(pjmp3_results)} 首匹配歌曲")

                        # 计算 pjmp3 结果的相似度
                        pjmp3_candidates = []
                        for song in pjmp3_results:
                            name_sim = self.matcher.calculate_similarity(
                                song_name, song.song_name
                            )
                            singer_sim = self.matcher.calculate_similarity(
                                singer, song.singers
                            )
                            similarity = (name_sim * 0.7) + (singer_sim * 0.3)

                            pjmp3_candidates.append(
                                MatchCandidate(
                                    song_name=song.song_name,
                                    singers=song.singers,
                                    album=song.album,
                                    file_size=song.file_size,
                                    duration=song.duration,
                                    source="Pjmp3Client",
                                    ext=song.ext,
                                    similarity_score=similarity,
                                    song_info_obj=song,
                                )
                            )

                        # 保存 pjmp3 候选
                        if pjmp3_candidates:
                            pjmp3_candidates.sort(
                                key=lambda x: x.similarity_score, reverse=True
                            )
                            song_match.all_matches["Pjmp3Client"] = pjmp3_candidates
                            song_match.searched_sources.append("Pjmp3Client")

                            logger.info(
                                f"pjmp3 最佳匹配: '{pjmp3_candidates[0].song_name} - "
                                f"{pjmp3_candidates[0].singers}' (similarity: "
                                f"{pjmp3_candidates[0].similarity_score:.2f})"
                            )

            # 第四步：在所有源中选出最佳匹配
            all_candidates_from_all_sources = []
            for source, candidates in song_match.all_matches.items():
                all_candidates_from_all_sources.extend(candidates)

            if all_candidates_from_all_sources:
                # 按相似度排序
                all_candidates_from_all_sources.sort(
                    key=lambda x: x.similarity_score, reverse=True
                )
                best_overall_match = all_candidates_from_all_sources[0]

                # 只有当最佳匹配相似度 >= 0.6 时才设置为自动匹配
                if best_overall_match.similarity_score >= 0.6:
                    song_match.current_match = best_overall_match
                    song_match.current_source = best_overall_match.source
                    song_match.has_match = True

                    logger.info(
                        f"Best overall match for '{song_name} - {singer}': "
                        f"'{best_overall_match.song_name} - {best_overall_match.singers}' "
                        f"from '{best_overall_match.source}' "
                        f"(similarity: {best_overall_match.similarity_score:.2f})"
                    )
                else:
                    song_match.current_match = best_overall_match
                    song_match.current_source = best_overall_match.source
                    song_match.has_match = False

                    logger.info(
                        f"Best match for '{song_name} - {singer}' "
                        f"(similarity: {best_overall_match.similarity_score:.2f}) "
                        f"below threshold 0.6, from '{best_overall_match.source}'"
                    )

            # 线程安全地存储结果
            self.result_collector.add_match(original_line, song_match)

            status = "✓" if song_match.has_match else "✗"
            logger.info(
                f"{status} Search completed for '{song_name} - {singer}' "
                f"(sources searched: {len(song_match.searched_sources)})"
            )

        except Exception as e:
            error_msg = f"Search failed for '{song_name} - {singer}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.signals.error.emit(error_msg)
