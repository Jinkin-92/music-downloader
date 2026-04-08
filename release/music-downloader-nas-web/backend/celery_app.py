"""
Celery应用配置

用于异步任务处理，支持批量搜索和下载。
使用Redis作为broker和backend。
"""
import os
from celery import Celery

# Redis配置
REDIS_URL = os.getenv(
    'REDIS_URL',
    'redis://localhost:6379/0'
)

# 创建Celery应用
celery_app = Celery(
    'music_downloader',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Celery配置
celery_app.conf.update(
    # 序列化配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,

    # Worker配置
    worker_prefetch_multiplier=1,  # 每次只预取1个任务
    task_acks_late=True,          # 任务完成后才确认
    worker_max_tasks_per_child=50, # 每个worker处理50个任务后重启

    # 任务配置
    task_track_started=True,       # 跟踪任务开始时间
    task_time_limit=3600,          # 任务最大执行时间（1小时）
    task_soft_time_limit=3000,     # 任务软时间限制（50分钟）

    # 结果配置
    result_expires=86400,          # 结果保存1天
    result_compression='gzip',     # 压缩结果

    # 重试配置
    task_autoretry_for=(Exception,),  # 所有异常自动重试
    task_retry_max_delay=60,          # 最大重试延迟60秒
    task_retry_delay=30,               # 默认重试延迟30秒

    # 日志配置
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# 自动发现任务（如果使用tasks.py文件）
# celery_app.autodiscover_tasks(['backend.workers'])

if __name__ == '__main__':
    # 启动Celery worker
    celery_app.start()
