"""Worker Threads for Async Operations"""

from PyQt6.QtCore import QThread, pyqtSignal
from .music_downloader import MusicDownloader
from .batch.parser import BatchParser
from .batch.matcher import SongMatcher
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class SearchWorker(QThread):
    """Worker thread for music search"""

    # Signals
    search_started = pyqtSignal()
    search_progress = pyqtSignal(str)  # Status message
    search_finished = pyqtSignal(dict)  # Results
    search_error = pyqtSignal(str)  # Error message

    def __init__(self, keyword, sources):
        super().__init__()
        self.keyword = keyword
        self.sources = sources
        self.downloader = MusicDownloader()

    def run(self):
        """Execute search in background thread"""
        try:
            self.search_started.emit()
            logger.info(f"Search started: {self.keyword}")

            self.search_progress.emit(f"Searching for '{self.keyword}'...")

            results = self.downloader.search(self.keyword, self.sources)

            total_results = sum(len(songs) for songs in results.values())
            self.search_progress.emit(f"Found {total_results} songs")

            logger.info(f"Search completed: {total_results} results")
            self.search_finished.emit(results)

        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            self.search_error.emit(error_msg)


class DownloadWorker(QThread):
    """Worker thread for music download"""

    # Signals
    download_started = pyqtSignal()
    download_progress = pyqtSignal(str, int)  # message, progress %
    download_finished = pyqtSignal(list)  # successful downloads
    download_error = pyqtSignal(str)

    def __init__(self, songs, download_dir=None):
        super().__init__()
        self.songs = songs
        self.download_dir = download_dir
        self.downloader = MusicDownloader()

    def run(self):
        """Execute download in background thread"""
        try:
            self.download_started.emit()
            logger.info(f"Download started: {len(self.songs)} songs")

            for i, song in enumerate(self.songs):
                song_name = song.get("song_name", "Unknown")
                self.download_progress.emit(
                    f"Downloading: {song_name}...", int((i / len(self.songs)) * 100)
                )

            self.downloader.download(self.songs, download_dir=self.download_dir)

            self.download_progress.emit("Download complete!", 100)
            logger.info("Download completed successfully")
            self.download_finished.emit(self.songs)

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg)
            self.download_error.emit(error_msg)


class BatchSearchWorker(QThread):
    """Worker thread for batch music search with intelligent matching"""

    # Signals
    search_started = pyqtSignal()
    search_progress = pyqtSignal(str, int, int)  # message, current, total
    search_finished = pyqtSignal(object)  # BatchSearchResult对象
    search_error = pyqtSignal(str)  # Error message

    def __init__(
        self, batch_text, sources, search_all_sources=True, max_candidates_per_source=5
    ):
        super().__init__()
        self.batch_text = batch_text
        self.sources = sources
        self.search_all_sources = search_all_sources
        self.max_candidates_per_source = max_candidates_per_source
        self.downloader = MusicDownloader()
        self.parser = BatchParser()
        self.matcher = SongMatcher()

    def run(self):
        """Execute batch search in background thread"""
        try:
            self.search_started.emit()
            logger.info(
                f"Batch search started with search_all_sources={self.search_all_sources}"
            )

            # Step 1: Parse batch input
            self.search_progress.emit("Parsing batch input...", 0, 0)
            parsed_songs = self.parser.parse(self.batch_text)

            if not parsed_songs:
                self.search_error.emit("No valid songs found in batch input")
                return

            logger.info(f"Parsed {len(parsed_songs)} songs from batch input")

            # Step 2: Search for each song
            from .batch.models import BatchSongMatch, BatchSearchResult, MatchCandidate
            import time

            start_time = time.time()
            matches = {}
            total_songs = len(parsed_songs)

            for idx, parsed_song in enumerate(parsed_songs):
                song_name = parsed_song["name"]
                singer = parsed_song["singer"]
                original_line = parsed_song["original_line"]

                self.search_progress.emit(
                    f"Searching [{idx + 1}/{total_songs}]: {song_name} - {singer}",
                    idx + 1,
                    total_songs,
                )

                # 创建BatchSongMatch对象
                song_match = BatchSongMatch(query=parsed_song, searched_sources=[])

                # 搜索所有源（或者找到第一个匹配就停止）
                for source in self.sources:
                    self.search_progress.emit(
                        f"  - Searching {source}...", idx + 1, total_songs
                    )

                    # 搜索单个源
                    search_results = self.downloader.search_single_source(
                        f"{song_name} {singer}", source
                    )

                    # 提取结果
                    source_results = search_results.get(source, [])
                    song_match.searched_sources.append(source)

                    if source_results:
                        # 计算所有结果的相似度并排序
                        candidates = []
                        for result in source_results:
                            # 计算相似度
                            name_sim = self.matcher.calculate_similarity(
                                song_name, result.get("song_name", "")
                            )
                            singer_sim = self.matcher.calculate_similarity(
                                singer, result.get("singers", "")
                            )
                            combined_score = (name_sim * 0.7) + (singer_sim * 0.3)

                            # 创建MatchCandidate
                            candidate = MatchCandidate(
                                song_name=result.get("song_name", ""),
                                singers=result.get("singers", ""),
                                album=result.get("album", ""),
                                file_size=result.get("file_size", ""),
                                duration=result.get("duration", ""),
                                source=source,
                                ext=result.get("ext", ""),
                                similarity_score=combined_score,
                                song_info_obj=result.get("song_info_obj"),
                            )
                            candidates.append(candidate)

                        # 按相似度降序排序
                        candidates.sort(key=lambda x: x.similarity_score, reverse=True)

                        # 限制每个源最多保存max_candidates_per_source个候选
                        candidates = candidates[: self.max_candidates_per_source]

                        # 保存到all_matches
                        song_match.all_matches[source] = candidates

                        # 如果找到匹配且配置为不搜索所有源，则设置当前匹配并break
                        best_candidate = candidates[0]  # 最相似的
                        if (
                            best_candidate.similarity_score
                            >= self.matcher.SIMILARITY_THRESHOLD
                        ):
                            if not song_match.current_match:  # 只设置第一次找到的匹配
                                song_match.current_match = best_candidate
                                song_match.current_source = source
                                song_match.has_match = True

                            if not self.search_all_sources:
                                logger.info(
                                    f"Found match in {source}, stopping search for this song"
                                )
                                break

                # 如果没有找到匹配，但有结果，选择相似度最高的
                if not song_match.current_match and song_match.all_matches:
                    # 跨所有源找到最佳匹配
                    all_candidates = song_match.get_all_candidates()
                    if all_candidates:
                        best_overall = all_candidates[0]  # 已按相似度排序
                        song_match.current_match = best_overall
                        song_match.current_source = best_overall.source
                        song_match.has_match = True

                # 保存到结果
                matches[original_line] = song_match

                if not song_match.has_match:
                    logger.warning(f"No match found: {song_name} - {singer}")

            search_time = time.time() - start_time

            # Step 3: 创建BatchSearchResult
            result = BatchSearchResult(
                total_songs=total_songs,
                matches=matches,
                search_time=search_time,
                sources_searched=self.sources,
            )

            # 发送结果
            matched_count = result.get_match_count()
            self.search_progress.emit(
                f"Matched {matched_count}/{total_songs} songs", total_songs, total_songs
            )
            logger.info(
                f"Batch search completed: {matched_count}/{total_songs} matched in {search_time:.2f}s"
            )

            self.search_finished.emit(result)

        except Exception as e:
            error_msg = f"Batch search failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.search_error.emit(error_msg)
