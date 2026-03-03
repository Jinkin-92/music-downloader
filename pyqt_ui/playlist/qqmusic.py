"""QQ音乐歌单解析器

支持解析QQ音乐歌单链接并提取歌曲列表。
"""
import re
import logging
from typing import List
from .base import BasePlaylistParser, PlaylistSong

logger = logging.getLogger(__name__)


class QQMusicPlaylistParser(BasePlaylistParser):
    """QQ音乐歌单解析器

    支持的歌单URL格式:
    - https://y.qq.com/n/ryqq/playlist/123456
    - https://i.y.qq.com/v8/favor-song-list.html?id=123456
    """

    # API端点
    PLAYLIST_API = "https://i.y.qq.com/v8/fav-bin/fav_getinfo"
    SONG_DETAIL_API = "https://i.y.qq.com/v8/fav-bin/song_info"

    # URL模式
    URL_PATTERNS = [
        r'https?://y\.qq\.com/n/ryqq/playlist/(\d+)',
        r'https?://i\.y\.qq\.com/v8/favor-song-list\.html.*[?&]id=(\d+)',
    ]

    def validate_url(self, url: str) -> bool:
        """验证是否为QQ音乐歌单链接

        Args:
            url: 待验证的URL

        Returns:
            True如果URL是QQ音乐歌单链接
        """
        return any(re.search(pattern, url) for pattern in self.URL_PATTERNS)

    def parse(self, url: str) -> List[PlaylistSong]:
        """解析QQ音乐歌单

        Args:
            url: 歌单URL

        Returns:
            歌曲列表

        Raises:
            ValueError: URL格式无效或歌单不存在
            RuntimeError: 网络请求失败或解析失败
        """
        logger.info(f"Parsing QQ Music playlist: {url}")

        # 1. 提取歌单ID (dir_id)
        dir_id = self._extract_dir_id(url)
        if not dir_id:
            raise ValueError(f"无法从URL提取歌单ID: {url}")

        logger.info(f"Extracted dir_id: {dir_id}")

        # 2. 获取歌单详情
        playlist_data = self._fetch_playlist_detail(dir_id)

        # 3. 提取歌曲列表
        songs = self._extract_songs(playlist_data)

        logger.info(f"Successfully parsed {len(songs)} songs from QQ Music")
        return songs

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "QQ音乐"

    def _extract_dir_id(self, url: str) -> str:
        """从URL提取歌单ID

        QQ音乐的ID叫dir_id

        Args:
            url: 歌单URL

        Returns:
            歌单ID,失败返回None
        """
        # 尝试多种模式匹配
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _fetch_playlist_detail(self, dir_id: str) -> dict:
        """获取歌单详情

        Args:
            dir_id: 歌单ID

        Returns:
            歌单详情数据

        Raises:
            RuntimeError: 请求失败
        """
        # QQ音乐的API需要特定的参数格式
        params = {
            'dirid': dir_id,
            'uin': '0',  # 游客模式
            'format': 'json'
        }

        headers = {
            'Referer': 'https://y.qq.com/',
            'Accept': 'application/json',
        }

        try:
            data = self._fetch_json(
                self.PLAYLIST_API,
                params=params,
                headers=headers
            )

            # QQ音乐的响应格式
            if data.get('code', 0) != 0:
                error_msg = data.get('msg', data.get('message', '未知错误'))
                raise RuntimeError(f"获取歌单详情失败: {error_msg}")

            return data

        except Exception as e:
            logger.error(f"Failed to fetch playlist detail: {e}")
            raise

    def _extract_songs(self, playlist_data: dict) -> List[PlaylistSong]:
        """从歌单数据中提取歌曲列表

        Args:
            playlist_data: 歌单详情数据

        Returns:
            歌曲列表
        """
        try:
            # QQ音乐的响应结构
            data = playlist_data.get('data', {})
            songlist = data.get('songlist', [])

            if not songlist:
                logger.warning("Playlist has no songs")
                return []

            songs = []

            for song_data in songlist:
                try:
                    song = self._parse_song_data(song_data)
                    if song:
                        songs.append(song)

                except Exception as e:
                    logger.warning(f"Failed to parse song {song_data}: {e}")
                    continue

            return songs

        except Exception as e:
            logger.error(f"Failed to extract songs: {e}")
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
            song_name = song_data.get('songname', song_data.get('title', ''))

            # 歌手信息
            singers = song_data.get('singername', '')

            # 专辑信息
            album = song_data.get('albumname', '')

            # 时长 (秒 → 分:秒)
            interval = song_data.get('interval', 0)
            if interval:
                minutes = int(interval) // 60
                seconds = int(interval) % 60
                duration = f"{minutes}:{seconds:02d}"
            else:
                duration = ""

            # 创建歌曲对象
            song = PlaylistSong(
                song_name=song_name,
                singers=singers,
                album=album,
                duration=duration,
                source_platform="QQ音乐"
            )

            logger.debug(f"Parsed song: {song}")
            return song

        except Exception as e:
            logger.error(f"Error parsing song data: {e}")
            return None
