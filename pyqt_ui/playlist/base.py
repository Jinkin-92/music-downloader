"""歌单解析器基类和核心数据类

定义了歌单解析器的抽象接口和歌曲数据结构。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import requests
import logging
import certifi

logger = logging.getLogger(__name__)


@dataclass
class PlaylistSong:
    """歌单中的歌曲信息

    Attributes:
        song_name: 歌曲名称
        singers: 歌手名称(多个歌手用逗号分隔)
        album: 专辑名称(可选)
        duration: 时长,格式 "分:秒"(可选)
        source_url: 原歌单中的链接(可选)
        source_platform: 来源平台标识("netease", "qqmusic"等)
    """
    song_name: str
    singers: str
    album: str = ""
    duration: str = ""
    source_url: str = ""
    source_platform: str = ""

    def to_match_format(self) -> str:
        """转换为匹配器所需的格式 "歌名 - 歌手"

        Returns:
            匹配格式的字符串
        """
        return f"{self.song_name} - {self.singers}"

    def __str__(self) -> str:
        """字符串表示"""
        if self.album:
            return f"{self.song_name} - {self.singers} ({self.album})"
        return f"{self.song_name} - {self.singers}"


class BasePlaylistParser(ABC):
    """歌单解析器抽象基类

    所有平台的解析器都需要继承这个类并实现抽象方法。
    """

    def __init__(self):
        """初始化解析器"""
        import certifi
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
        })
        # 修复Windows下certifi证书问题
        self.session.verify = certifi.where()
        logger.info(f"Initialized {self.__class__.__name__} with certifi: {certifi.where()}")

    @abstractmethod
    def parse(self, url: str) -> List[PlaylistSong]:
        """解析歌单链接

        Args:
            url: 歌单URL

        Returns:
            歌曲列表

        Raises:
            ValueError: URL格式无效或歌单不存在
            RuntimeError: 网络请求失败或解析失败
        """
        pass

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """验证URL是否属于该平台

        Args:
            url: 待验证的URL

        Returns:
            True如果URL属于该平台,否则False
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称

        Returns:
            平台名称(如"网易云音乐", "QQ音乐")
        """
        pass

    def _fetch_json(self, url: str, params: dict = None,
                    headers: dict = None, timeout: int = 10) -> dict:
        """通用的JSON获取方法

        Args:
            url: 请求URL
            params: 查询参数(可选)
            headers: 额外的请求头(可选)
            timeout: 超时时间(秒)

        Returns:
            解析后的JSON数据

        Raises:
            RuntimeError: 网络请求失败或返回非JSON数据
        """
        try:
            # 禁用SSL验证以绕过certifi路径问题
            verify = False
            if headers:
                response = self.session.get(
                    url, params=params, headers=headers, timeout=timeout, verify=verify
                )
            else:
                response = self.session.get(
                    url, params=params, timeout=timeout, verify=verify
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {url}")
            raise RuntimeError(f"请求超时: {url}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise RuntimeError(f"网络请求失败: {e}")

        except ValueError as e:
            logger.error(f"JSON decode error: {e}")
            raise RuntimeError(f"返回数据格式错误: {e}")

    def _fetch_html(self, url: str, params: dict = None,
                    timeout: int = 10) -> str:
        """通用的HTML获取方法

        Args:
            url: 请求URL
            params: 查询参数(可选)
            timeout: 超时时间(秒)

        Returns:
            HTML内容

        Raises:
            RuntimeError: 网络请求失败
        """
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise RuntimeError(f"网络请求失败: {e}")

    def __repr__(self) -> str:
        """对象表示"""
        return f"<{self.__class__.__name__}>"
