"""歌单解析Worker线程

在后台线程中解析歌单,避免阻塞UI。
"""
from PyQt6.QtCore import QThread, pyqtSignal
import logging
from typing import List
from .base import PlaylistSong
from .factory import PlaylistParserFactory

logger = logging.getLogger(__name__)


class PlaylistParseWorker(QThread):
    """歌单解析Worker线程

    在后台解析歌单,通过信号通知UI进度和结果。
    """

    # 信号定义
    progress = pyqtSignal(str)  # 进度信息
    finished = pyqtSignal(list)  # 解析完成,返回歌曲列表
    error = pyqtSignal(str)  # 解析错误

    def __init__(self, url: str):
        """初始化Worker

        Args:
            url: 歌单URL
        """
        super().__init__()
        self.url = url
        logger.info(f"Created PlaylistParseWorker for URL: {url}")

    def run(self):
        """执行解析任务"""
        try:
            self.progress.emit("正在解析歌单链接...")

            # 使用工厂类解析歌单
            songs = PlaylistParserFactory.parse_playlist(self.url)

            self.progress.emit(f"✓ 解析成功!共找到 {len(songs)} 首歌曲")
            logger.info(f"Parse completed: {len(songs)} songs")

            # 发送解析结果
            self.finished.emit(songs)

        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Parse error (ValueError): {error_msg}")
            self.error.emit(error_msg)

        except RuntimeError as e:
            error_msg = str(e)
            logger.error(f"Parse error (RuntimeError): {error_msg}")
            self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"解析失败: {str(e)}"
            logger.exception("Unexpected parse error")
            self.error.emit(error_msg)

    def __repr__(self) -> str:
        """对象表示"""
        return f"<PlaylistParseWorker url={self.url}>"
