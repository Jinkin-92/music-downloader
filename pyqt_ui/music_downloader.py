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
            # Convert SongInfo objects to dicts
            formatted_results = {}
            for source, songs in results.items():
                if source in sources:
                    formatted_results[source] = [
                        self._songinfo_to_dict(song) for song in songs
                    ]
            return formatted_results
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def search_single_source(self, keyword, source):
        """
        Search for music from a single source only

        Args:
            keyword: Search keyword
            source: Single source name (e.g., 'QQMusicClient')

        Returns:
            {source: [song_dict, ...]} or {} if no results
        """
        logger.info(f"Searching single source '{source}' for '{keyword}'")
        
        try:
            # Create a temporary MusicClient with only one source
            from musicdl.musicdl import MusicClient
            from pathlib import Path
            
            temp_client = MusicClient(
                music_sources=[source],
                init_music_clients_cfg={
                    source: {'work_dir': str(DOWNLOAD_DIR)}
                }
            )
            
            # Search only this source
            results = temp_client.search(keyword)
            
            # Convert SongInfo objects to dicts
            formatted_results = {}
            for src, songs in results.items():
                if src == source:
                    formatted_results[source] = [
                        self._songinfo_to_dict(song) for song in songs
                    ]
            
            logger.info(f"Found {len(formatted_results.get(source, []))} results from {source}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Single source search error for {source}: {e}")
            return {}

    def _songinfo_to_dict(self, song_info):
        """Convert SongInfo object to dictionary"""
        return {
            'song_name': getattr(song_info, 'song_name', ''),
            'singers': getattr(song_info, 'singers', ''),
            'album': getattr(song_info, 'album', ''),
            'file_size': getattr(song_info, 'file_size', ''),
            'duration': getattr(song_info, 'duration', ''),
            'source': getattr(song_info, 'source', ''),
            'ext': getattr(song_info, 'ext', ''),
            'song_info_obj': song_info  # Keep reference for download
        }

    def download(self, songs, download_dir=None):
        """
        Download songs

        Args:
            songs: List of song_info dictionaries
            download_dir: Optional custom download directory (Path or str)
        """
        # Use custom directory if provided, otherwise use default client
        if download_dir:
            logger.info(f"[CUSTOM PATH] Downloading to custom directory: {download_dir}")
            logger.info(f"[CUSTOM PATH] Type: {type(download_dir)}")
            # Create a temporary MusicClient with custom download directory
            from musicdl.musicdl import MusicClient
            
            temp_client = MusicClient(
                music_sources=DEFAULT_SOURCES,
                init_music_clients_cfg={
                    source: {'work_dir': str(download_dir)}
                    for source in DEFAULT_SOURCES
                }
            )
            client = temp_client
        else:
            # Use default client
            if self._client is None:
                self._initialize_client()
            client = self._client
            logger.warning(f"[DEFAULT PATH] Downloading to default directory: {DOWNLOAD_DIR}")
            logger.warning(f"[DEFAULT PATH] custom download_dir was: {download_dir}")

        logger.info(f"Downloading {len(songs)} songs...")
        try:
            # Extract SongInfo objects from dicts
            song_info_objects = []
            for song_dict in songs:
                song_obj = song_dict.get('song_info_obj')
                if song_obj:
                    song_info_objects.append(song_obj)
                else:
                    logger.warning(f"No song_info_obj found in: {song_dict}")

            if not song_info_objects:
                raise ValueError("No valid SongInfo objects to download")

            # CRITICAL FIX: Modify work_dir in each SongInfo object
            # musicdl downloads use song_info.work_dir, not client's work_dir
            if download_dir:
                for song_obj in song_info_objects:
                    if hasattr(song_obj, 'work_dir'):
                        old_dir = getattr(song_obj, 'work_dir', '')
                        song_obj.work_dir = str(download_dir)
                        logger.info(f"Modified SongInfo work_dir: {old_dir} -> {download_dir}")

            client.download(song_info_objects)
            logger.info("Download completed")
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise
