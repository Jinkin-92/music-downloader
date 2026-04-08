"""
API路由模块

导出所有API路由器
"""
from backend.api.search import router as search_router
from backend.api.batch import router as batch_router
from backend.api.download import router as download_router

__all__ = ['search_router', 'batch_router', 'download_router']
