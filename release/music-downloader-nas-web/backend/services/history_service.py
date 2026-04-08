"""
Download History Service - 下载历史服务

提供下载历史管理功能：
- 记录下载
- 检查重复
- 文件状态验证
- 打开文件夹
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from backend.models.download_history import DownloadHistoryDB, DownloadRecord


class HistoryService:
    """
    下载历史服务

    单例模式，提供统一的下载历史管理接口
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db = DownloadHistoryDB()
        return cls._instance

    def record_download(
        self,
        song_name: str,
        singers: str,
        file_path: str,
        file_size: int = 0,
        source: str = "",
        similarity: float = 0.0
    ) -> int:
        """
        记录下载

        Args:
            song_name: 歌曲名
            singers: 歌手
            file_path: 文件路径
            file_size: 文件大小
            source: 来源平台
            similarity: 匹配相似度

        Returns:
            记录ID
        """
        record = DownloadRecord(
            song_name=song_name,
            singers=singers,
            file_path=file_path,
            file_size=file_size,
            source=source,
            similarity=similarity,
            file_exists=True
        )
        return self._db.add_record(record)

    def check_duplicate(self, song_name: str, singers: str) -> bool:
        """
        检查是否已下载（用于过滤重复）

        Args:
            song_name: 歌曲名
            singers: 歌手

        Returns:
            是否已下载
        """
        return self._db.check_file_exists(song_name, singers)

    def filter_duplicates(self, songs: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        过滤已下载的歌曲

        Args:
            songs: 待检查的歌曲列表

        Returns:
            (未下载的歌曲, 已下载的歌曲)
        """
        not_downloaded = []
        already_downloaded = []

        for song in songs:
            if self.check_duplicate(song.get('name', ''), song.get('singer', '')):
                already_downloaded.append(song)
            else:
                not_downloaded.append(song)

        return not_downloaded, already_downloaded

    def get_all_history(self, include_missing: bool = True) -> List[Dict]:
        """
        获取所有下载历史

        Args:
            include_missing: 是否包含缺失文件

        Returns:
            历史记录列表
        """
        records = self._db.get_all_records(include_missing=include_missing)
        return [r.to_dict() for r in records]

    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息

        Returns:
            {'total': 总数, 'valid': 有效数, 'missing': 缺失数}
        """
        return self._db.verify_all_files()

    def open_folder(self, file_path: str) -> bool:
        """
        打开文件所在文件夹

        Args:
            file_path: 文件路径

        Returns:
            是否成功
        """
        path = Path(file_path)

        if not path.exists():
            return False

        folder = path.parent

        try:
            system = platform.system()
            if system == 'Windows':
                # Windows: 选中文件
                subprocess.run(['explorer', '/select,', str(path)], check=False)
            elif system == 'Darwin':
                # macOS: 选中文件
                subprocess.run(['open', '-R', str(path)], check=False)
            else:
                # Linux: 打开文件夹
                subprocess.run(['xdg-open', str(folder)], check=False)
            return True
        except Exception:
            return False

    def delete_file_and_record(self, record_id: int, delete_file: bool = True) -> bool:
        """
        删除记录和文件

        Args:
            record_id: 记录ID
            delete_file: 是否同时删除文件

        Returns:
            是否成功
        """
        records = self._db.get_all_records()
        record = next((r for r in records if r.id == record_id), None)

        if record is None:
            return False

        # 删除文件
        if delete_file:
            try:
                path = Path(record.file_path)
                if path.exists():
                    path.unlink()
            except Exception:
                pass

        # 删除记录
        self._db.delete_record(record_id)
        return True

    def clean_missing_records(self) -> int:
        """
        清理缺失文件的记录

        Returns:
            删除的记录数
        """
        return self._db.clean_missing_records()

    def get_history_directories(self) -> List[str]:
        """
        获取历史下载目录列表

        Returns:
            目录路径列表
        """
        return self._db.get_history_directories()


# 全局单例
history_service = HistoryService()