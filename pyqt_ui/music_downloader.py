"""MusicDL Wrapper Class - Singleton Pattern"""
import threading
from musicdl.musicdl import MusicClient
from .config import DOWNLOAD_DIR, DEFAULT_SOURCES
import logging

logger = logging.getLogger(__name__)


class MusicDownloader:
    """Thread-safe singleton wrapper for MusicDL client"""

    _instance = None
    _lock = threading.Lock()
    _client = None

    def __new__(cls):
        """Ensure only one instance exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize MusicDL client if not already initialized"""
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize MusicClient singleton"""
        try:
            logger.info("Initializing MusicClient...")
            self._client = MusicClient(
                music_sources=DEFAULT_SOURCES,
                init_music_clients_cfg={
                    source: {'work_dir': str(DOWNLOAD_DIR)}
                    for source in DEFAULT_SOURCES
                }
            )
            logger.info("MusicClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MusicClient: {e}")
            raise

    def search(self, keyword, sources=None):
        """
        Search for music

        Args:
            keyword: Search keyword
            sources: List of sources (None = all)

        Returns:
            {source: [song_dict, ...]}
        """
        if self._client is None:
            self._initialize_client()

        sources = sources or DEFAULT_SOURCES
        logger.info(f"Searching for '{keyword}' from {sources}")

        try:
            results = self._client.search(keyword)
            # Filter by selected sources
            return {k: v for k, v in results.items() if k in sources}
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def download(self, songs):
        """
        Download songs

        Args:
            songs: List of song_info dictionaries
        """
        if self._client is None:
            self._initialize_client()

        logger.info(f"Downloading {len(songs)} songs...")
        try:
            self._client.download(songs)
            logger.info("Download completed")
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise
