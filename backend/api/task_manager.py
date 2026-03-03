"""
后台任务管理器

支持后台运行的搜索和下载任务，任务生命周期独立于前端连接。
即使前端断开，后台任务仍会继续执行。

核心功能：
- 创建后台任务
- 查询任务状态和进度
- 更新任务进度
- 取消正在运行的任务
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    CANCELLED = "cancelled"   # 已取消


class BackgroundTask:
    """
    后台任务数据类

    存储任务的所有状态信息，包括进度、结果、错误等。
    """

    def __init__(self, task_id: str, task_type: str, params: dict):
        self.task_id = task_id
        self.task_type = task_type  # 'search', 'download', 'parse_playlist' 等
        self.params = params

        # 状态信息
        self.status = TaskStatus.PENDING
        self.progress = 0  # 当前进度
        self.total = 0     # 总数量
        self.message = ""  # 状态消息

        # 执行结果
        self.result = None    # 成功时的结果数据
        self.error = None    # 失败时的错误信息

        # 时间戳
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # asyncio任务引用
        self.task: Optional[asyncio.Task] = None

    def to_dict(self) -> dict:
        """转换为字典（用于API响应）"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status.value,
            'progress': self.progress,
            'total': self.total,
            'message': self.message,
            'result': self.result if self.status == TaskStatus.COMPLETED else None,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskManager:
    """
    任务管理器（单例模式）

    管理所有后台任务的生命周期：
    - 创建任务
    - 启动任务
    - 查询任务状态
    - 更新任务进度
    - 取消任务
    """

    _instance = None
    _tasks: Dict[str, BackgroundTask] = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_task(self, task_type: str, params: dict, total: int = 0) -> str:
        """
        创建新任务

        Args:
            task_type: 任务类型 ('search', 'download', 'parse_playlist' 等)
            params: 任务参数
            total: 总数量（用于计算进度）

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())
        task = BackgroundTask(task_id, task_type, params)
        task.total = total
        self._tasks[task_id] = task
        logger.info(f"[TaskManager] 创建任务: {task_id}, 类型: {task_type}, 总数: {total}")
        return task_id

    def start_task(self, task_id: str, coro, task_name: str = None) -> str:
        """
        启动后台任务

        Args:
            task_id: 任务ID
            coro: 协程对象
            task_name: 任务名称（可选，用于日志）

        Returns:
            task_id: 任务ID
        """
        if task_id not in self._tasks:
            raise ValueError(f"任务不存在: {task_id}")

        task = self._tasks[task_id]

        # 创建asyncio任务
        async def wrapped_task():
            task.started_at = datetime.now()
            task.status = TaskStatus.RUNNING
            name = task_name or task.task_type
            logger.info(f"[TaskManager] 任务开始: {task_id} ({name})")
            try:
                await coro
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                logger.info(f"[TaskManager] 任务已取消: {task_id}")
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                logger.error(f"[TaskManager] 任务失败: {task_id}, 错误: {e}")
                import traceback
                logger.error(traceback.format_exc())

        task.task = asyncio.create_task(wrapped_task())
        logger.info(f"[TaskManager] 任务已启动: {task_id}")
        return task_id

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """获取任务"""
        return self._tasks.get(task_id)

    def get_task_dict(self, task_id: str) -> Optional[dict]:
        """获取任务字典（用于API响应）"""
        task = self.get_task(task_id)
        return task.to_dict() if task else None

    def update_progress(self, task_id: str, progress: int, message: str = ""):
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 当前进度
            message: 状态消息
        """
        if task_id in self._tasks:
            self._tasks[task_id].progress = progress
            if message:
                self._tasks[task_id].message = message
            logger.debug(f"[TaskManager] 任务进度: {task_id}, {progress}/{self._tasks[task_id].total} - {message}")

    def complete_task(self, task_id: str, result: Any):
        """
        标记任务完成

        Args:
            task_id: 任务ID
            result: 结果数据
        """
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.progress = task.total  # 确保进度为100%
            task.completed_at = datetime.now()
            logger.info(f"[TaskManager] 任务完成: {task_id}, 结果: {len(str(result))} 字节")

    def fail_task(self, task_id: str, error: str):
        """
        标记任务失败

        Args:
            task_id: 任务ID
            error: 错误信息
        """
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now()
            logger.error(f"[TaskManager] 任务失败: {task_id}, 错误: {error}")

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]

        # 如果任务还在运行，取消它
        if task.task and not task.task.done():
            task.task.cancel()
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"[TaskManager] 任务已取消: {task_id}")
            return True

        return False

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        清理旧任务

        删除超过指定时间的已完成/失败/已取消的任务。

        Args:
            max_age_hours: 最大保留时间（小时）
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        to_delete = []
        for task_id, task in self._tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at
                and task.completed_at < cutoff):
                to_delete.append(task_id)

        for task_id in to_delete:
            del self._tasks[task_id]
            logger.info(f"[TaskManager] 清理旧任务: {task_id}")

        return len(to_delete)

    def get_all_tasks(self) -> Dict[str, dict]:
        """获取所有任务（字典格式）"""
        return {
            task_id: task.to_dict()
            for task_id, task in self._tasks.items()
        }


# 全局单例
task_manager = TaskManager()
