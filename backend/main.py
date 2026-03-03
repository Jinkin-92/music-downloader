"""
FastAPI 后端服务主入口

PyQt6 音乐下载器的 Web 版本后端
提供RESTful API和SSE实时推送功能
"""
# 设置UTF-8编码（解决Windows上的GBK编码问题）
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8MODE'] = '1'
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import logging
import json

# ==================== 路径配置 ====================
# 必须在日志配置前定义BASE_DIR
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 配置文件和控制台日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'backend.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"后端日志文件: {os.path.join(LOG_DIR, 'backend.log')}")

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入API路由
from backend.api.search import router as search_router
from backend.api.batch import router as batch_router
from backend.api.download import router as download_router
from backend.api.playlist import router as playlist_router
from backend.api.logs import router as logs_router

# ==================== FastAPI应用 ====================

app = FastAPI(
    title="PyQt6 音乐下载器 API",
    description="Web版本的后端API服务 - 支持单曲搜索、批量下载、歌单导入",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 目录配置 ====================
# BASE_DIR和LOG_DIR已在文件开头定义
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'musicdl_outputs')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==================== 注册路由 ====================

# API路由
app.include_router(search_router)
app.include_router(batch_router)
app.include_router(download_router)
app.include_router(playlist_router)
app.include_router(logs_router)

# 静态文件（前端）
frontend_dir = os.path.join(BASE_DIR, 'backend', 'static')
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    logger.info(f"静态文件目录: {frontend_dir}")
else:
    logger.warning(f"静态文件目录不存在: {frontend_dir}")


# ==================== 根端点 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "PyQt6 音乐下载器 API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "running",
        "endpoints": {
            "search": "/api/search/",
            "batch": "/api/batch/",
            "download": "/api/download/",
            "playlist": "/api/playlist/"
        }
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }


# ==================== 启动配置 ====================

if __name__ == "__main__":
    import uvicorn
    import asyncio

    # 运行服务器
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8002,  # 修复：使用8002端口匹配前端代理配置
        reload=False,  # 修复：reload=True会导致文件变化时自动重启，中断正在执行的下载
        log_level="info"
    )
