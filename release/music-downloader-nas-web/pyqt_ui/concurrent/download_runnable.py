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
                      可能包含_fallback_candidates字段（其他源的备用候选）
            download_dir: 下载目录（None则使用默认目录）
            max_retries: 最大重试次数（默认2次）
        """
        super().__init__()
        self.song_dict = song_dict
        self.download_dir = download_dir
        self.max_retries = max_retries
        self.downloader = MusicDownloader()
        self.signals = DownloadRunnableSignals()

        # 提取备用候选列表（用于403错误时切换源）
        self.fallback_candidates = song_dict.get('_fallback_candidates', [])

        logger.debug(
            f"SingleSongDownloadRunnable created for: {song_dict.get('song_name', 'Unknown')} "
            f"with {len(self.fallback_candidates)} fallback candidates"
        )

    def run(self):
        """执行下载（带重试机制和多源fallback）"""
        song_name = self.song_dict.get("song_name", "Unknown")
        singer = self.song_dict.get("singers", "")
        current_song_dict = self.song_dict  # 跟踪当前尝试的song_dict

        for attempt in range(self.max_retries + 1):
            try:
                current_source = current_song_dict.get("source", "Unknown")
                logger.info(
                    f"Downloading '{song_name} - {singer}' from {current_source} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                self.signals.progress.emit(f"正在下载: {song_name} - {singer}")

                # 执行下载
                self.downloader.download(
                    [current_song_dict], download_dir=self.download_dir
                )

                # 成功
                self.signals.success.emit(song_name)
                logger.info(
                    f"✓ Downloaded successfully: {song_name} - {singer} "
                    f"from {current_source}"
                )
                return

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Download failed (attempt {attempt + 1}): {song_name} - {singer} "
                    f"from {current_source} - {error_msg}"
                )

                # ⚠️ 检查是否为403错误（版权保护），如果有备用候选则尝试切换源
                is_403_error = (
                    "403" in error_msg or
                    "forbidden" in error_msg.lower() or
                    "版权" in error_msg or
                    "copyright" in error_msg.lower()
                )

                if is_403_error and self.fallback_candidates:
                    # 尝试切换到下一个源
                    fallback_source = self.fallback_candidates[0].get("source", "Unknown")
                    logger.info(
                        f"⚠️ 403 error detected, switching to fallback source: {fallback_source}"
                    )
                    self.signals.progress.emit(
                        f"403错误，切换源: {current_source} → {fallback_source}"
                    )

                    # 切换到第一个备用候选
                    current_song_dict = self.fallback_candidates.pop(0)
                    # 重置attempt计数器，给新源完整的重试机会
                    attempt = -1  # 会在循环开始时+1变成0
                    continue

                if attempt < self.max_retries:
                    # 指数退避：1s, 2s, 4s...
                    wait_time = 2**attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # 最后一次尝试失败
                    self.signals.error.emit(song_name, error_msg)
                    logger.error(
                        f"✗ Download failed after {self.max_retries} retries: "
                        f"{song_name} - {singer} - {error_msg}"
                    )
