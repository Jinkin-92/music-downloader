"""歌单解析器工厂

根据URL自动选择合适的解析器。
"""
import logging
from typing import List
from .base import BasePlaylistParser, PlaylistSong

logger = logging.getLogger(__name__)


class PlaylistParserFactory:
    """歌单解析器工厂类

    根据歌单URL自动选择合适的解析器。
    每次请求创建新的解析器实例，避免多进程环境下共享Session对象。
    """

    _parser_classes = []
    _initialized = False

    @classmethod
    def register_parser_class(cls, parser_class: type):
        """注册解析器类（而非实例）

        Args:
            parser_class: 解析器类
        """
        if parser_class not in cls._parser_classes:
            cls._parser_classes.append(parser_class)
            logger.info(f"Registered parser class: {parser_class.__name__}")

    @classmethod
    def initialize_parsers(cls):
        """初始化所有解析器类

        在首次使用时调用,注册所有平台的解析器类。
        """
        if cls._initialized:
            return

        # 延迟导入避免循环依赖
        try:
            from .netease import NeteasePlaylistParser
            cls.register_parser_class(NeteasePlaylistParser)
        except ImportError as e:
            logger.warning(f"Failed to import NeteasePlaylistParser: {e}")

        try:
            from .qqmusic import QQMusicPlaylistParser
            cls.register_parser_class(QQMusicPlaylistParser)
        except ImportError as e:
            logger.warning(f"Failed to import QQMusicPlaylistParser: {e}")

        cls._initialized = True
        logger.info(f"Initialized {len(cls._parser_classes)} parser class(es)")

    @classmethod
    def create_parser(cls, url: str) -> BasePlaylistParser:
        """根据URL创建对应的解析器（每次创建新实例）

        Args:
            url: 歌单URL

        Returns:
            对应的解析器实例

        Raises:
            ValueError: 不支持的平台或URL格式无效
        """
        cls.initialize_parsers()

        for parser_class in cls._parser_classes:
            # 创建临时实例用于验证URL
            temp_parser = parser_class()
            if temp_parser.validate_url(url):
                logger.info(f"Selected parser: {parser_class.__name__} for URL: {url}")
                return temp_parser

        supported = ", ".join([
            parser_class.__name__ for parser_class in cls._parser_classes
        ])
        raise ValueError(
            f"不支持的歌单链接或URL格式错误\n"
            f"URL: {url}\n"
            f"支持的平台: {supported}"
        )

    @classmethod
    def parse_playlist(cls, url: str) -> List[PlaylistSong]:
        """便捷方法:直接解析歌单

        Args:
            url: 歌单URL

        Returns:
            歌曲列表

        Raises:
            ValueError: URL格式无效
            RuntimeError: 解析失败
        """
        logger.info(f"[FACTORY] parse_playlist called for: {url}")
        parser = cls.create_parser(url)
        songs = parser.parse(url)
        logger.info(f"[FACTORY] parser returned {len(songs)} songs")

        # 标记来源平台
        platform = parser.get_platform_name()
        for song in songs:
            if not song.source_platform:
                song.source_platform = platform

        logger.info(f"Parsed {len(songs)} songs from {platform}")
        return songs

    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """获取支持的平台列表

        Returns:
            平台名称列表
        """
        cls.initialize_parsers()
        # 创建临时实例获取平台名称
        return [parser_class().get_platform_name() for parser_class in cls._parser_classes]
