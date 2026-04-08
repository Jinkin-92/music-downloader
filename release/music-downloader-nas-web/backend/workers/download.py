"""
Celery下载任务

处理异步下载任务，支持：
- 并发下载
- 403错误自动切换源
- 进度推送
- 失败重试
"""
import time
import logging
from typing import List, Dict, Optional
from pathlib import Path

from backend.celery_app import celery_app
from core import MusicDownloader, DOWNLOAD_DIR

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    name='tasks.download_single_song'
)
def download_single_song_task(
    self,
    song_dict: Dict,
    fallback_candidates: Optional[List[Dict]] = None,
    download_dir: Optional[str] = None
) -> Dict:
    """
    单歌下载任务（Celery Worker版）

    支持多源fallback：遇到403错误自动切换源。

    Args:
        self: Celery任务实例
        song_dict: 歌曲信息字典
        fallback_candidates: 备选源列表（按优先级排序）
        download_dir: 下载目录

    Returns:
        {
            'success': bool,
            'song_name': str,
            'source': str,
            'error': str (如果失败)
        }
    """
    downloader = MusicDownloader()
    download_path = Path(download_dir or DOWNLOAD_DIR)

    # 确保下载目录存在
    download_path.mkdir(parents=True, exist_ok=True)

    fallback_candidates = fallback_candidates or []
    current_song = song_dict
    current_source = song_dict.get('source', 'Unknown')

    # 更新任务状态
    self.update_state(
        state='PROGRESS',
        meta={
            'message': f"开始下载: {song_dict.get('song_name')}",
            'progress': 0,
            'source': current_source
        }
    )

    for attempt in range(self.max_retries + 1):
        try:
            logger.info(
                f"下载尝试 {attempt + 1}/{self.max_retries + 1}: "
                f"{current_song.get('song_name')} from {current_source}"
            )

            # 执行下载
            downloader.download(
                [current_song],
                download_dir=str(download_path)
            )

            # 下载成功
            logger.info(f"下载成功: {current_song.get('song_name')}")
            return {
                'success': True,
                'song_name': current_song.get('song_name'),
                'singers': current_song.get('singers'),
                'source': current_source,
                'attempt': attempt + 1
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"下载失败 (attempt {attempt + 1}): {error_msg}")

            # 检查是否是403错误
            is_403_error = any(
                keyword in error_msg.lower()
                for keyword in ['403', 'forbidden', '版权', 'copyright']
            )

            if is_403_error and fallback_candidates:
                # 有备选源，切换源
                if len(fallback_candidates) > 0:
                    current_song = fallback_candidates.pop(0)
                    current_source = current_song.get('source', 'Unknown')

                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'message': f"403错误，切换到: {current_source}",
                            'progress': attempt * 20,
                            'source': current_source
                        }
                    )

                    # 重置重试计数（新源有新的重试机会）
                    continue
                else:
                    # 没有更多备选源了
                    logger.error(f"所有源都失败: {song_dict.get('song_name')}")
                    return {
                        'success': False,
                        'song_name': song_dict.get('song_name'),
                        'error': '所有音乐源都返回403错误（版权保护）',
                        'source': current_source,
                        'attempts': attempt + 1
                    }

            # 非403错误，检查是否可以重试
            if attempt < self.max_retries:
                # 指数退避
                wait_time = 2 ** attempt
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

                self.update_state(
                    state='PROGRESS',
                    meta={
                        'message': f"下载失败，{wait_time}秒后重试",
                        'progress': attempt * 20,
                        'error': error_msg
                    }
                )
            else:
                # 达到最大重试次数
                logger.error(f"下载失败，已达最大重试次数: {song_dict.get('song_name')}")
                return {
                    'success': False,
                    'song_name': song_dict.get('song_name'),
                    'error': error_msg,
                    'source': current_source,
                    'attempts': attempt + 1
                }

    # 理论上不应该到这里
    return {
        'success': False,
        'song_name': song_dict.get('song_name'),
        'error': '未知错误',
        'source': current_source
    }


@celery_app.task(
    bind=True,
    name='tasks.download_batch_songs'
)
def download_batch_songs_task(
    self,
    songs: List[Dict],
    download_dir: Optional[str] = None
) -> Dict:
    """
    批量下载任务（Celery Group版）

    创建一组下载任务，并发执行。

    Args:
        self: Celery任务实例
        songs: 要下载的歌曲列表
        download_dir: 下载目录

    Returns:
        {
            'total': int,
            'success': int,
            'failed': int,
            'results': List[Dict]
        }
    """
    from celery import group

    total = len(songs)
    logger.info(f"开始批量下载: {total} 首歌曲")

    # 创建下载任务组
    job = group(
        download_single_song_task.s(
            song_dict=song,
            fallback_candidates=song.get('_fallback_candidates', []),
            download_dir=download_dir
        )
        for song in songs
    )

    # 异步执行任务组
    result = job.apply_async()

    # 等待所有任务完成（带进度更新）
    downloaded_count = 0
    failed_count = 0
    results_list = []

    while not result.ready():
        # 检查已完成的任务
        completed_tasks = sum(1 for r in result.results if r.ready())
        progress = int((completed_tasks / total) * 100) if total > 0 else 0

        self.update_state(
            state='PROGRESS',
            meta={
                'message': f"下载中... {completed_tasks}/{total}",
                'progress': progress,
                'downloaded': completed_tasks,
                'total': total
            }
        )

        time.sleep(1)  # 每秒检查一次

    # 收集结果
    for task_result in result.results:
        if task_result.successful():
            result_data = task_result.get()
            if result_data.get('success'):
                downloaded_count += 1
            else:
                failed_count += 1
            results_list.append(result_data)
        else:
            failed_count += 1
            results_list.append({
                'success': False,
                'error': str(task_result.result)
            })

    logger.info(
        f"批量下载完成: {downloaded_count} 成功, "
        f"{failed_count} 失败"
    )

    return {
        'total': total,
        'success': downloaded_count,
        'failed': failed_count,
        'results': results_list
    }


@celery_app.task(
    bind=True,
    name='tasks.batch_search'
)
def batch_search_task(
    self,
    batch_text: str,
    sources: List[str],
    options: Optional[Dict] = None
) -> Dict:
    """
    批量搜索任务（Celery版）

    使用AsyncConcurrentSearcher进行并发搜索。

    Args:
        self: Celery任务实例
        batch_text: 批量文本
        sources: 音乐源列表
        options: 额外选项

    Returns:
        批量搜索结果
    """
    import asyncio
    from backend.workers.concurrent_search import AsyncConcurrentSearcher

    options = options or {}
    concurrency = options.get('concurrency', 5)

    # 创建搜索器
    searcher = AsyncConcurrentSearcher(concurrency=concurrency)

    # 解析歌曲数（用于进度报告）
    from core import BatchParser
    parser = BatchParser()
    songs = parser.parse(batch_text)
    total_songs = len(songs)

    self.update_state(
        state='PROGRESS',
        meta={
            'message': f'准备搜索 {total_songs} 首歌曲...',
            'progress': 0,
            'total': total_songs
        }
    )

    # 执行异步批量搜索
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            searcher.search_batch(batch_text, sources)
        )

        logger.info(
            f"批量搜索完成: {result['matched']}/{result['total']} 匹配"
        )

        return result

    except Exception as e:
        logger.error(f"批量搜索失败: {e}")
        raise

    finally:
        searcher.close()
