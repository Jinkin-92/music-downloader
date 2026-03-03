"""
歌单导入API端点

提供网易云音乐和QQ音乐歌单解析功能。
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging
import json
import asyncio

from core import BatchSongMatch, DEFAULT_SOURCES, SOURCE_LABELS, PlaylistParserFactory
from backend.workers.concurrent_search import AsyncConcurrentSearcher

logger = logging.getLogger(__name__)

# 中文源名到客户端名称的映射
SOURCE_NAME_MAP = {
    '网易云': 'NeteaseMusicClient',
    'QQ音乐': 'QQMusicClient',
    '酷狗': 'KugouMusicClient',
    '酷我': 'KuwoMusicClient',
}

def _map_source_names(sources: List[str]) -> List[str]:
    """
    将前端传递的中文名称映射为后端客户端名称

    Args:
        sources: 前端传递的源名称列表，可能包含中文

    Returns:
        映射后的客户端名称列表
    """
    mapped = []
    for source in sources:
        # 使用SOURCE_LABELS的反向映射查找
        for client_name, label in SOURCE_LABELS.items():
            if label == source:
                mapped.append(client_name)
                break
        else:
            # 如果源名称已经是客户端名称，直接使用
            mapped.append(source)
    return mapped

# 创建路由器
router = APIRouter(
    prefix='/api/playlist',
    tags=['歌单']
)


def _parse_duration_to_seconds(duration_str: str) -> int:
    """转换时长格式 "分:秒" 为秒数

    Args:
        duration_str: 时长字符串，格式如 "3:45" 或空字符串

    Returns:
        时长秒数
    """
    if not duration_str:
        return 0
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
    except (ValueError, IndexError):
        pass
    return 0


# ==================== Pydantic模型 ====================

class PlaylistParseRequest(BaseModel):
    """歌单解析请求"""
    url: str = Field(..., min_length=1, description='歌单URL')

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://music.163.com/#/playlist?id=3778678"
                }
            ]
        }
    }


class PlaylistSongResponse(BaseModel):
    """歌单歌曲响应"""
    name: str = Field(..., description='歌曲名称')
    artist: str = Field(..., description='歌手')
    album: str = Field(default='', description='专辑')
    duration: int = Field(default=0, description='时长（秒）')


class PlaylistParseResponse(BaseModel):
    """歌单解析响应"""
    success: bool = Field(..., description='是否成功')
    platform: str = Field(..., description='歌单平台')
    total: int = Field(..., description='歌曲总数')
    songs: List[PlaylistSongResponse] = Field(..., description='歌曲列表')
    error: Optional[str] = None


class PlaylistSongForSearch(BaseModel):
    """用于搜索的歌单歌曲"""
    name: str = Field(..., description='歌曲名称')
    artist: str = Field(..., description='歌手')
    album: str = Field(default='', description='专辑')


class PlaylistBatchSearchRequest(BaseModel):
    """歌单批量搜索请求"""
    songs: List[PlaylistSongForSearch] = Field(..., description='歌曲列表')
    sources: Optional[List[str]] = Field(default=None, description='音乐源列表')
    concurrency: int = Field(default=8, description='并发数')  # 优化为8，平衡性能与API限流


class MatchCandidate(BaseModel):
    """单个匹配候选"""
    song_name: str = Field(..., description='歌曲名称')
    singers: str = Field(..., description='歌手')
    album: str = Field(default='', description='专辑')
    size: str = Field(default='', description='文件大小')
    duration: str = Field(default='', description='时长')
    source: str = Field(..., description='音乐源')
    similarity: float = Field(default=0.0, description='相似度分数')


class BatchMatchInfoV2(BaseModel):
    """批量匹配信息V2"""
    query_name: str = Field(..., description='查询歌曲名称')
    query_singer: str = Field(..., description='查询歌手')
    current_match: Optional[MatchCandidate] = Field(default=None, description='当前最佳匹配')
    all_matches: Dict[str, List[MatchCandidate]] = Field(default_factory=dict, description='所有候选')
    has_match: bool = Field(default=False, description='是否有匹配')


class PlaylistBatchSearchResponse(BaseModel):
    """歌单批量搜索响应"""
    success: bool = Field(..., description='是否成功')
    total: int = Field(..., description='歌曲总数')
    matched: int = Field(..., description='已匹配数量')
    matches: List[BatchMatchInfoV2] = Field(..., description='匹配结果列表')
    error: Optional[str] = None


# ==================== API端点 ====================

@router.post('/parse', response_model=PlaylistParseResponse)
async def parse_playlist(request: PlaylistParseRequest):
    """
    解析歌单URL

    支持网易云音乐和QQ音乐歌单。

    Args:
        request: 歌单解析请求

    Returns:
        解析后的歌曲列表
    """
    from concurrent.futures import ThreadPoolExecutor
    import asyncio

    try:
        logger.info(f"[START] 解析歌单: {request.url[:100]}...")

        # 在线程池中运行同步解析，避免async/sync混合问题
        loop = asyncio.get_event_loop()
        songs = await loop.run_in_executor(
            None,  # 使用默认executor
            lambda: PlaylistParserFactory.parse_playlist(request.url)
        )

        logger.info(f"[SUCCESS] 解析到 {len(songs)} 首歌曲")

        platform = PlaylistParserFactory.get_supported_platforms()[0] if songs else '未知'

        # 转换为响应格式（限制前100首避免超时）
        song_responses = [
            PlaylistSongResponse(
                name=song.song_name,
                artist=song.singers,
                album=song.album or '',
                duration=_parse_duration_to_seconds(song.duration)
            )
            for song in songs[:100]
        ]

        logger.info(f"[COMPLETE] 解析完成: {len(song_responses)} 首歌曲 from {platform}")

        return PlaylistParseResponse(
            success=True,
            platform=platform,
            total=len(song_responses),
            songs=song_responses,
            error=None
        )

    except ValueError as e:
        logger.error(f"[ERROR] 歌单URL格式错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return PlaylistParseResponse(
            success=False,
            platform='',
            total=0,
            songs=[],
            error=str(e)
        )
    except Exception as e:
        logger.error(f"[ERROR] 歌单解析失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return PlaylistParseResponse(
            success=False,
            platform='',
            total=0,
            songs=[],
            error=f"解析失败: {str(e)}"
        )


@router.get('/platforms')
async def get_supported_platforms():
    """
    获取支持的歌单平台

    Returns:
        支持的平台列表
    """
    try:
        platforms = PlaylistParserFactory.get_supported_platforms()
        return {
            'success': True,
            'platforms': platforms
        }
    except Exception as e:
        logger.error(f"获取支持平台失败: {e}")
        return {
            'success': False,
            'platforms': [],
            'error': str(e)
        }


@router.post('/batch-search', response_model=PlaylistBatchSearchResponse)
async def batch_search_playlist(request: PlaylistBatchSearchRequest):
    """
    歌单批量搜索 - 返回完整候选列表

    Args:
        request: 批量搜索请求

    Returns:
        批量搜索结果（包含所有源的候选）
    """
    try:
        # 处理空列表情况
        if not request.songs or len(request.songs) == 0:
            logger.info("[DEBUG V2] 批量搜索：空歌曲列表")
            return PlaylistBatchSearchResponse(
                success=True,
                total=0,
                matched=0,
                matches=[],
                error=None
            )

        logger.info(f"[DEBUG V2] 批量搜索 {len(request.songs)} 首歌曲")

        # 1. 转换为批量文本格式
        def get_artist(s):
            # 打印调试信息
            logger.info(f"[DEBUG] Song type: {type(s)}, attributes: {dir(s)}")
            # Pydantic模型使用artist字段
            return getattr(s, 'artist', '') or getattr(s, 'singer', '')
        batch_text = '\n'.join([f"{s.name} - {get_artist(s)}" for s in request.songs])
        logger.info(f"[DEBUG V2] Batch text: {batch_text[:100]}...")

        # 2. 复用AsyncConcurrentSearcher，添加默认相似度阈值0.3（30%）提高匹配率
        similarity_threshold = 0.3  # 默认30%相似度阈值
        searcher = AsyncConcurrentSearcher(
            concurrency=request.concurrency,
            similarity_threshold=similarity_threshold
        )
        logger.info(f"[DEBUG V2] Created searcher with concurrency={request.concurrency}, similarity_threshold={similarity_threshold}")

        result = await searcher.search_batch(
            batch_text=batch_text,
            sources=request.sources or DEFAULT_SOURCES
        )
        logger.info(f"[DEBUG V2] Search completed. Result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

        # 3. 转换为V2响应格式
        matches_v2 = []
        logger.info(f"[DEBUG V2] Processing {len(result['matches'])} matches")

        for idx, (original_line, match_info) in enumerate(result['matches'].items()):
            logger.info(f"[DEBUG V2] Processing match {idx+1}: {original_line}")
            # 提取所有候选
            all_matches: Dict[str, List[MatchCandidate]] = {}

            for source, candidates in match_info.all_matches.items():
                all_matches[source] = [
                    MatchCandidate(
                        song_name=candidate.song_name,
                        singers=candidate.singers,
                        album=candidate.album or '',
                        size=candidate.file_size or '',
                        duration=candidate.duration or '',
                        source=candidate.source,
                        similarity=candidate.similarity_score
                    )
                    for candidate in candidates
                ]

            # 当前最佳匹配
            current_match = None
            if match_info.current_match:
                current_match = MatchCandidate(
                    song_name=match_info.current_match.song_name,
                    singers=match_info.current_match.singers,
                    album=match_info.current_match.album or '',
                    size=match_info.current_match.file_size or '',
                    duration=match_info.current_match.duration or '',
                    source=match_info.current_match.source,
                    similarity=match_info.current_match.similarity_score
                )

            batch_match_v2 = BatchMatchInfoV2(
                query_name=match_info.query.get('name', ''),
                query_singer=match_info.query.get('singer', ''),
                current_match=current_match,
                all_matches=all_matches,
                has_match=match_info.has_match
            )

            matches_v2.append(batch_match_v2)

        logger.info(f"批量搜索完成: {len(matches_v2)} 首歌曲，{result['matched']} 首匹配")

        return PlaylistBatchSearchResponse(
            success=True,
            total=len(matches_v2),
            matched=result['matched'],
            matches=matches_v2,
            error=None
        )

    except Exception as e:
        logger.error(f"批量搜索失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return PlaylistBatchSearchResponse(
            success=False,
            total=0,
            matched=0,
            matches=[],
            error=f"批量搜索失败: {str(e)}"
        )


@router.get('/batch-search-stream')
async def batch_search_stream(
    songs_json: str,
    sources: Optional[str] = None,
    concurrency: int = Query(default=8, description='并发数'),  # 优化为8，平衡性能与API限流
    similarity_threshold: Optional[float] = None
):
    """
    SSE流式批量搜索 - 实时推送搜索进度

    使用AsyncConcurrentSearcher实现真正的异步并发搜索。

    Args:
        songs_json: JSON字符串格式的歌曲列表
        sources: 逗号分隔的音乐源列表
        concurrency: 并发数
        similarity_threshold: 相似度阈值 (0.0-1.0)，默认0.6

    Returns:
        SSE流，实时推送搜索进度
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    # 解析参数
    try:
        songs_data = json.loads(songs_json)
        # 使用映射函数处理中文源名
        source_list = _map_source_names(sources.split(',')) if sources else DEFAULT_SOURCES
    except Exception as param_error:
        error_msg = str(param_error)
        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'error': f'参数解析失败: {error_msg}'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    def batch_match_to_dict(match) -> dict:
        """将BatchSongMatch转换为可JSON序列化的字典"""
        # 转换所有候选 - 使用 'similarity' 字段名以匹配前端类型定义
        all_matches_serializable = {}
        for source, candidates in match.all_matches.items():
            all_matches_serializable[source] = [
                {
                    'song_name': c.song_name,
                    'singers': c.singers,
                    'album': c.album,
                    'file_size': c.file_size,
                    'duration': c.duration,
                    'source': c.source,
                    'ext': c.ext,
                    'similarity': c.similarity_score,  # 使用 'similarity' 匹配前端接口
                    # 新增字段
                    'download_url': getattr(c, 'download_url', None),
                    'duration_s': getattr(c, 'duration_s', 0),
                    'name_similarity': c.name_similarity,
                    'singer_similarity': c.singer_similarity,
                    'album_similarity': c.album_similarity,
                    # 缓存ID（用于下载时获取SongInfo对象）
                    'song_id': getattr(c, 'song_id', None),
                }
                for c in candidates
            ]

        # 转换当前匹配 - 使用 'similarity' 字段名以匹配前端类型定义
        current_match_serializable = None
        if match.current_match:
            current_match_serializable = {
                'song_name': match.current_match.song_name,
                'singers': match.current_match.singers,
                'album': match.current_match.album,
                'file_size': match.current_match.file_size,
                'duration': match.current_match.duration,
                'source': match.current_match.source,
                'ext': match.current_match.ext,
                'similarity': match.current_match.similarity_score,  # 使用 'similarity' 匹配前端接口
                # 新增字段
                'download_url': getattr(match.current_match, 'download_url', None),
                'duration_s': getattr(match.current_match, 'duration_s', 0),
                'name_similarity': match.current_match.name_similarity,
                'singer_similarity': match.current_match.singer_similarity,
                'album_similarity': match.current_match.album_similarity,
                # 缓存ID（用于下载时获取SongInfo对象）
                'song_id': getattr(match.current_match, 'song_id', None),
            }

        return {
            'query': match.query,
            'current_match': current_match_serializable,
            'current_source': match.current_source,
            'all_matches': all_matches_serializable,
            'has_match': match.has_match,
        }

    async def progress_stream():
        """SSE进度流 - 使用AsyncConcurrentSearcher实现真正的异步搜索"""
        try:
            # 构建批量文本 - 兼容 'artist' 和 'singer' 两种键名
            batch_text = '\n'.join([f"{s['name']} - {(s.get('singer') or s.get('artist', ''))}" for s in songs_data])
            total_songs = len(songs_data)

            logger.info(f"[SSE] 开始批量搜索 {total_songs} 首歌曲")
            logger.info(f"[SSE] Batch text preview: {batch_text[:200]}...")

            # 发送开始事件
            yield f"event: start\ndata: {json.dumps({'total': total_songs})}\n\n"

            # 使用AsyncConcurrentSearcher进行异步并发搜索
            # 默认使用0.3阈值以提高匹配率
            searcher = AsyncConcurrentSearcher(
                concurrency=concurrency,
                similarity_threshold=similarity_threshold if similarity_threshold is not None else 0.3
            )
            logger.info(f"[SSE] Created searcher with concurrency={concurrency}, similarity_threshold={similarity_threshold if similarity_threshold is not None else 0.3}")

            # 分批搜索并实时发送进度
            from core import BatchParser
            parser = BatchParser()
            parsed_songs = parser.parse(batch_text)

            matches_dict = {}
            matched_count = 0

            # 使用外部信号量控制并发，实现真正的边搜索边发送进度
            # 关键：不要一次创建所有任务，而是动态创建任务
            logger.info(f"[SSE] 开始并发搜索 {total_songs} 首歌曲，使用外部信号量控制并发")

            # 创建外部信号量
            semaphore = asyncio.Semaphore(concurrency)

            async def search_with_semaphore(song, index):
                """使用信号量包装的单歌搜索"""
                async with semaphore:
                    logger.info(f"[SSE] 开始搜索歌曲 {index+1}/{total_songs}: {song.get('name', '')}")
                    batch_match = await searcher.search_single_song(song, source_list)
                    logger.info(f"[SSE] 完成搜索歌曲 {index+1}/{total_songs}: {song.get('name', '')}")
                    return index, batch_match

            completed_count = 0

            # 创建初始任务（最多并发数个）
            pending_songs = list(enumerate(parsed_songs))
            active_tasks = []

            # 启动第一批任务
            while len(active_tasks) < concurrency and pending_songs:
                idx, song = pending_songs.pop(0)
                task = asyncio.create_task(search_with_semaphore(song, idx))
                active_tasks.append((task, idx, song))

            logger.info(f"[SSE] 启动了 {len(active_tasks)} 个初始任务")

            # 处理完成的任务并启动新任务
            while active_tasks:
                # 等待任意一个任务完成
                done, _ = await asyncio.wait(
                    [task for task, _, _ in active_tasks],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # 移除已完成的任务
                for task in done:
                    # 找到对应的任务信息
                    task_info = None
                    for i, (t, idx, song) in enumerate(active_tasks):
                        if t == task:
                            task_info = (idx, song, i)
                            break

                    if task_info:
                        idx, song, pos = task_info
                        active_tasks.pop(pos)

                        try:
                            index, batch_match = await task

                            logger.info(f"[SSE] Processing result {index+1}: song={song}, batch_match type={type(batch_match)}")

                            if isinstance(batch_match, Exception):
                                logger.error(f"[SSE] 搜索歌曲 {song} 失败: {batch_match}")
                                batch_match = BatchSongMatch(
                                    query=song,
                                    all_matches={},
                                    has_match=False
                                )
                            elif batch_match is None:
                                logger.warning(f"[SSE] 搜索歌曲 {song} 返回None")
                                batch_match = BatchSongMatch(
                                    query=song,
                                    all_matches={},
                                    has_match=False
                                )

                            # 保存结果
                            singer = song.get('singer') or song.get('artist', '')
                            original_line = song.get('original_line', f"{song['name']} - {singer}")
                            matches_dict[original_line] = batch_match

                            if batch_match.has_match:
                                matched_count += 1

                            # 发送进度更新
                            progress = {
                                'completed': completed_count + 1,
                                'total': total_songs,
                                'percent': round((completed_count + 1) / total_songs * 100),
                                'song_name': song.get('name', ''),
                                'has_match': batch_match.has_match,
                            }
                            logger.info(f"[SSE] 进度: {progress['percent']}% - {progress['song_name']}")
                            yield f"event: progress\ndata: {json.dumps(progress)}\n\n"

                            completed_count += 1

                        except Exception as e:
                            logger.error(f"[SSE] 处理结果失败: {e}")
                            import traceback
                            logger.error(traceback.format_exc())

                        # 启动下一个待处理的任务
                        if pending_songs:
                            next_idx, next_song = pending_songs.pop(0)
                            next_task = asyncio.create_task(search_with_semaphore(next_song, next_idx))
                            active_tasks.append((next_task, next_idx, next_song))
                            logger.info(f"[SSE] 启动下一个任务 {next_idx+1}/{total_songs}: {next_song.get('name', '')}")

            # 转换matches_dict为可序列化的格式
            logger.info(f"[SSE] Before serialization: matched_count={matched_count}, total_songs={total_songs}")
            logger.info(f"[SSE] matches_dict keys: {list(matches_dict.keys())}")

            matches_serializable = {
                original_line: batch_match_to_dict(match)
                for original_line, match in matches_dict.items()
            }

            # 发送完成事件
            final_result = {
                'total': total_songs,
                'matched': matched_count,
                'matches': matches_serializable
            }
            logger.info(f"[SSE] Sending complete event: matched={matched_count}, total={total_songs}")
            logger.info(f"[SSE] Final result keys: {list(final_result.keys())}")
            logger.info(f"[SSE] Final matched value type: {type(final_result['matched'])}")
            yield f"event: complete\ndata: {json.dumps(final_result)}\n\n"

        except Exception as e:
            logger.error(f"[SSE] 批量搜索失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ==================== 后台任务搜索API ====================
# 这些端点支持后台运行，即使前端断开连接，搜索也会继续执行

from backend.api.task_manager import task_manager, TaskStatus


@router.post('/batch-search-start')
async def start_batch_search_background(request: PlaylistBatchSearchRequest):
    """
    启动后台批量搜索任务

    这是支持后台运行的新API。与SSE流式API不同，此API会立即返回task_id，
    搜索在后台独立执行。即使前端断开连接，搜索也会继续。

    使用流程：
    1. 调用此API获取task_id
    2. 使用 /batch-search-status/{task_id} 轮询查询进度
    3. 搜索完成后获取结果

    Args:
        request: 批量搜索请求

    Returns:
        {'task_id': str, 'status': 'started'}
    """
    try:
        # 解析参数
        songs_data = [s.model_dump() for s in request.songs]
        source_list = _map_source_names(request.sources) if request.sources else DEFAULT_SOURCES
        concurrency = request.concurrency or 8

        logger.info(f"[后台搜索] 启动批量搜索: {len(songs_data)} 首歌曲, 源: {source_list}")

        # 创建任务
        task_id = task_manager.create_task('search', {
            'songs': songs_data,
            'sources': source_list,
            'concurrency': concurrency
        }, total=len(songs_data))

        # 启动后台任务
        async def search_task():
            """后台搜索协程"""
            try:
                # 构建批量文本
                from core import BatchParser
                batch_text = '\n'.join([f"{s['name']} - {s.get('artist', '')}" for s in songs_data])
                parser = BatchParser()
                parsed_songs = parser.parse(batch_text)

                # 创建搜索器
                searcher = AsyncConcurrentSearcher(
                    concurrency=concurrency,
                    similarity_threshold=0.3
                )

                matches_dict = {}
                matched_count = 0

                # 逐个搜索
                for idx, song in enumerate(parsed_songs):
                    # 检查任务是否被取消
                    task = task_manager.get_task(task_id)
                    if task.status == TaskStatus.CANCELLED:
                        logger.info(f"[后台搜索] 任务已取消: {task_id}")
                        return

                    try:
                        # 搜索歌曲
                        batch_match = await searcher.search_single_song(song, source_list)

                        # 保存结果
                        singer = song.get('singer') or song.get('artist', '')
                        original_line = song.get('original_line', f"{song['name']} - {singer}")
                        matches_dict[original_line] = batch_match

                        if batch_match.has_match:
                            matched_count += 1

                        # 更新进度
                        task_manager.update_progress(
                            task_id,
                            idx + 1,
                            f"搜索完成: {song.get('name', '')}"
                        )

                    except Exception as e:
                        logger.error(f"[后台搜索] 搜索歌曲失败: {song}, 错误: {e}")

                # 转换结果为可序列化格式
                def batch_match_to_dict(match) -> dict:
                    all_matches_serializable = {}
                    for source, candidates in match.all_matches.items():
                        all_matches_serializable[source] = [
                            {
                                'song_name': c.song_name,
                                'singers': c.singers,
                                'album': c.album,
                                'file_size': c.file_size,
                                'duration': c.duration,
                                'source': c.source,
                                'ext': c.ext,
                                'similarity': c.similarity_score,
                                # 缓存ID（用于下载时获取SongInfo对象）
                                'song_id': getattr(c, 'song_id', None),
                            }
                            for c in candidates
                        ]

                    current_match_serializable = None
                    if match.current_match:
                        current_match_serializable = {
                            'song_name': match.current_match.song_name,
                            'singers': match.current_match.singers,
                            'album': match.current_match.album,
                            'file_size': match.current_match.file_size,
                            'duration': match.current_match.duration,
                            'source': match.current_match.source,
                            'ext': match.current_match.ext,
                            'similarity': match.current_match.similarity_score,
                            # 缓存ID（用于下载时获取SongInfo对象）
                            'song_id': getattr(match.current_match, 'song_id', None),
                        }

                    return {
                        'query': match.query,
                        'current_match': current_match_serializable,
                        'current_source': match.current_source,
                        'all_matches': all_matches_serializable,
                        'has_match': match.has_match,
                    }

                matches_serializable = {
                    original_line: batch_match_to_dict(match)
                    for original_line, match in matches_dict.items()
                }

                # 标记任务完成
                result = {
                    'total': len(songs_data),
                    'matched': matched_count,
                    'matches': matches_serializable
                }
                task_manager.complete_task(task_id, result)
                logger.info(f"[后台搜索] 任务完成: {task_id}, 匹配 {matched_count}/{len(songs_data)}")

            except Exception as e:
                logger.error(f"[后台搜索] 任务失败: {task_id}, 错误: {e}")
                import traceback
                logger.error(traceback.format_exc())
                task_manager.fail_task(task_id, str(e))

        task_manager.start_task(task_id, search_task(), task_name="批量搜索")

        return {
            'task_id': task_id,
            'status': 'started',
            'total': len(songs_data)
        }

    except Exception as e:
        logger.error(f"[后台搜索] 启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"启动搜索失败: {str(e)}")


@router.get('/batch-search-status/{task_id}')
async def get_batch_search_status(task_id: str):
    """
    查询后台搜索任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态信息
    """
    task_dict = task_manager.get_task_dict(task_id)

    if not task_dict:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    return task_dict


@router.delete('/batch-search-cancel/{task_id}')
async def cancel_batch_search(task_id: str):
    """
    取消后台搜索任务

    Args:
        task_id: 任务ID

    Returns:
        取消结果
    """
    success = task_manager.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"任务不存在或无法取消: {task_id}")

    return {
        'task_id': task_id,
        'status': 'cancelled'
    }
