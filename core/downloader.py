"""
MusicDL Wrapper Class - Singleton Pattern

此模块提供 musicdl 的线程安全单例封装，可被后端和桌面端共同使用。

IMPORTANT: 必须在任何 musicdl 导入之前禁用 rich 进度条
因为 rich 库在同一时间只能有一个活动的进度条，多线程并发调用会冲突
"""

import os

# 方案1: 设置环境变量禁用 rich 进度条
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'

# 方案2: Monkey patch rich.progress.Progress 类，使其成为空操作
# 这必须在 musicdl 导入之前执行
try:
    from rich.progress import Progress as _OriginalProgress

    class _DummyTask:
        """Dummy Task object with all necessary attributes"""
        def __init__(self, task_id, description='', total=None, completed=0):
            self.id = task_id
            self.description = description
            self.total = total
            self._completed = completed

        @property
        def completed(self):
            return self._completed

        @completed.setter
        def completed(self, value):
            self._completed = value

        @property
        def percentage(self):
            if self.total and self.total > 0:
                return (self._completed / self.total) * 100
            return 0

    class _DummyProgress:
        """Dummy Progress class that does nothing, for thread safety.
        Implements all methods/properties that musicdl might use.
        """
        def __init__(self, *args, **kwargs):
            self._tasks = {}  # task_id -> _DummyTask
            self._task_counter = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def add_task(self, description, total=None, completed=0, **kwargs):
            task_id = self._task_counter
            self._task_counter += 1
            self._tasks[task_id] = _DummyTask(task_id, description, total, completed)
            return task_id

        def update(self, task_id, total=None, completed=None, advance=None, **kwargs):
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if total is not None:
                    task.total = total
                if completed is not None:
                    task._completed = completed
                if advance is not None:
                    task._completed += advance

        def advance(self, task_id, amount=1):
            self.update(task_id, advance=amount)

        def remove_task(self, task_id):
            self._tasks.pop(task_id, None)

        @property
        def tasks(self):
            # Return list of _DummyTask objects
            return list(self._tasks.values())

        def stop_task(self, task_id):
            pass

        def start_task(self, task_id):
            pass

        def refresh(self):
            pass

        def stop(self):
            pass

        def start(self):
            pass

    # Replace rich.progress.Progress with our dummy
    import rich.progress
    rich.progress.Progress = _DummyProgress
except ImportError:
    pass  # rich not installed, no need to patch

