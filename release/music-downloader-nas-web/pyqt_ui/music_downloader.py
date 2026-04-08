"""MusicDL Wrapper Class - Singleton Pattern"""
import threading
from musicdl.musicdl import MusicClient
from .config import DOWNLOAD_DIR, DEFAULT_SOURCES
from core.pjmp3_client import Pjmp3Client, get_pjmp3_client
import logging

logger = logging.getLogger(__name__)


class MusicDownloader:
    """Thread-safe singleton wrapper for MusicDL client"""

    _instance = None
    _lock = threading.Lock()
    _client = None
    _pjmp3_client = None  # Pjmp3 独立客户端

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
        if self._pjmp3_client is None:
            self._pjmp3_client = get_pjmp3_client()

    def _initialize_client(self):
        """Initialize MusicClient singleton"""
        try:
            logger.info("Initializing MusicClient...")
            # 设置超时为180秒，避免API响应慢导致超时（musicdl搜索很慢）
            request_overrides = {
                source: {'timeout': (30, 180)}  # (连接超时30s, 读取超时180s)
                for source in DEFAULT_SOURCES
            }
            self._client = MusicClient(
                music_sources=DEFAULT_SOURCES,
                init_music_clients_cfg={
                    source: {'work_dir': str(DOWNLOAD_DIR)}
                    for source in DEFAULT_SOURCES
                },
                requests_overrides=request_overrides
            )
            logger.info("MusicClient initialized successfully with 180s timeout")
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
        if self._pjmp3_client is None:
            self._pjmp3_client = get_pjmp3_client()

        sources = sources or DEFAULT_SOURCES
        logger.info(f"Searching for '{keyword}' from {sources}")

        try:
            # 分离 Spotify、Pjmp3 和其他源
            musicdl_sources = [s for s in sources if s not in ("SpotifyClient", "Pjmp3Client")]
            spotify_sources = [s for s in sources if s == "SpotifyClient"]
            pjmp3_sources = [s for s in sources if s == "Pjmp3Client"]

            formatted_results = {}

            # 搜索 musicdl 源
            if musicdl_sources:
                results = self._client.search(keyword)
                for source, songs in results.items():
                    if source in musicdl_sources:
                        formatted_results[source] = [
                            self._songinfo_to_dict(song) for song in songs
                        ]

            # 搜索 Spotify
            if spotify_sources:
                spotify_results = self._search_spotify(keyword)
                if spotify_results:
                    formatted_results["SpotifyClient"] = spotify_results

            # 搜索 Pjmp3
            if pjmp3_sources and self._pjmp3_client and self._pjmp3_client.enabled:
                pjmp3_results = self._pjmp3_client.search(keyword)
                if pjmp3_results:
                    formatted_results["Pjmp3Client"] = [
                        self._pjmp3_songinfo_to_dict(song) for song in pjmp3_results
                    ]

            return formatted_results
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def search_single_source(self, keyword, source):
        """
        Search for music from a single source only

        优化版本：使用主客户端的特定源客户端，避免创建新客户端

        Args:
            keyword: Search keyword
            source: Single source name (e.g., 'QQMusicClient')

        Returns:
            {source: [song_dict, ...]} or {} if no results
        """
        logger.info(f"Searching single source '{source}' for '{keyword}'")

        # 特殊处理 Spotify
        if source == "SpotifyClient":
            spotify_results = self._search_spotify(keyword)
            if spotify_results:
                return {"SpotifyClient": spotify_results}
            return {}

        # 特殊处理 Pjmp3
        if source == "Pjmp3Client":
            if self._pjmp3_client is None:
                self._pjmp3_client = get_pjmp3_client()
            if self._pjmp3_client and self._pjmp3_client.enabled:
                pjmp3_results = self._pjmp3_client.search(keyword)
                if pjmp3_results:
                    return {
                        "Pjmp3Client": [self._pjmp3_songinfo_to_dict(song) for song in pjmp3_results]
                    }
            return {}

        if self._client is None:
            self._initialize_client()

        try:
            # 确保keyword是字符串并正确编码
            if not isinstance(keyword, str):
                keyword = str(keyword)
            keyword = keyword.encode('utf-8', errors='ignore').decode('utf-8')

            # 使用主客户端的特定源客户端直接搜索
            if hasattr(self._client, 'music_clients') and source in self._client.music_clients:
                mc = self._client.music_clients.get(source)
                if mc and hasattr(mc, 'search'):
                    # 直接调用特定源的客户端
                    raw_results = mc.search(keyword)
                    if raw_results and source in raw_results:
                        formatted_results = {
                            source: [self._songinfo_to_dict(song) for song in raw_results[source]]
                        }
                        logger.info(f"Found {len(formatted_results.get(source, []))} results from {source}")
                        return formatted_results

            # Fallback: 使用主客户端的search方法，但只保留指定源的结果
            results = self._client.search(keyword)
            formatted_results = {}
            if source in results and results[source]:
                formatted_results[source] = [
                    self._songinfo_to_dict(song) for song in results[source]
                ]
                logger.info(f"Found {len(formatted_results.get(source, []))} results from {source} (fallback)")
            return formatted_results

        except Exception as e:
            logger.error(f"Single source search error for {source}: {e}")
            return {}

    def _search_spotify(self, keyword: str) -> list:
        """
        搜索 Spotify

        Args:
            keyword: 搜索关键词

        Returns:
            歌曲字典列表
        """
        try:
            from core.spotify_client import get_spotify_client

            spotify = get_spotify_client()
            if not spotify or not spotify.enabled:
                logger.debug("Spotify not configured, skipping")
                return []

            results = spotify.search(keyword, limit=10)

            # 转换为标准字典格式
            formatted = []
            for song in results:
                formatted.append({
                    'song_name': song.song_name,
                    'singers': song.singers,
                    'album': song.album,
                    'file_size': song.file_size,
                    'duration': song.duration,
                    'source': song.source,
                    'ext': song.ext,
                    'download_url': song.download_url,
                    'duration_s': song.duration_s,
                    'song_info_obj': song,  # 存储原始对象用于下载
                    'spotify_id': song.spotify_id,
                    'spotify_url': song.spotify_url,
                    'preview_url': song.preview_url,
                })

            logger.info(f"Spotify search returned {len(formatted)} results")
            return formatted

        except Exception as e:
            logger.error(f"Spotify search error: {e}")
            return []

    def _songinfo_to_dict(self, song_info):
        """Convert SongInfo object to dictionary"""
        # Handle both dict and SongInfo object
        if isinstance(song_info, dict):
            return {
                'song_name': song_info.get('song_name', ''),
                'singers': song_info.get('singers', ''),
                'album': song_info.get('album', ''),
                'file_size': song_info.get('file_size', ''),
                'duration': song_info.get('duration', ''),
                'source': song_info.get('source', ''),
                'ext': song_info.get('ext', ''),
                'download_url': song_info.get('download_url'),  # For direct download
                'duration_s': song_info.get('duration_s', 0),   # For filtering
                'song_info_obj': song_info  # Keep reference for PyQt UI download
            }
        else:
            return {
                'song_name': getattr(song_info, 'song_name', ''),
                'singers': getattr(song_info, 'singers', ''),
                'album': getattr(song_info, 'album', ''),
                'file_size': getattr(song_info, 'file_size', ''),
                'duration': getattr(song_info, 'duration', ''),
                'source': getattr(song_info, 'source', ''),
                'ext': getattr(song_info, 'ext', ''),
                'download_url': getattr(song_info, 'download_url', None),  # For direct download
                'duration_s': getattr(song_info, 'duration_s', 0),           # For filtering
                'song_info_obj': song_info  # Keep reference for PyQt UI download
            }

    def _pjmp3_songinfo_to_dict(self, song_info):
        """Convert Pjmp3SongInfo object to dictionary"""
        return {
            'song_name': getattr(song_info, 'song_name', ''),
            'singers': getattr(song_info, 'singers', ''),
            'album': getattr(song_info, 'album', ''),
            'file_size': getattr(song_info, 'file_size', ''),
            'duration': getattr(song_info, 'duration', ''),
            'source': 'Pjmp3Client',
            'ext': getattr(song_info, 'ext', 'mp3'),
            'download_url': getattr(song_info, 'download_url', None),
            'duration_s': getattr(song_info, 'duration_s', 0),
            'song_info_obj': song_info,  # Keep reference for download
            'song_id': getattr(song_info, 'song_id', ''),
            'cover_url': getattr(song_info, 'cover_url', ''),
            'preview_url': getattr(song_info, 'preview_url', None),
        }

    def download(self, songs, download_dir=None):
        """
        Download songs

        Args:
            songs: List of song_info dictionaries
            download_dir: Optional custom download directory (Path or str)
        """
        import os

        # Determine target directory
        target_dir = str(download_dir) if download_dir else str(DOWNLOAD_DIR)
        logger.info(f"[DOWNLOAD] Target directory: {target_dir}")

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

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
            logger.info(f"[DEFAULT PATH] Downloading to default directory: {DOWNLOAD_DIR}")

        # Initialize Pjmp3 client
        if self._pjmp3_client is None:
            self._pjmp3_client = get_pjmp3_client()

        logger.info(f"Downloading {len(songs)} songs...")
        try:
            # 分离 Pjmp3 歌曲和其他源歌曲
            pjmp3_songs = []
            other_songs = []

            for song_dict in songs:
                source = song_dict.get('source', '')
                if source == 'Pjmp3Client':
                    pjmp3_songs.append(song_dict)
                else:
                    other_songs.append(song_dict)

            # 下载 Pjmp3 歌曲
            if pjmp3_songs and self._pjmp3_client and self._pjmp3_client.enabled:
                logger.info(f"Downloading {len(pjmp3_songs)} Pjmp3 songs...")
                for song_dict in pjmp3_songs:
                    song_obj = song_dict.get('song_info_obj')
                    if song_obj:
                        download_url = getattr(song_obj, 'download_url', None)
                        if download_url:
                            song_name = getattr(song_obj, 'song_name', 'Unknown')
                            ext = getattr(song_obj, 'ext', 'mp3')
                            song_name_safe = song_name.replace('/', '-').replace('\\', '-')
                            filename = f"{song_name_safe}.{ext}"
                            save_path = os.path.join(target_dir, filename)
                            self._pjmp3_client.download_file(download_url, save_path, song_name)
                        else:
                            logger.warning(f"No download_url for Pjmp3 song: {getattr(song_obj, 'song_name', 'Unknown')}")

            # 下载其他源歌曲（使用 musicdl）
            if other_songs:
                self._download_musicdl_songs(other_songs, client)

            logger.info("Download completed")
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise

    def _download_musicdl_songs(self, songs, client):
        """Download songs using musicdl client"""
        try:
            # Extract SongInfo objects from dicts
            song_info_objects = []
            for song_dict in songs:
                logger.info(f"Processing song_dict, keys={list(song_dict.keys())[:8]}")
                song_obj = song_dict.get('song_info_obj')
                logger.info(f"song_obj type: {type(song_obj) if song_obj else 'None'}")

                if song_obj:
                    # Check if song_obj is a dict (from musicdl search) or SongInfo object
                    if isinstance(song_obj, dict):
                        # musicdl search returns dict, need to get SongInfo from client
                        song_name = song_obj.get('song_name', '')
                        source = song_obj.get('source', '')
                        logger.info(f"Re-searching for SongInfo: {song_name} from {source}")

                        # Get SongInfo from client's cache or search again
                        if hasattr(client, 'music_clients') and source in client.music_clients:
                            mc = client.music_clients.get(source)
                            if mc and hasattr(mc, 'search'):
                                # Re-search to get fresh SongInfo
                                search_results = mc.search(song_name)
                                if search_results:
                                    for si in search_results:
                                        if hasattr(si, 'song_name') and si.song_name == song_name:
                                            song_info_objects.append(si)
                                            logger.info(f"Found SongInfo: {si.song_name}")
                                            break
                    else:
                        # It's a SongInfo object
                        song_info_objects.append(song_obj)
                else:
                    logger.warning(f"No song_info_obj found in: {song_dict}")

            if not song_info_objects:
                logger.warning("No valid SongInfo objects to download for musicdl sources")
                return

            # DEBUG: 打印song_info_objects信息
            logger.info(f"Total musicdl song_info_objects: {len(song_info_objects)}")
            for i, obj in enumerate(song_info_objects):
                if isinstance(obj, dict):
                    logger.info(f"Song {i}: type=dict, keys={list(obj.keys())[:5]}")
                else:
                    logger.info(f"Song {i}: type={type(obj).__name__}, has_save_path={hasattr(obj, 'save_path')}")

            client.download(song_info_objects)
            logger.info("MusicDL download completed")
        except Exception as e:
            logger.error(f"MusicDL download error: {e}")
            raise
