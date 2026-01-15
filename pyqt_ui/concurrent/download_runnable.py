"""单首歌下载任务"""
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
from ..music_downloader import MusicDownloader
import logging
import time

logger = logging.getLogger(__name__)


class DownloadRunnableSignals(QObject):
    """DownloadRunnable的信号类"""

    progress = pyqtSignal(str)  # song_name
    success = pyqtSignal(str)  # song_name
    error = pyqtSignal(str, str)  # song_name, error_msg


class SingleSongDownloadRunnable(QRunnable):
    """单首歌的下载任务（在QThreadPool中执行）

    支持失败重试机制，自动重试最多2次。
    使用指数退避策略（1s, 2s）。
    """

    def __init__(self, song_dict: dict, download_dir: str = None, max_retries: int = 2):
        """初始化下载任务

        Args:
            song_dict: 歌曲信息字典（包含song_name, singers, song_info_obj等）
            download_dir: 下载目录（None则使用默认目录）
            max_retries: 最大重试次数（默认2次）
        """
        super().__init__()
        self.song_dict = song_dict
        self.download_dir = download_dir
        self.max_retries = max_retries
        self.downloader = MusicDownloader()
        self.signals = DownloadRunnableSignals()

        logger.debug(
            f"SingleSongDownloadRunnable created for: {song_dict.get('song_name', 'Unknown')}"
        )

    def run(self):
        """执行下载（带重试机制）"""
        song_name = self.song_dict.get("song_name", "Unknown")
        singer = self.song_dict.get("singers", "")

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Downloading '{song_name} - {singer}' (attempt {attempt + 1}/{self.max_retries + 1})")
                self.signals.progress.emit(f"正在下载: {song_name} - {singer}")

                # 执行下载
                self.downloader.download(
                    [self.song_dict], download_dir=self.download_dir
                )

                # 成功
                self.signals.success.emit(song_name)
                logger.info(f"✓ Downloaded successfully: {song_name} - {singer}")
                return

            except Exception as e:
                logger.warning(
                    f"Download failed (attempt {attempt + 1}): {song_name} - {singer} - {e}"
                )

                if attempt < self.max_retries:
                    # 指数退避：1s, 2s, 4s...
                    wait_time = 2**attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # 最后一次尝试失败
                    error_msg = f"{str(e)}"
                    self.signals.error.emit(song_name, error_msg)
                    logger.error(
                        f"✗ Download failed after {self.max_retries} retries: {song_name} - {singer} - {error_msg}"
                    )
