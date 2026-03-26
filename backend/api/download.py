"""
下载API端点

提供异步下载功能，支持进度推送和403错误处理。
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import os
import json
import asyncio
import requests

from core import MusicDownloader, DOWNLOAD_DIR
from core.song_cache import song_info_cache
from backend.services.history_service import history_service
# Celery tasks disabled for testing
# from backend.workers.download import download_single_song_task, download_batch_songs_task

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix='/api/download',
    tags=['下载']
)

# 全局单例
music_downloader = MusicDownloader()


def _get_pjmp3_download_headers() -> dict:
    """Headers required by pjmp3 direct media links."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://pjmp3.com/",
        "Accept": "*/*",
    }


# ==================== Pydantic模型 ====================

class DownloadSong(BaseModel):
    """下载歌曲信息"""
    song_name: str = Field(..., description='歌曲名称')
    singers: str = Field(..., description='歌手')
    album: str = Field(default='', description='专辑')
    size: str = Field(default='', description='文件大小')
    duration: str = Field(default='', description='时长')
    source: str = Field(..., description='音乐源')
    song_id: Optional[str] = Field(default=None, description='缓存ID，用于获取SongInfo对象')
    download_url: Optional[str] = Field(default=None, description='直接下载URL')
    ext: Optional[str] = Field(default='mp3', description='文件扩展名')
    fallback_candidates: Optional[List[dict]] = Field(
        default=None,
        description='备选源列表',
        alias='_fallback_candidates'
    )


class DownloadRequest(BaseModel):
    """下载请求"""
    songs: List[DownloadSong] = Field(..., min_items=1, description='要下载的歌曲列表')
    download_dir: Optional[str] = Field(
        default=None,
        description='下载目录（None=默认）'
    )


class DownloadResponse(BaseModel):
    """下载响应"""
    success: bool = Field(..., description='是否成功')
    message: str = Field(..., description='响应消息')
    total: int = Field(..., description='总歌曲数')
    task_id: Optional[str] = Field(None, description='任务ID（用于查询进度）')


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description='任务ID')
    status: str = Field(..., description='任务状态')
    result: Optional[dict] = Field(None, description='任务结果')


class FilesListResponse(BaseModel):
    """文件列表响应"""
    success: bool = Field(..., description='是否成功')
    total: int = Field(..., description='文件总数')
    files: List[dict] = Field(..., description='文件列表')


# ==================== API端点 ====================

