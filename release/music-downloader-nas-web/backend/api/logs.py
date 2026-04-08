"""
错误日志API端点

保存前端错误日志到服务器
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix='/api/logs',
    tags=['日志']
)

# 日志目录
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)


class ErrorLogEntry(BaseModel):
    """前端错误日志条目"""
    timestamp: str
    context: str
    error: Dict[str, Any]
    userAgent: str
    url: str


@router.post('/error')
async def save_error_log(log: ErrorLogEntry):
    """
    保存前端错误日志

    Args:
        log: 错误日志条目

    Returns:
        保存结果
    """
    try:
        # 按日期分组日志文件
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = LOG_DIR / f'frontend_errors_{date_str}.log'

        # 写入日志
        log_line = json.dumps(log.dict(), ensure_ascii=False)

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')

        logger.info(f"错误日志已保存: {log_file}")

        return {
            'success': True,
            'file': str(log_file)
        }

    except Exception as e:
        logger.error(f"保存错误日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get('/download')
async def download_logs(date: str = None):
    """
    下载指定日期的错误日志

    Args:
        date: 日期字符串（格式：YYYYMMDD），默认为今天

    Returns:
        日志文件
    """
    try:
        if not date:
            date = datetime.now().strftime('%Y%m%d')

        log_file = LOG_DIR / f'frontend_errors_{date}.log'

        if not log_file.exists():
            raise HTTPException(status_code=404, detail=f"日志文件不存在: {date}")

        return FileResponse(
            log_file,
            filename=f'error_logs_{date}.log',
            media_type='text/plain'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get('/list')
async def list_logs():
    """
    列出所有可用的错误日志文件

    Returns:
        日志文件列表
    """
    try:
        log_files = []

        for log_file in LOG_DIR.glob('frontend_errors_*.log'):
            # 从文件名提取日期
            date_str = log_file.stem.replace('frontend_errors_', '')
            log_files.append({
                'date': date_str,
                'file': str(log_file),
                'size': log_file.stat().st_size
            })

        # 按日期倒序排列
        log_files.sort(key=lambda x: x['date'], reverse=True)

        return {
            'success': True,
            'logs': log_files
        }

    except Exception as e:
        logger.error(f"列出日志失败: {e}")
        return {
            'success': False,
            'logs': [],
            'error': str(e)
        }
