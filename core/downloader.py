"""
MusicDL Wrapper Class - Singleton Pattern

此模块提供 musicdl 的线程安全单例封装，可被后端和桌面端共同使用。
"""

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

        优化版本：创建专用client只搜索指定源，避免搜索所有源

        Args:
            keyword: Search keyword
            source: Single source name (e.g., 'QQMusicClient')

        Returns:
            {source: [song_dict, ...]} or {} if no results
        """
        logger.info(f"Searching single source '{source}' for '{keyword}'")

        if self._client is None:
            self._initialize_client()

        try:
            # 确保keyword是字符串并正确编码
            if not isinstance(keyword, str):
                keyword = str(keyword)
            # 确保字符串可编码
            keyword = keyword.encode('utf-8', errors='ignore').decode('utf-8')

            # 创建专用client只搜索指定源
            from musicdl.musicdl import MusicClient
            single_source_client = MusicClient(
                music_sources=[source],  # 只传入指定的源
                init_music_clients_cfg={
                    source: {'work_dir': str(DOWNLOAD_DIR)}
                },
                requests_overrides={
                    source: {'timeout': (30, 180)}
                }
            )

            # 只搜索指定的源
            results = single_source_client.search(keyword)

            # 转换为字典格式
            formatted_results = {}
            if source in results and results[source]:
                formatted_results[source] = [
                    self._songinfo_to_dict(song) for song in results[source]
                ]

            logger.info(f"Found {len(formatted_results.get(source, []))} results from {source}")
            return formatted_results

        except Exception as e:
            logger.error(f"Single source search error for {source}: {e}")
            return {}

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

    def download(self, songs, download_dir=None):
        """
        Download songs

        Args:
            songs: List of song_info dictionaries
            download_dir: Optional custom download directory (Path or str)
        """
        import os

        # Determine the target directory
        target_dir = str(download_dir) if download_dir else str(DOWNLOAD_DIR)
        logger.info(f"[DOWNLOAD] Target directory: {target_dir}")

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        # Use default client for downloading
        if self._client is None:
            self._initialize_client()
        client = self._client

        logger.info(f"Downloading {len(songs)} songs...")
        try:
            # Extract SongInfo objects from dicts and update their paths
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
                                            # Update the work_dir and save_path for custom directory
                                            if download_dir and hasattr(si, 'work_dir'):
                                                si.work_dir = target_dir
                                            if download_dir and hasattr(si, 'save_path'):
                                                # Rebuild save_path with new directory
                                                ext = getattr(si, 'ext', 'mp3')
                                                song_name_safe = song_name.replace('/', '-').replace('\\', '-')
                                                singers = getattr(si, 'singers', '')
                                                singers_safe = singers.replace('/', '-').replace('\\', '-') if singers else ''
                                                filename = f"{song_name_safe} - {singers_safe}.{ext}" if singers else f"{song_name_safe}.{ext}"
                                                si.save_path = os.path.join(target_dir, filename)
                                            song_info_objects.append(si)
                                            logger.info(f"Found SongInfo: {si.song_name}, save_path: {getattr(si, 'save_path', 'N/A')}")
                                            break
                    else:
                        # It's a SongInfo object - update work_dir and save_path for custom directory
                        if download_dir:
                            if hasattr(song_obj, 'work_dir'):
                                song_obj.work_dir = target_dir
                                logger.info(f"[CUSTOM PATH] Updated work_dir to: {target_dir}")
                            if hasattr(song_obj, 'save_path'):
                                # Rebuild save_path with new directory
                                ext = getattr(song_obj, 'ext', 'mp3')
                                song_name = getattr(song_obj, 'song_name', 'Unknown')
                                song_name_safe = song_name.replace('/', '-').replace('\\', '-')
                                singers = getattr(song_obj, 'singers', '')
                                singers_safe = singers.replace('/', '-').replace('\\', '-') if singers else ''
                                filename = f"{song_name_safe} - {singers_safe}.{ext}" if singers else f"{song_name_safe}.{ext}"
                                song_obj.save_path = os.path.join(target_dir, filename)
                                logger.info(f"[CUSTOM PATH] Updated save_path to: {song_obj.save_path}")
                        song_info_objects.append(song_obj)
                else:
                    logger.warning(f"No song_info_obj found in: {song_dict}")

            if not song_info_objects:
                raise ValueError("No valid SongInfo objects to download")

            # DEBUG: 打印song_info_objects信息
            logger.info(f"Total song_info_objects: {len(song_info_objects)}")
            for i, obj in enumerate(song_info_objects):
                if isinstance(obj, dict):
                    logger.info(f"Song {i}: type=dict, keys={list(obj.keys())[:5]}")
                else:
                    logger.info(f"Song {i}: type={type(obj).__name__}, save_path={getattr(obj, 'save_path', 'N/A')}")

            # 使用对应源的 music_client 进行下载，确保使用更新后的路径
            for song_obj in song_info_objects:
                source = getattr(song_obj, 'source', None)
                if source and hasattr(client, 'music_clients') and source in client.music_clients:
                    mc = client.music_clients.get(source)
                    if mc and hasattr(mc, 'download'):
                        mc.download([song_obj])
                        logger.info(f"Downloaded via {source} client")
                else:
                    # Fallback to main client
                    client.download([song_obj])

            logger.info("Download completed")
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise