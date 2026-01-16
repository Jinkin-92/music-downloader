"""单首歌搜索任务"""
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
from ..music_downloader import MusicDownloader
from ..batch.matcher import SongMatcher
from ..batch.models import BatchSongMatch, MatchCandidate
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

            # 串行搜索所有源
            for source in self.sources:
                self.signals.progress.emit(f"正在搜索 {source}: {song_name} - {singer}")

                logger.debug(f"Searching source '{source}' for '{song_name}'")

                # 调用单源搜索
                results = self.downloader.search_single_source(
                    f"{song_name} {singer}", source
                )

                # ✅ 修复: search_single_source 返回 {source: [song_dicts]}
                # 需要提取该源的SongInfo列表
                if source not in results or not results[source]:
                    logger.debug(f"No results from '{source}'")
                    continue

                song_info_list = results[source]
                logger.debug(f"Got {len(song_info_list)} results from '{source}'")

                # ✅ 修复: results[source] 已经是字典列表（search_single_source已转换）
                # 直接使用字典，不需要再调用 _songinfo_to_dict
                candidates = []
                for song_dict in song_info_list:
                    # ✅ 分别计算歌名和歌手的相似度
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

            # ✅ 优化：在所有源搜索完后，选择相似度最高的结果作为默认匹配
            # 收集所有源中的所有候选
            all_candidates_from_all_sources = []
            for source, candidates in song_match.all_matches.items():
                all_candidates_from_all_sources.extend(candidates)

            if all_candidates_from_all_sources:
                # 按相似度排序，选择最高的
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
                    # 相似度最高但仍 < 0.6，保存最佳候选但不标记为自动匹配
                    song_match.current_match = best_overall_match
                    song_match.current_source = best_overall_match.source
                    song_match.has_match = False  # 保持 False，表示未达到自动匹配标准

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
