"""
Download History Database Model - SQLite数据库模型

管理下载历史记录，支持：
- 下载记录持久化
- 文件存在性检测
- 重复歌曲检测
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager

from core.config import HISTORY_DB_PATH


@dataclass
class DownloadRecord:
    """下载记录数据类"""
    id: Optional[int] = None
    song_name: str = ""
    singers: str = ""
    file_path: str = ""
    file_size: int = 0
    source: str = ""
    similarity: float = 0.0
    download_time: datetime = None
    file_exists: bool = True

    def __post_init__(self):
        if self.download_time is None:
            self.download_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'song_name': self.song_name,
            'singers': self.singers,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'source': self.source,
            'similarity': self.similarity,
            'download_time': self.download_time.isoformat() if self.download_time else None,
            'file_exists': self.file_exists,
        }


class DownloadHistoryDB:
    """
    下载历史数据库管理类

    使用SQLite存储下载历史，支持：
    - 线程安全的数据库访问
    - 文件存在性检测
    - 重复歌曲检测
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_path = HISTORY_DB_PATH
        self._local = threading.local()
        self._ensure_db()
        self._initialized = True

    def _ensure_db(self):
        """确保数据库和表存在"""
        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_name TEXT NOT NULL,
                    singers TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    file_size INTEGER DEFAULT 0,
                    source TEXT,
                    similarity REAL DEFAULT 0,
                    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_exists INTEGER DEFAULT 1
                )
            ''')

            # 创建索引加速查询
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_song_name_singers
                ON download_history(song_name, singers)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_exists
                ON download_history(file_exists)
            ''')

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """获取线程安全的数据库连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # 启用外键约束
            self._local.conn.execute('PRAGMA foreign_keys = ON')

        try:
            yield self._local.conn
        except Exception:
            self._local.conn.rollback()
            raise

    def add_record(self, record: DownloadRecord) -> int:
        """
        添加下载记录

        Args:
            record: 下载记录

        Returns:
            新记录的ID
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO download_history
                (song_name, singers, file_path, file_size, source, similarity, file_exists)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.song_name,
                record.singers,
                record.file_path,
                record.file_size,
                record.source,
                record.similarity,
                1 if record.file_exists else 0
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_records(self, include_missing: bool = True) -> List[DownloadRecord]:
        """
        获取所有下载记录

        Args:
            include_missing: 是否包含缺失的文件

        Returns:
            下载记录列表
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            if include_missing:
                cursor = conn.execute('''
                    SELECT * FROM download_history
                    ORDER BY download_time DESC
                ''')
            else:
                cursor = conn.execute('''
                    SELECT * FROM download_history
                    WHERE file_exists = 1
                    ORDER BY download_time DESC
                ''')

            return [self._row_to_record(row) for row in cursor.fetchall()]

    def check_file_exists(self, song_name: str, singers: str) -> bool:
        """
        检查歌曲是否已下载

        Args:
            song_name: 歌曲名
            singers: 歌手

        Returns:
            是否已下载
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM download_history
                WHERE song_name = ? AND singers = ? AND file_exists = 1
            ''', (song_name, singers))
            return cursor.fetchone()[0] > 0

    def get_existing_songs(self, songs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        获取已存在的歌曲列表（用于过滤重复）

        Args:
            songs: 待检查的歌曲列表 [{'name': '歌名', 'singer': '歌手'}, ...]

        Returns:
            已存在的歌曲列表
        """
        existing = []
        with self._get_connection() as conn:
            for song in songs:
                cursor = conn.execute('''
                    SELECT file_path FROM download_history
                    WHERE song_name = ? AND singers = ? AND file_exists = 1
                    LIMIT 1
                ''', (song.get('name', ''), song.get('singer', '')))
                row = cursor.fetchone()
                if row:
                    existing.append({
                        **song,
                        'file_path': row[0]
                    })
        return existing

    def update_file_status(self, record_id: int, exists: bool):
        """
        更新文件存在状态

        Args:
            record_id: 记录ID
            exists: 文件是否存在
        """
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE download_history
                SET file_exists = ?
                WHERE id = ?
            ''', (1 if exists else 0, record_id))
            conn.commit()

    def verify_all_files(self) -> Dict[str, int]:
        """
        验证所有文件是否存在

        Returns:
            统计信息 {'total': 总数, 'valid': 有效数, 'missing': 缺失数}
        """
        records = self.get_all_records()
        stats = {'total': len(records), 'valid': 0, 'missing': 0}

        for record in records:
            exists = Path(record.file_path).exists()
            self.update_file_status(record.id, exists)
            if exists:
                stats['valid'] += 1
            else:
                stats['missing'] += 1

        return stats

    def delete_record(self, record_id: int):
        """
        删除记录

        Args:
            record_id: 记录ID
        """
        with self._get_connection() as conn:
            conn.execute('DELETE FROM download_history WHERE id = ?', (record_id,))
            conn.commit()

    def clean_missing_records(self) -> int:
        """
        清理缺失文件的记录

        Returns:
            删除的记录数
        """
        with self._get_connection() as conn:
            cursor = conn.execute('DELETE FROM download_history WHERE file_exists = 0')
            conn.commit()
            return cursor.rowcount

    def get_history_directories(self) -> List[str]:
        """
        获取历史下载目录列表（用于UI快捷选择）

        Returns:
            目录路径列表
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT dirname(file_path) as dir
                FROM download_history
                WHERE file_exists = 1
                ORDER BY dir
            ''')
            # SQLite没有dirname函数，使用Python处理
            pass

        # 使用Python获取目录
        records = self.get_all_records(include_missing=False)
        dirs = set()
        for record in records:
            path = Path(record.file_path)
            if path.parent.exists():
                dirs.add(str(path.parent))

        return sorted(list(dirs))

    def _row_to_record(self, row: sqlite3.Row) -> DownloadRecord:
        """将数据库行转换为DownloadRecord"""
        return DownloadRecord(
            id=row['id'],
            song_name=row['song_name'],
            singers=row['singers'],
            file_path=row['file_path'],
            file_size=row['file_size'],
            source=row['source'],
            similarity=row['similarity'],
            download_time=datetime.fromisoformat(row['download_time']) if row['download_time'] else None,
            file_exists=bool(row['file_exists'])
        )


# SQLite自定义函数：获取目录名
def register_sqlite_functions(conn):
    """注册自定义SQLite函数"""
    def dirname(path):
        return str(Path(path).parent)

    conn.create_function('dirname', 1, dirname)