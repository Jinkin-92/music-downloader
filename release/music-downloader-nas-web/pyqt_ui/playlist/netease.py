"""网易云音乐歌单解析器

支持解析网易云音乐歌单链接并提取歌曲列表。
"""
import re
import logging
from typing import List
from .base import BasePlaylistParser, PlaylistSong

logger = logging.getLogger(__name__)


class NeteasePlaylistParser(BasePlaylistParser):
    """网易云音乐歌单解析器

    支持的歌单URL格式:
    - https://music.163.com/#/playlist?id=123456
    - https://music.163.com/playlist?id=123456
    - https://163cn.tv/xxxxx (短链接)
    """

    # API端点
    PLAYLIST_API = "https://music.163.com/api/v6/playlist/detail"
    SONG_DETAIL_API = "https://music.163.com/api/v3/song/detail"

    # URL模式
    URL_PATTERNS = [
        r'https?://music\.163\.com/#/playlist\?id=(\d+)',
        r'https?://music\.163\.com/playlist\?id=(\d+)',
        r'https?://music\.163\.com/m/playlist\?id=(\d+)',  # 移动端链接
        r'https?://163cn\.tv/[a-zA-Z0-9]+',  # 短链接
    ]

    def validate_url(self, url: str) -> bool:
        """验证是否为网易云歌单链接

        Args:
            url: 待验证的URL

        Returns:
            True如果URL是网易云歌单链接
        """
        return any(re.match(pattern, url) for pattern in self.URL_PATTERNS)

    def parse(self, url: str) -> List[PlaylistSong]:
        """解析网易云歌单

        Args:
            url: 歌单URL

        Returns:
            歌曲列表

        Raises:
            ValueError: URL格式无效或歌单不存在
            RuntimeError: 网络请求失败或解析失败
        """
        logger.info(f"[PARSE START] 开始解析歌单: {url}")
        logger.info(f"Parsing Netease playlist: {url}")

        # 1. 提取歌单ID
        playlist_id = self._extract_playlist_id(url)
        if not playlist_id:
            raise ValueError(f"无法从URL提取歌单ID: {url}")

        logger.info(f"Extracted playlist ID: {playlist_id}")

        # 2. 获取歌单详情
        playlist_data = self._fetch_playlist_detail(playlist_id)

        # 3. 提取歌曲ID列表
        track_ids = self._extract_track_ids(playlist_data)
        if not track_ids:
            logger.warning(f"Playlist {playlist_id} has no songs")
            return []

        logger.info(f"Found {len(track_ids)} songs in playlist")

        # 4. 分批获取歌曲详情 (每批3首，因为API限制)
        songs = []
        batch_size = 3
        total_batches = (len(track_ids) + batch_size - 1) // batch_size

        for i in range(0, len(track_ids), batch_size):
            batch_ids = track_ids[i:i + batch_size]
            batch_number = i // batch_size + 1
            logger.info(f"Fetching batch {batch_number}/{total_batches}: {len(batch_ids)} songs")

            batch_songs = self._fetch_song_details(batch_ids)
            logger.info(f"Batch {batch_number}: 返回 {len(batch_songs)} 首歌曲，累计 {len(songs)} 首")
            songs.extend(batch_songs)

        logger.info(f"Successfully parsed {len(songs)} songs from Netease")
        logger.info(f"[PARSE END] 解析完成: 返回 {len(songs)} 首歌曲")
        return songs

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "网易云音乐"

    def _extract_playlist_id(self, url: str) -> str:
        """从URL提取歌单ID

        Args:
            url: 歌单URL

        Returns:
            歌单ID,失败返回None
        """
        # 处理标准链接
        match = re.search(r'id=(\d+)', url)
        if match:
            return match.group(1)

        # 处理短链接 (需要重定向)
        if '163cn.tv' in url:
            try:
                logger.info(f"Resolving short URL: {url}")
                response = self.session.head(url, timeout=10, allow_redirects=True)
                real_url = response.url
                logger.info(f"Short URL redirects to: {real_url}")

                # 从重定向后的URL提取ID
                return self._extract_playlist_id(real_url)

            except Exception as e:
                logger.error(f"Failed to resolve short URL: {e}")
                return None

        return None

    def _fetch_playlist_detail(self, playlist_id: str) -> dict:
        """获取歌单详情

        Args:
            playlist_id: 歌单ID

        Returns:
            歌单详情数据

        Raises:
            RuntimeError: 请求失败
        """
        params = {'id': playlist_id}

        # 添加额外的请求头模拟真实浏览器
        headers = {
            'Referer': 'https://music.163.com/',
            'Accept': '*/*',
        }

        try:
            data = self._fetch_json(
                self.PLAYLIST_API,
                params=params,
                headers=headers
            )

            # 检查返回状态
            if data.get('code') != 200:
                error_msg = data.get('message', '未知错误')
                raise RuntimeError(f"获取歌单详情失败: {error_msg}")

            return data

        except Exception as e:
            logger.error(f"Failed to fetch playlist detail: {e}")
            raise

    def _extract_track_ids(self, playlist_data: dict) -> List[int]:
        """从歌单数据中提取歌曲ID列表

        Args:
            playlist_data: 歌单详情数据

        Returns:
            歌曲ID列表
        """
        try:
            # 网易云API返回的数据结构是 {'playlist': {...}}
            result = playlist_data.get('playlist', {})
            track_ids_info = result.get('trackIds', [])

            # 提取ID
            track_ids = [item['id'] for item in track_ids_info]

            logger.info(f"Extracted {len(track_ids)} track IDs")
            return track_ids

        except Exception as e:
            logger.error(f"Failed to extract track IDs: {e}")
            return []

    def _fetch_song_details(self, track_ids: List[int]) -> List[PlaylistSong]:
        """批量获取歌曲详情

        Args:
            track_ids: 歌曲ID列表

        Returns:
            歌曲列表
        """
        # 构造请求数据
        # 网易云API格式: [{"id": 123}, {"id": 456}, ...]
        song_params = '[' + ','.join([f'{{"id":{tid}}}' for tid in track_ids]) + ']'

        params = {'c': song_params}
        headers = {
            'Referer': 'https://music.163.com/',
            'Accept': '*/*',
        }

        try:
            data = self._fetch_json(
                self.SONG_DETAIL_API,
                params=params,
                headers=headers
            )

            # 检查返回状态
            if data.get('code') != 200:
                logger.warning(f"Failed to fetch song details: {data.get('message')}")
                return []

            # 解析歌曲信息
            songs_data = data.get('songs', [])
            logger.info(f"[DEBUG] API返回 {len(songs_data)} 首歌曲详情，请求了 {len(track_ids)} 首")

            songs = []

            for song_data in songs_data:
                try:
                    song = self._parse_song_data(song_data)
                    if song:
                        songs.append(song)

                except Exception as e:
                    logger.warning(f"Failed to parse song {song_data}: {e}")
                    continue

            logger.info(f"[DEBUG] 成功解析 {len(songs)} 首歌曲")
            return songs

        except Exception as e:
            logger.error(f"Failed to fetch song details: {e}")
            return []

    def _parse_song_data(self, song_data: dict) -> PlaylistSong:
        """解析单首歌曲的数据

        Args:
            song_data: 歌曲数据

        Returns:
            PlaylistSong对象
        """
        try:
            # 基本信息
            song_name = song_data.get('name', '')

            # 歌手信息 (可能多个)
            ar_data = song_data.get('ar', [])
            singers = ', '.join([ar.get('name', '') for ar in ar_data if ar.get('name')])

            # 专辑信息
            al_data = song_data.get('al', {})
            album = al_data.get('name', '')

            # 时长 (毫秒 → 分:秒)
            dt_ms = song_data.get('dt', 0)
            duration_seconds = dt_ms // 1000
            duration = f"{duration_seconds // 60}:{duration_seconds % 60:02d}"

            # 创建歌曲对象
            song = PlaylistSong(
                song_name=song_name,
                singers=singers,
                album=album,
                duration=duration,
                source_platform="网易云音乐"
            )

            logger.debug(f"Parsed song: {song}")
            return song

        except Exception as e:
            logger.error(f"Error parsing song data: {e}")
            return None
