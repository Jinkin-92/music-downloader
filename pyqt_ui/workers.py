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
