"""
下载API端点 - 简化版

提供异步下载功能，支持进度推送和403错误处理。
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import json
import asyncio
import subprocess
import sys
import os
import tempfile

from core import MusicDownloader, DOWNLOAD_DIR

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/download',
    tags=['下载']
)

music_downloader = MusicDownloader()


class DownloadSong(BaseModel):
    song_name: str
    singers: str
    album: str = ''
    size: str = ''
    duration: str = ''
    source: str


class DownloadRequest(BaseModel):
    songs: List[DownloadSong]
    download_dir: Optional[str] = None


@router.post('/stream')
async def stream_download(request: DownloadRequest):
    """SSE流式下载"""
    async def download_stream():
        try:
            songs_data = [song.model_dump() for song in request.songs]
            total_songs = len(songs_data)
            logger.info(f"[SSE下载] 开始下载 {total_songs} 首歌曲")

            yield f"event: start\ndata: {json.dumps({'total': total_songs})}\n\n"

            completed_count = 0
            failed_count = 0

            # 写入临时文件
            songs_json_path = os.path.join(tempfile.gettempdir(), 'download_songs.json')
            with open(songs_json_path, 'w', encoding='utf-8') as f:
                json.dump(songs_data, f, ensure_ascii=False)

            # 下载脚本 - 使用动态路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            script_path = os.path.join(tempfile.gettempdir(), 'run_download.py')
            script_content = '''# -*- coding: utf-8 -*-
import sys
import json
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8MODE"] = "1"
os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANG"] = "C.UTF-8"

PROJECT_ROOT = r"''' + project_root.replace('\\', '\\\\') + '''"
sys.path.insert(0, PROJECT_ROOT)
from core import MusicDownloader

# 读取歌曲数据
songs_json_path = os.path.join(os.environ.get("TEMP", "/tmp"), "download_songs.json")
with open(songs_json_path, "r", encoding="utf-8") as f:
    songs_data = json.load(f)

downloader = MusicDownloader()
all_sources = ["QQMusicClient", "NeteaseMusicClient", "KugouMusicClient", "KuwoMusicClient"]

total = len(songs_data)
for idx, song in enumerate(songs_data):
    song_name = song.get("song_name", "Unknown")
    singers = song.get("singers", "")
    source = song.get("source", "")

    progress = str(idx + 1) + "/" + str(total) + ": " + song_name + " - " + singers
    print("下载 " + progress)

    # 搜索
    search_keyword = song_name + " " + singers
    search_keyword = search_keyword.strip()

    # 首先尝试指定来源
    search_results = downloader.search(search_keyword, sources=[source])

    # 如果指定来源无结果，尝试所有来源
    if not search_results.get(source):
        print("DEBUG: 指定来源无结果，尝试所有来源")
        search_results = downloader.search(search_keyword, sources=all_sources)

    # 打印搜索结果
    print("DEBUG: 搜索结果: " + str(list(search_results.keys())))

    # 匹配和下载
    found = False
    for src, songs_list in search_results.items():
        for s in songs_list:
            song_info_obj = s.get("song_info_obj")
            if song_info_obj and hasattr(song_info_obj, "song_name"):
                if song_info_obj.song_name == song_name and singers in song_info_obj.singers:
                    print("DEBUG: 找到匹配，准备下载 " + song_name + " (from " + src + ")")
                    try:
                        if hasattr(downloader._client, "download"):
                            downloader._client.download([song_info_obj])
                        else:
                            downloader._client.music_clients.get(src).download([song_info_obj])
                        print("SUCCESS: " + song_name)
                        found = True
                        break
                    except Exception as de:
                        print("DEBUG: download失败: " + str(de))
        if found:
            break

    if not found:
        print("FAILED: " + song_name + " - 未找到匹配")
'''

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # 执行
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            # 发送输出
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        if 'SUCCESS' in line:
                            completed_count += 1
                            yield f"event: progress\ndata: {json.dumps({'completed': completed_count, 'total': total_songs, 'percent': 100, 'success': True})}\n\n"
                        elif 'FAILED' in line or 'ERROR' in line:
                            failed_count += 1
                            yield f"event: progress\ndata: {json.dumps({'completed': i+1, 'total': total_songs, 'percent': 100, 'success': False, 'error': line})}\n\n"

            # 完成
            yield f"event: complete\ndata: {json.dumps({'total': total_songs, 'completed': completed_count, 'failed': failed_count, 'percent': 100})}\n\n"

        except Exception as e:
            logger.error(f"[SSE下载] 错误: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        download_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
