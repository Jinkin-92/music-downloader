"""Worker Threads for Async Operations"""
from PyQt5.QtCore import QThread, pyqtSignal
from .music_downloader import MusicDownloader
import logging

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
