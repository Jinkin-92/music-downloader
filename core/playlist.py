"""
歌单解析模块重导出

为了保持向后兼容，此模块重导出 pyqt_ui.playlist 中的工厂类。
这允许 backend 从 core 导入而不直接依赖 pyqt_ui。
"""

# 从 pyqt_ui.playlist 重导出
from pyqt_ui.playlist.factory import PlaylistParserFactory
from pyqt_ui.playlist.base import PlaylistSong, BasePlaylistParser

__all__ = [
    'PlaylistParserFactory',
    'PlaylistSong',
    'BasePlaylistParser',
]