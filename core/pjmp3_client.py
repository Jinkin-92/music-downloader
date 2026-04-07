"""
pjmp3.com Music Client Adapter

提供 pjmp3.com 网站的网页抓取功能，作为备用音乐源。

注意：此模块已重构，核心实现已迁移到 core.sources.pjmp3_source
此文件保留用于向后兼容。
"""

from typing import Optional

# 向后兼容导入
from core.sources.pjmp3_source import (
    Pjmp3Source,
    get_pjmp3_source,
)

# 保留原始类型别名
Pjmp3SongInfo = Pjmp3Source if hasattr(Pjmp3Source, '__dataclass_fields__') else object


class Pjmp3Client:
    """
    pjmp3.com 网页抓取客户端（向后兼容包装器）

    此类保留用于向后兼容，新代码应使用 Pjmp3Source
    """

    BASE_URL = "https://pjmp3.com"
    SEARCH_URL = "/search.php"
    SONG_URL = "/song.php"

    def __init__(self):
        self._source = get_pjmp3_source()
        self.enabled = self._source.is_available() if self._source else False

    def search(self, keyword: str, limit: int = 20):
        """搜索歌曲"""
        if not self.enabled:
            return []
        results = self._source.search(keyword, limit)
        # 转换为旧格式
        return [self._to_old_format(r) for r in results]

    def search_with_artist_filter(self, song_name: str, artist: str = "", limit: int = 10):
        """搜索并过滤歌手（向后兼容）"""
        return self.search(song_name, limit)

    def get_song_detail(self, song_id: str):
        """获取歌曲详情"""
        if not self.enabled:
            return None
        result = self._source.get_detail(song_id)
        return self._to_old_format(result) if result else None

    def download_file(self, download_url: str, save_path: str, song_name: str = "") -> bool:
        """下载歌曲文件"""
        return self._source.download(song_id=download_url, save_path=save_path)

    def _to_old_format(self, song_info):
        """转换为旧格式"""
        if not song_info:
            return None
        from dataclasses import dataclass
        @dataclass
        class OldSongInfo:
            song_name: str = ""
            singers: str = ""
            album: str = ""
            file_size: str = ""
            duration: str = ""
            source: str = "Pjmp3Client"
            ext: str = "mp3"
            download_url: str = None
            duration_s: int = 0
            song_id: str = ""
            cover_url: str = ""
            preview_url: str = None
        return OldSongInfo(
            song_name=song_info.song_name,
            singers=song_info.singers,
            album=song_info.album,
            file_size=song_info.file_size,
            duration=song_info.duration,
            source=song_info.source,
            ext=song_info.ext,
            download_url=song_info.download_url,
            duration_s=song_info.duration_s,
            song_id=song_info.song_id,
            cover_url=song_info.cover_url,
            preview_url=song_info.preview_url,
        )


# 全局客户端实例（向后兼容）
_pjmp3_client: Optional[Pjmp3Client] = None


def get_pjmp3_client() -> Optional[Pjmp3Client]:
    """获取全局 Pjmp3Client 实例"""
    global _pjmp3_client
    if _pjmp3_client is None:
        _pjmp3_client = Pjmp3Client()
    return _pjmp3_client


def reset_pjmp3_client():
    """重置全局实例"""
    global _pjmp3_client
    _pjmp3_client = None
