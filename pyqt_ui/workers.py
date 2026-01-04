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

    def __init__(self, songs):
        super().__init__()
        self.songs = songs
        self.downloader = MusicDownloader()

    def run(self):
        """Execute download in background thread"""
        try:
            self.download_started.emit()
            logger.info(f"Download started: {len(self.songs)} songs")

            for i, song in enumerate(self.songs):
                song_name = song.get('song_name', 'Unknown')
                self.download_progress.emit(
                    f"Downloading: {song_name}...",
                    int((i / len(self.songs)) * 100)
                )

            self.downloader.download(self.songs)

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
    search_progress = pyqtSignal(str)  # Status message
    search_finished = pyqtSignal(dict)  # Matched results {song_name: [matches]}
    search_error = pyqtSignal(str)  # Error message

    def __init__(self, batch_text, sources):
        super().__init__()
        self.batch_text = batch_text
        self.sources = sources
        self.downloader = MusicDownloader()
        self.parser = BatchParser()
        self.matcher = SongMatcher()

    def run(self):
        """Execute batch search in background thread"""
        try:
            self.search_started.emit()
            logger.info(f"Batch search started with {len(self.batch_text.splitlines())} lines")

            # Step 1: Parse batch input
            self.search_progress.emit("Parsing batch input...")
            parsed_songs = self.parser.parse(self.batch_text)
            
            if not parsed_songs:
                self.search_error.emit("No valid songs found in batch input")
                return

            logger.info(f"Parsed {len(parsed_songs)} songs from batch input")
            self.search_progress.emit(f"Parsed {len(parsed_songs)} songs")

            # Step 2: Search for each song
            matched_results = {}
            total_songs = len(parsed_songs)
            
            for idx, parsed_song in enumerate(parsed_songs):
                song_name = parsed_song['song_name']
                singer = parsed_song['singer']
                
                self.search_progress.emit(
                    f"Searching [{idx+1}/{total_songs}]: {song_name} - {singer}"
                )
                
                # Search across all sources
                search_results = self.downloader.search(
                    f"{song_name} {singer}",
                    self.sources
                )
                
                # Flatten results from all sources
                all_results = []
                for source, songs in search_results.items():
                    all_results.extend(songs)
                
                if all_results:
                    # Use matcher to find best match
                    best_match = self.matcher.find_best_match(
                        parsed_song,
                        all_results
                    )
                    
                    if best_match:
                        matched_results[parsed_song['original']] = {
                            'parsed': parsed_song,
                            'match': best_match,
                            'matched_song_name': getattr(best_match, 'song_name', ''),
                            'matched_singer': getattr(best_match, 'singers', '')
                        }
                        logger.info(f"Match found: {song_name} - {singer}")
                    else:
                        logger.warning(f"No match found: {song_name} - {singer}")
                else:
                    logger.warning(f"No results found: {song_name} - {singer}")

            # Step 3: Send results
            total_matched = len(matched_results)
            self.search_progress.emit(f"Matched {total_matched}/{total_songs} songs")
            logger.info(f"Batch search completed: {total_matched}/{total_songs} matched")
            
            self.search_finished.emit(matched_results)

        except Exception as e:
            error_msg = f"Batch search failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.search_error.emit(error_msg)