import threading
from musicdl.musicdl import MusicClient
from .config import DOWNLOAD_DIR, DEFAULT_SOURCES
from .pjmp3_client import Pjmp3Client, Pjmp3SongInfo, get_pjmp3_client
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
            # 只使用 musicdl 支持的源（排除 Pjmp3Client 和 SpotifyClient）
            musicdl_supported_sources = [s for s in DEFAULT_SOURCES if s not in ("SpotifyClient", "Pjmp3Client")]
            logger.info(f"[DEBUG] MusicClient will use sources: {musicdl_supported_sources}")
            # 设置超时为180秒，避免API响应慢导致超时（musicdl搜索很慢）
            request_overrides = {
                source: {'timeout': (30, 180)}  # (连接超时30s, 读取超时180s)
                for source in musicdl_supported_sources
            }
            self._client = MusicClient(
                music_sources=musicdl_supported_sources,
                init_music_clients_cfg={
                    source: {'work_dir': str(DOWNLOAD_DIR)}
                    for source in musicdl_supported_sources
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

        # 分离 musicdl 源和 Pjmp3 源
        musicdl_sources = [s for s in sources if s != 'Pjmp3Client']
        pjmp3_sources = [s for s in sources if s == 'Pjmp3Client']

        formatted_results = {}

        try:
            # 搜索 musicdl 支持的源
            if musicdl_sources:
                results = self._client.search(keyword)
                for source, songs in results.items():
                    if source in musicdl_sources:
                        formatted_results[source] = [
                            self._songinfo_to_dict(song) for song in songs
                        ]

            # 独立搜索 Pjmp3
            if pjmp3_sources and self._pjmp3_client and self._pjmp3_client.enabled:
                pjmp3_results = self._pjmp3_client.search(keyword)
                if pjmp3_results:
                    formatted_results['Pjmp3Client'] = [
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

        # 特殊处理 Pjmp3 源
        if source == 'Pjmp3Client':
            if self._pjmp3_client is None:
                self._pjmp3_client = get_pjmp3_client()
            if self._pjmp3_client and self._pjmp3_client.enabled:
                pjmp3_results = self._pjmp3_client.search(keyword)
                if pjmp3_results:
                    return {
                        'Pjmp3Client': [self._pjmp3_songinfo_to_dict(song) for song in pjmp3_results]
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

            # Fallback: 如果无法访问特定源客户端，使用主客户端的search方法
            # 但只保留指定源的结果
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

    def _resolve_song_source(self, song_dict):
        """Resolve source from song dict, falling back to the embedded song object."""
        source = song_dict.get('source', '')
        if source:
            return source

        song_obj = song_dict.get('song_info_obj')
        return getattr(song_obj, 'source', '') if song_obj else ''

    def _prepare_pjmp3_song(self, song_dict):
        """
        Ensure a pjmp3 song has a detail object with download_url before download.

        Search results from pjmp3 only contain summary data plus song_id. The actual
        download URL lives on the detail page, so we must hydrate it before writing.
        """
        song_obj = song_dict.get('song_info_obj')
        if song_obj is None:
            return None

        if not isinstance(song_obj, Pjmp3SongInfo):
            return song_obj

        if getattr(song_obj, 'download_url', None):
            return song_obj

        song_id = getattr(song_obj, 'song_id', '') or song_dict.get('song_id', '')
        if not song_id or self._pjmp3_client is None:
            return song_obj

        detail = self._pjmp3_client.get_song_detail(song_id)
        if detail is None:
            logger.warning(f"Failed to fetch pjmp3 detail for song_id={song_id}")
            return song_obj

        # Keep summary metadata when the detail page omits fields.
        detail.song_name = detail.song_name or song_obj.song_name
        detail.singers = detail.singers or song_obj.singers
        detail.album = detail.album or song_obj.album
        detail.ext = detail.ext or song_obj.ext
        detail.cover_url = detail.cover_url or song_obj.cover_url
        detail.source = "Pjmp3Client"

        song_dict['song_info_obj'] = detail
        song_dict['download_url'] = detail.download_url
        return detail

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

        # Initialize Pjmp3 client
        if self._pjmp3_client is None:
            self._pjmp3_client = get_pjmp3_client()

        logger.info(f"Downloading {len(songs)} songs...")

        try:
            # 分离 Pjmp3 歌曲和其他源歌曲
            pjmp3_songs = []
            other_songs = []

            for song_dict in songs:
                source = self._resolve_song_source(song_dict)
                if source == 'Pjmp3Client':
                    pjmp3_songs.append(song_dict)
                else:
                    other_songs.append(song_dict)

            # 下载 Pjmp3 歌曲
            if pjmp3_songs and self._pjmp3_client and self._pjmp3_client.enabled:
                logger.info(f"Downloading {len(pjmp3_songs)} Pjmp3 songs...")
                for song_dict in pjmp3_songs:
                    song_obj = self._prepare_pjmp3_song(song_dict)
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
                self._download_musicdl_songs(other_songs, target_dir, client)

            logger.info("Download completed")
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise

    def _download_musicdl_songs(self, songs, target_dir, client):
        """Download songs using musicdl client"""
        import os

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
                                        if hasattr(si, 'work_dir'):
                                            si.work_dir = target_dir
                                        # 设置 _save_path 私有字段（save_path 是只读 property）
                                        ext = getattr(si, 'ext', 'mp3')
                                        song_name_safe = song_name.replace('/', '-').replace('\\', '-')
                                        singers = getattr(si, 'singers', '')
                                        singers_safe = singers.replace('/', '-').replace('\\', '-') if singers else ''
                                        filename = f"{song_name_safe} - {singers_safe}.{ext}" if singers else f"{song_name_safe}.{ext}"
                                        si._save_path = os.path.join(target_dir, filename)
                                        song_info_objects.append(si)
                                        logger.info(f"Found SongInfo: {si.song_name}, save_path: {getattr(si, 'save_path', 'N/A')}")
                                        break
                else:
                    # It's a SongInfo object - update work_dir and save_path for custom directory
                    # 设置 work_dir 让 save_path property 自动生成正确路径
                    if hasattr(song_obj, 'work_dir'):
                        song_obj.work_dir = target_dir
                        logger.info(f"[CUSTOM PATH] Updated work_dir to: {target_dir}")
                    # 设置 _save_path 私有字段（save_path 是只读 property）
                    ext = getattr(song_obj, 'ext', 'mp3')
                    song_name = getattr(song_obj, 'song_name', 'Unknown')
                    song_name_safe = song_name.replace('/', '-').replace('\\', '-')
                    singers = getattr(song_obj, 'singers', '')
                    singers_safe = singers.replace('/', '-').replace('\\', '-') if singers else ''
                    filename = f"{song_name_safe} - {singers_safe}.{ext}" if singers else f"{song_name_safe}.{ext}"
                    song_obj._save_path = os.path.join(target_dir, filename)
                    logger.info(f"[CUSTOM PATH] Updated _save_path to: {song_obj._save_path}")
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
