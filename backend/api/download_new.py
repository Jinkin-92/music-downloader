@router.post('/stream')
async def stream_download(request: DownloadRequest):
    """
    SSE流式下载 - 实时推送下载进度

    使用子进程执行下载（解决Windows编码问题），通过SSE推送进度更新。

    Args:
        request: 下载请求

    Returns:
        SSE流，实时推送下载进度
    """
    import subprocess
    import sys
    import tempfile
    import os

    async def download_stream():
        """SSE下载进度流"""
        try:
            songs_data = [song.model_dump() for song in request.songs]
            total_songs = len(songs_data)

            logger.info(f"[SSE下载] 开始下载 {total_songs} 首歌曲")

            # 发送开始事件
            yield f"event: start\ndata: {json.dumps({'total': total_songs})}\n\n"

            completed_count = 0
            failed_count = 0

            # 写入临时脚本文件
            script_path = os.path.join(tempfile.gettempdir(), 'download_script.py')
            songs_json_path = os.path.join(tempfile.gettempdir(), 'download_songs.json')

            # 写入songs_data到json文件
            with open(songs_json_path, 'w', encoding='utf-8') as f:
                json.dump(songs_data, f, ensure_ascii=False)

            # 获取项目根目录（动态路径）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            download_output_dir = os.path.join(project_root, "musicdl_outputs")

            # 写入下载脚本 - 使用动态路径
            script_content = '''# -*- coding: utf-8 -*-
import sys
import json
import os

# 设置编码
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8MODE"] = "1"
os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANG"] = "C.UTF-8"

PROJECT_ROOT = r"''' + project_root.replace('\\', '\\\\') + '''"
sys.path.insert(0, PROJECT_ROOT)

from core import MusicDownloader

# 从临时文件读取歌曲数据
songs_json_path = os.path.join(os.environ.get("TEMP", "/tmp"), "download_songs.json")
with open(songs_json_path, 'r', encoding='utf-8') as f:
    songs_data = json.load(f)

DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "musicdl_outputs")
downloader = MusicDownloader()

for i, song in enumerate(songs_data):
    try:
        song_name = song.get("song_name", "Unknown")
        singers = song.get("singers", "")
        source = song.get("source", "")

        print("下载 (%d/%d): %s - %s" % (i+1, len(songs_data), song_name, singers))

        # 搜索获取SongInfo
        search_keyword = song_name + " " + singers
        search_keyword = search_keyword.strip()

        # 首先尝试指定来源
        search_results = downloader.search(search_keyword, sources=[source])

        # 如果指定来源无结果，尝试所有来源
        if not search_results.get(source):
            print("DEBUG: 指定来源无结果，尝试所有来源")
            all_sources = ['QQMusicClient', 'NeteaseMusicClient', 'KugouMusicClient', 'KuwoMusicClient']
            search_results = downloader.search(search_keyword, sources=all_sources)

        # 打印搜索结果
        print("DEBUG: 搜索结果来源: %s" % str(list(search_results.keys())))

        # 从song_info_obj获取SongInfo对象进行匹配和下载
        found = False
        for src, songs_list in search_results.items():
            for s in songs_list:
                song_info_obj = s.get('song_info_obj')
                if song_info_obj and hasattr(song_info_obj, 'song_name'):
                    if song_info_obj.song_name == song_name and singers in song_info_obj.singers:
                        print("DEBUG: 找到匹配，准备下载 %s (from %s)" % (song_name, src))
                        try:
                            # 直接使用 SongInfo 对象下载
                            if hasattr(downloader._client, 'download'):
                                downloader._client.download([song_info_obj])
                            else:
                                downloader._client.music_clients.get(src).download([song_info_obj])
                            print("SUCCESS: %s" % song_name)
                            found = True
                            break
                        except Exception as download_err:
                            print("DEBUG: download失败: %s" % str(download_err))
            if found:
                break

        if not found:
            print("FAILED: %s - 未找到匹配" % song_name)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR: %s - %s" % (song_name, str(e)))
'''

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # 执行脚本
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            # 发送子进程调试输出
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        yield f"event: debug\ndata: {json.dumps({'message': line.strip()})}\n\n"

            # 发送子进程错误输出
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    if line.strip():
                        yield f"event: debug\ndata: {json.dumps({'message': 'STDERR: ' + line.strip()})}\n\n"

            # 解析输出
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    if 'SUCCESS' in line:
                        completed_count += 1
                        progress = {
                            'completed': completed_count,
                            'total': total_songs,
                            'percent': round(completed_count / total_songs * 100),
                            'song_name': line.split('SUCCESS: ')[-1] if 'SUCCESS:' in line else '',
                            'success': True
                        }
                        yield f"event: progress\ndata: {json.dumps(progress)}\n\n"
                    elif 'FAILED' in line or 'ERROR' in line:
                        failed_count += 1
                        song_name = line.split(': ')[-1] if ': ' in line else 'Unknown'
                        progress = {
                            'completed': i + 1,
                            'total': total_songs,
                            'percent': round((i + 1) / total_songs * 100),
                            'song_name': song_name,
                            'success': False,
                            'error': line.split(' - ')[-1] if ' - ' in line else 'Download failed'
                        }
                        yield f"event: progress\ndata: {json.dumps(progress)}\n\n"

            # 发送完成事件
            final_result = {
                'total': total_songs,
                'completed': completed_count,
                'failed': failed_count,
                'percent': 100
            }
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
