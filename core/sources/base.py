"""
Base Music Source - 音乐源抽象基类

定义所有音乐源必须实现的接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SongInfo:
    """
    统一歌曲信息数据结构

    兼容所有音乐源的歌曲数据格式。
    """
    song_name: str
    singers: str
    album: str = ""
    file_size: str = ""
    duration: str = ""
    source: str = ""
    ext: str = "mp3"
    download_url: Optional[str] = None
    duration_s: int = 0
    song_id: str = ""
    cover_url: str = ""
    preview_url: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "song_name": self.song_name,
            "singers": self.singers,
            "album": self.album,
            "file_size": self.file_size,
            "duration": self.duration,
            "source": self.source,
            "ext": self.ext,
            "download_url": self.download_url,
            "duration_s": self.duration_s,
            "song_id": self.song_id,
            "cover_url": self.cover_url,
            "preview_url": self.preview_url,
        }


class BaseMusicSource(ABC):
    """
    音乐源抽象基类

    所有音乐源必须实现以下方法：
    - name: 源名称
    - search: 搜索歌曲
    - get_detail: 获取歌曲详情
    - download: 下载歌曲
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """返回音乐源名称"""
        pass

    @property
    def display_name(self) -> str:
        """返回显示名称（可被子类重写）"""
        return self.name

    @abstractmethod
    def search(self, keyword: str, limit: int = 20) -> List[SongInfo]:
        """
        搜索歌曲

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            歌曲信息列表
        """
        pass

    @abstractmethod
    def get_detail(self, song_id: str) -> Optional[SongInfo]:
        """
        获取歌曲详情（包含下载链接）

        Args:
            song_id: 歌曲ID

        Returns:
            歌曲详情，如果获取失败返回 None
        """
        pass

    @abstractmethod
    def download(self, song_id: str, save_path: str) -> bool:
        """
        下载歌曲到指定路径

        Args:
            song_id: 歌曲ID
            save_path: 保存路径

        Returns:
            下载是否成功
        """
        pass

    def is_available(self) -> bool:
        """
        检查音乐源是否可用

        子类可重写此方法以实现自定义可用性检查。
        默认返回 True。
        """
        return True
