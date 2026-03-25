"""
Spotify Music Client Adapter

由于 musicdl 库不支持 Spotify，此模块提供 Spotify Web API 的适配器，
使其能够与现有的 MusicDownloader 接口兼容。

使用说明：
1. 在环境变量中设置 SPOTIFY_CLIENT_ID 和 SPOTIFY_CLIENT_SECRET
2. 首次使用时会自动获取访问令牌
3. 搜索功能与其他音乐源保持一致

文档：https://developer.spotify.com/documentation/web-api/
"""

import os
import base64
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class SpotifySongInfo:
    """Spotify 歌曲信息（兼容 SongInfo 接口）"""
    song_name: str
    singers: str
    album: str
    file_size: str = ""
    duration: str = ""
    source: str = "SpotifyClient"
    ext: str = "mp3"
    download_url: Optional[str] = None
    duration_s: int = 0
    spotify_id: str = ""
    spotify_url: str = ""
    preview_url: Optional[str] = None  # 30秒预览URL


def _format_duration(ms: int) -> str:
    """将毫秒格式化为 MM:SS"""
    seconds = ms // 1000
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


class SpotifyClient:
    """
    Spotify Web API 客户端

    需要配置环境变量：
    - SPOTIFY_CLIENT_ID: Spotify App 的 Client ID
    - SPOTIFY_CLIENT_SECRET: Spotify App 的 Client Secret

    如果没有配置，客户端将无法使用（搜索返回空结果）。
    """

    API_BASE = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com/api/token"

    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token: Optional[str] = None
        self.enabled = bool(self.client_id and self.client_secret)

        if not self.enabled:
            logger.warning(
                "SpotifyClient: 未配置 SPOTIFY_CLIENT_ID 和 SPOTIFY_CLIENT_SECRET，"
                "Spotify 源将被禁用。请在环境变量中配置后再使用。"
            )
        else:
            logger.info("SpotifyClient: 已配置，正在初始化...")
            self._authenticate()

    def _authenticate(self) -> bool:
        """
        使用 Client Credentials Flow 获取访问令牌

        Returns:
            认证是否成功
        """
        if not self.enabled:
            return False

        try:
            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_bytes = base64.b64encode(auth_str.encode()).decode()

            headers = {
                "Authorization": f"Basic {auth_bytes}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            data = {"grant_type": "client_credentials"}

            response = requests.post(
                self.AUTH_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)

            logger.info(f"SpotifyClient: 认证成功，令牌有效期 {expires_in} 秒")
            return True

        except Exception as e:
            logger.error(f"SpotifyClient: 认证失败 - {e}")
            self.enabled = False
            return False

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        发起 API 请求

        Args:
            endpoint: API 端点（不带 base URL）
            params: 查询参数

        Returns:
            API 响应的 JSON 数据，失败返回 None
        """
        if not self.enabled or not self.access_token:
            return None

        url = f"{self.API_BASE}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            # 如果返回 401，可能是令牌过期，尝试重新认证
            if response.status_code == 401:
                logger.warning("SpotifyClient: 令牌可能过期，尝试重新认证...")
                if self._authenticate():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.get(url, headers=headers, params=params, timeout=30)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"SpotifyClient: 请求失败 - {e}")
            return None

    def search(self, keyword: str, limit: int = 10) -> List[SpotifySongInfo]:
        """
        搜索歌曲

        Args:
            keyword: 搜索关键词（歌曲名 + 歌手）
            limit: 返回结果数量上限

        Returns:
            SpotifySongInfo 列表
        """
        if not self.enabled:
            return []

        logger.info(f"SpotifyClient: 搜索 '{keyword}'")

        params = {
            "q": keyword,
            "type": "track",
            "limit": limit,
            "market": "CN",  # 中国市场
        }

        data = self._make_request("search", params)
        if not data or "tracks" not in data:
            return []

        tracks = data["tracks"].get("items", [])
        results = []

        for track in tracks:
            try:
                # 提取歌曲信息
                song_name = track.get("name", "")
                spotify_id = track.get("id", "")
                spotify_url = track.get("external_urls", {}).get("spotify", "")
                preview_url = track.get("preview_url")
                duration_ms = track.get("duration_ms", 0)

                # 提取歌手信息
                artists = track.get("artists", [])
                singer_names = [a.get("name", "") for a in artists]
                singers = ", ".join(singer_names) if singer_names else ""

                # 提取专辑信息
                album = track.get("album", {})
                album_name = album.get("name", "")

                song_info = SpotifySongInfo(
                    song_name=song_name,
                    singers=singers,
                    album=album_name,
                    duration=_format_duration(duration_ms),
                    duration_s=duration_ms // 1000,
                    spotify_id=spotify_id,
                    spotify_url=spotify_url,
                    preview_url=preview_url,
                )
                results.append(song_info)

            except Exception as e:
                logger.error(f"SpotifyClient: 解析歌曲信息失败 - {e}")
                continue

        logger.info(f"SpotifyClient: 找到 {len(results)} 首歌曲")
        return results


# 全局客户端实例（懒加载）
_spotify_client: Optional[SpotifyClient] = None


def get_spotify_client() -> Optional[SpotifyClient]:
    """获取全局 SpotifyClient 实例"""
    global _spotify_client
    if _spotify_client is None:
        _spotify_client = SpotifyClient()
    return _spotify_client


def reset_spotify_client():
    """重置全局实例（用于测试或重新配置）"""
    global _spotify_client
    _spotify_client = None