@router.post('/start', response_model=DownloadResponse)
async def start_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks
):
    """
    开始下载任务

    使用同步方式下载（Celery已禁用用于测试）。

    Args:
        request: 下载请求
        background_tasks: FastAPI后台任务

    Returns:
        下载任务信息
    """
    try:
        song_count = len(request.songs)
        logger.info(f"下载请求: {song_count} 首歌曲")

        # 转换为字典格式
        songs_dict = [song.model_dump() for song in request.songs]

        # 简化版同步下载（用于测试）
        download_dir = request.download_dir or DOWNLOAD_DIR

        def sync_download():
            for song in songs_dict:
                try:
                    # 提取SongInfo对象或重新搜索获取
                    song_obj = song.get('song_info_obj')
                    if song_obj:
                        # 使用原始SongInfo对象
                        music_downloader.download([song])
                    else:
                        # 重新搜索获取SongInfo对象
                        logger.info(f"重新搜索获取下载链接: {song['song_name']}")
                        search_results = music_downloader.search(
                            song['song_name'],
                            sources=[song['source']]
                        )
                        for src, songs_list in search_results.items():
                            for s in songs_list:
                                # s 是 SongInfo 对象，使用 getattr 访问属性
                                s_name = getattr(s, 'song_name', '')
                                if s_name == song['song_name']:
                                    song_dict = music_downloader._songinfo_to_dict(s)
                                    music_downloader.download([song_dict])
                                    logger.info(f"下载成功: {song['song_name']}")
                                    break
                    logger.info(f"下载成功: {song['song_name']}")
                except Exception as e:
                    logger.error(f"下载失败 {song['song_name']}: {e}")

        # 添加到后台任务
        background_tasks.add_task(sync_download)

        return DownloadResponse(
            success=True,
            message=f"开始下载 {song_count} 首歌曲",
            total=song_count,
            task_id="sync_task"
        )

    except Exception as e:
        logger.error(f"创建下载任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/status/{task_id}', response_model=TaskStatusResponse)
async def get_download_status(task_id: str):
    """
    获取下载任务状态（简化版，用于测试）

    Args:
        task_id: 任务ID

    Returns:
        任务状态和结果
    """
    try:
        # 简化版：假设任务总是成功
        return TaskStatusResponse(
            task_id=task_id,
            status='success',
            result={'message': 'Download completed'}
        )

    except Exception as e:
        logger.error(f"查询任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/files', response_model=FilesListResponse)
async def get_downloaded_files():
    """
    获取已下载的文件列表

    递归扫描下载目录的所有子目录，返回所有音频文件。

    Returns:
        文件列表
    """
    try:
        # 确保下载目录存在
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # 支持的音频文件扩展名
        audio_extensions = ('.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac', '.wma')

        # 递归扫描所有子目录
        files = []
        for root, dirs, filenames in os.walk(DOWNLOAD_DIR):
            for filename in filenames:
                # 只返回音频文件
                if filename.lower().endswith(audio_extensions):
                    filepath = os.path.join(root, filename)
                    stat = os.stat(filepath)
                    # 计算相对路径，便于前端显示来源
                    rel_path = os.path.relpath(filepath, DOWNLOAD_DIR)
                    files.append({
                        'name': filename,
                        'path': rel_path,  # 相对路径，显示来源目录
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })

        logger.info(f"扫描下载目录: {len(files)} 个音频文件")

        return FilesListResponse(
            success=True,
            total=len(files),
            files=files
        )

    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/stream')
async def stream_download_get(
    songs_json: str,
    download_dir: Optional[str] = None
):
    """
    SSE流式下载 - GET版本（EventSource兼容）

    使用后台任务执行下载，通过SSE推送进度更新。

    Args:
        songs_json: JSON字符串格式的歌曲列表
        download_dir: 下载目录（可选）

    Returns:
        SSE流，实时推送下载进度
    """
    # 解析歌曲列表
    try:
        songs = json.loads(songs_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid songs_json format")

    # 创建请求对象
    request = DownloadRequest(songs=songs, download_dir=download_dir)
    return await _execute_download_stream(request)


@router.post('/stream')
async def stream_download(request: DownloadRequest):
    """
    SSE流式下载 - POST版本

    使用后台任务执行下载，通过SSE推送进度更新。

    Args:
        request: 下载请求

    Returns:
        SSE流，实时推送下载进度
    """
    return await _execute_download_stream(request)


async def _execute_download_stream(request: DownloadRequest):
    async def download_stream():
        """SSE下载进度流"""
        try:
            songs_dict = [song.model_dump() for song in request.songs]
            total_songs = len(songs_dict)
            download_dir = request.download_dir or DOWNLOAD_DIR

            logger.info(f"[SSE下载] 开始下载 {total_songs} 首歌曲")

            # 发送开始事件
            yield f"event: start\ndata: {json.dumps({'total': total_songs})}\n\n"

            completed_count = 0
            failed_count = 0

            # 逐首下载并实时发送进度
            for index, song in enumerate(songs_dict):
                try:
                    song_name = song.get('song_name', 'Unknown')
                    singers = song.get('singers', '')
                    song_id = song.get('song_id')
                    download_url = song.get('download_url')
                    ext = song.get('ext', 'mp3')
                    source = song.get('source', '')
                    logger.info(f"[SSE下载] 下载 ({index+1}/{total_songs}): {song_name} - {singers}")

                    # 优先级1: 使用 song_id 从缓存获取 SongInfo 对象
                    if song_id:
                        cached_info = song_info_cache.get_info(song_id)
                        if cached_info:
                            song_info_obj = cached_info['song_info_obj']
                            logger.info(f"[缓存命中] song_id={song_id}, 直接下载")
                            try:
                                music_downloader.download(
                                    [{
                                        'song_info_obj': song_info_obj,
                                        'source': source or getattr(song_info_obj, 'source', '')
                                    }],
                                    download_dir=download_dir
                                )

                                # 记录下载历史
                                try:
                                    file_name = f"{song_name} - {singers}.mp3"
                                    file_name = ''.join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.'))
                                    save_path = os.path.join(download_dir, file_name)
                                    if os.path.exists(save_path):
                                        file_size = os.path.getsize(save_path)
                                        history_service.record_download(
                                            song_name=song_name,
                                            singers=singers,
                                            file_path=save_path,
                                            file_size=file_size,
                                            source=song.get('source', ''),
                                            similarity=0.0
                                        )
                                except Exception as hist_err:
                                    logger.warning(f"记录下载历史失败: {hist_err}")

                                completed_count += 1
                                progress = {
                                    'completed': index + 1,
                                    'total': total_songs,
                                    'percent': round((index + 1) / total_songs * 100),
                                    'song_name': song_name,
                                    'success': True
                                }
                                logger.info(f"[SSE下载] 进度: {progress['percent']}% - {song_name}")
                                yield f"event: progress\ndata: {json.dumps(progress)}\n\n"
                                continue
                            except Exception as e:
                                logger.warning(f"[缓存下载] 失败: {e}，尝试其他方式")
                        else:
                            logger.warning(f"[缓存未命中] song_id={song_id}")

                    # 优先级2: 使用 download_url 直接下载
                    if download_url:
                        logger.info(f"[直接下载] 使用 download_url: {download_url[:50]}...")
                        try:
                            request_headers = _get_pjmp3_download_headers() if source == 'Pjmp3Client' else None
                            # 使用 requests 直接下载
                            response = requests.get(
                                download_url,
                                headers=request_headers,
                                stream=True,
                                timeout=60
                            )
                            response.raise_for_status()

                            # 生成文件名
                            filename = f"{song_name} - {singers}.{ext}"
                            # 清理文件名中的特殊字符
                            filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
                            save_path = os.path.join(download_dir, filename)

                            # 确保下载目录存在
                            os.makedirs(download_dir, exist_ok=True)

                            # 写入文件
                            with open(save_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)

                            logger.info(f"[直接下载] 保存成功: {save_path}")
                            completed_count += 1

                            # 记录下载历史
                            try:
                                file_size = os.path.getsize(save_path)
                                history_service.record_download(
                                    song_name=song_name,
                                    singers=singers,
                                    file_path=save_path,
                                    file_size=file_size,
                                    source=song.get('source', ''),
                                    similarity=0.0
                                )
                            except Exception as hist_err:
                                logger.warning(f"记录下载历史失败: {hist_err}")

                            # 发送进度更新
                            progress = {
                                'completed': index + 1,
                                'total': total_songs,
                                'percent': round((index + 1) / total_songs * 100),
                                'song_name': song_name,
                                'success': True
                            }
                            yield f"event: progress\ndata: {json.dumps(progress)}\n\n"
                            continue  # 成功下载，跳过后续的 re-search 逻辑
                        except Exception as e:
                            logger.warning(f"[直接下载] 失败: {e}，尝试 fallback 方式")

                    # 优先级3: Fallback - 重新搜索获取下载链接
                    logger.info(f"[Fallback] 重新搜索获取下载链接: {song_name} - {singers}")
                    search_keyword = f"{song_name} {singers}".strip()
                    search_results = music_downloader.search(
                        search_keyword,
                        sources=[song['source']]
                    )

                    # 尝试精确匹配（歌名+歌手）
                    found = False
                    for src, songs_list in search_results.items():
                        for s in songs_list:
                            # s 是字典，使用 get() 访问属性
                            s_name = s.get('song_name', '')
                            s_singers = s.get('singers', '')
                            # 匹配逻辑：歌名完全匹配，歌手部分匹配
                            if (s_name == song_name and
                                singers in s_singers):
                                music_downloader.download([s], download_dir=download_dir)
                                found = True
                                logger.info(f"下载成功: {song_name} - {singers}")
                                break
                        if found:
                            break

                    if not found:
                        # 如果精确匹配失败，尝试只匹配歌名
                        for src, songs_list in search_results.items():
                            for s in songs_list:
                                s_name = s.get('song_name', '')
                                if s_name == song_name:
                                    music_downloader.download([s], download_dir=download_dir)
                                    found = True
                                    logger.info(f"下载成功（歌名匹配）: {song_name}")
                                    break
                            if found:
                                break

                    if not found:
                        logger.warning(f"未找到匹配的下载链接: {song_name} - {singers}")
                        raise Exception(f"未找到匹配的下载链接")

                    completed_count += 1

                    # 记录下载历史
                    try:
                        file_name = f"{song_name} - {singers}.mp3"
                        file_name = ''.join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.'))
                        save_path = os.path.join(download_dir, file_name)
                        if os.path.exists(save_path):
                            file_size = os.path.getsize(save_path)
                            history_service.record_download(
                                song_name=song_name,
                                singers=singers,
                                file_path=save_path,
                                file_size=file_size,
                                source=song.get('source', ''),
                                similarity=0.0
                            )
                    except Exception as hist_err:
                        logger.warning(f"记录下载历史失败: {hist_err}")

                    # 发送进度更新
                    progress = {
                        'completed': index + 1,
                        'total': total_songs,
                        'percent': round((index + 1) / total_songs * 100),
                        'song_name': song_name,
                        'success': True
                    }
                    logger.info(f"[SSE下载] 进度: {progress['percent']}% - {song_name}")
                    yield f"event: progress\ndata: {json.dumps(progress)}\n\n"

                except Exception as e:
                    failed_count += 1
                    logger.error(f"[SSE下载] 下载失败 {song.get('song_name', 'Unknown')}: {e}")

                    # 发送失败进度
                    progress = {
                        'completed': index + 1,
                        'total': total_songs,
                        'percent': round((index + 1) / total_songs * 100),
                        'song_name': song.get('song_name', 'Unknown'),
                        'success': False,
                        'error': str(e)
                    }
                    yield f"event: progress\ndata: {json.dumps(progress)}\n\n"

            # 发送完成事件
            final_result = {
                'total': total_songs,
                'completed': completed_count,
                'failed': failed_count,
                'percent': 100
            }
            logger.info(f"[SSE下载] 下载完成: {completed_count}/{total_songs} 成功, {failed_count} 失败")
            yield f"event: complete\ndata: {json.dumps(final_result)}\n\n"

        except Exception as e:
            logger.error(f"[SSE下载] 下载失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        download_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
