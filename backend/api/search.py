"""
搜索API端点

提供单曲搜索和批量搜索功能，使用asyncio实现高性能并发。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from core import MusicDownloader, DEFAULT_SOURCES, SOURCE_LABELS
from backend.workers.concurrent_search import AsyncConcurrentSearcher

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix='/api/search',
    tags=['搜索']
)

# 全局单例
music_downloader = MusicDownloader()


# ==================== Pydantic模型 ====================

class SourceResponse(BaseModel):
    """音乐源响应"""
    value: str = Field(..., description='源代码')
    label: str = Field(..., description='源显示名称')


class SourcesListResponse(BaseModel):
    """音乐源列表响应"""
    sources: List[SourceResponse]


class SearchRequest(BaseModel):
    """单曲搜索请求"""
    keyword: str = Field(..., min_length=1, description='搜索关键词')
    sources: Optional[List[str]] = Field(
        default=None,
        description='指定的音乐源列表（None=全部）'
    )
    max_results: int = Field(
        default=20,
        ge=1,
        le=100,
        description='每个源最大结果数'
    )


class SongInfo(BaseModel):
    """歌曲信息"""
    song_name: str = Field(..., description='歌曲名称')
    singers: str = Field(..., description='歌手')
    album: str = Field(..., description='专辑')
    size: str = Field(..., description='文件大小')
    duration: str = Field(..., description='时长')
    source: str = Field(..., description='音乐源')


class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool = Field(..., description='是否成功')
    keyword: str = Field(..., description='搜索关键词')
    total: int = Field(..., description='总结果数')
    songs: List[SongInfo] = Field(..., description='歌曲列表')


class BatchSearchRequest(BaseModel):
    """批量搜索请求"""
    text: str = Field(..., min_length=1, description='批量文本，每行一首歌')
    sources: Optional[List[str]] = Field(
        default=None,
        description='音乐源列表（None=全部）'
    )
    concurrency: int = Field(
        default=5,
        ge=1,
        le=10,
        description='并发搜索数量'
    )


class BatchMatchInfo(BaseModel):
    """批量匹配信息"""
    query_name: str = Field(..., description='查询歌名')
    query_singer: str = Field(..., description='查询歌手')
    song_name: str = Field(..., description='匹配的歌名')
    singers: str = Field(..., description='匹配的歌手')
    album: str = Field(..., description='专辑')
    size: str = Field(..., description='文件大小')
    duration: str = Field(..., description='时长')
    source: str = Field(..., description='音乐源')
    similarity: float = Field(..., description='相似度分数')
    has_candidates: bool = Field(..., description='是否有其他候选')
    # 新增字段
    download_url: Optional[str] = Field(None, description='直接下载URL')
    duration_s: Optional[int] = Field(None, description='时长（秒）')
    ext: Optional[str] = Field(None, description='文件扩展名')
    name_similarity: Optional[float] = Field(None, description='歌名相似度')
    singer_similarity: Optional[float] = Field(None, description='歌手相似度')
    album_similarity: Optional[float] = Field(None, description='专辑相似度')
    all_candidates: Optional[List[dict]] = Field(None, description='所有候选结果（全局排序）')


class BatchSearchResponse(BaseModel):
    """批量搜索响应"""
    success: bool = Field(..., description='是否成功')
    total: int = Field(..., description='总歌曲数')
    matched: int = Field(..., description='匹配成功数')
    matches: List[BatchMatchInfo] = Field(..., description='匹配结果列表')


# ==================== API端点 ====================

@router.get('/sources', response_model=SourcesListResponse)
async def get_sources():
    """
    获取支持的音乐源

    Returns:
        所有支持的音乐源列表
    """
    try:
        sources = [
            SourceResponse(
                value=source,
                label=SOURCE_LABELS.get(source, source)
            )
            for source in DEFAULT_SOURCES
        ]

        return SourcesListResponse(sources=sources)

    except Exception as e:
        logger.error(f"获取音乐源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/', response_model=SearchResponse)
async def search_music(request: SearchRequest):
    """
    单曲搜索

    并发搜索所有指定音乐源，返回合并结果。

    Args:
        request: 搜索请求

    Returns:
        搜索结果列表
    """
    try:
        sources = request.sources or DEFAULT_SOURCES
        logger.info(
            f"单曲搜索: keyword='{request.keyword}', "
            f"sources={sources}"
        )

        # 使用现有的MusicDownloader搜索
        results = music_downloader.search(
            keyword=request.keyword,
            sources=sources
        )

        # 转换为响应格式
        songs_list = []
        for source, songs in results.items():
            for song in songs:
                # song已经是字典格式
                songs_list.append(SongInfo(
                    song_name=song.get('song_name', ''),
                    singers=song.get('singers', ''),
                    album=song.get('album', ''),
                    size=song.get('file_size', ''),
                    duration=song.get('duration', ''),
                    source=song.get('source', source)
                ))

        logger.info(f"搜索完成: 共找到 {len(songs_list)} 首歌曲")

        return SearchResponse(
            success=True,
            keyword=request.keyword,
            total=len(songs_list),
            songs=songs_list
        )

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/batch', response_model=BatchSearchResponse)
async def batch_search(request: BatchSearchRequest):
    """
    批量搜索

    解析批量文本，使用AsyncConcurrentSearcher并发搜索所有歌曲。

    Args:
        request: 批量搜索请求

    Returns:
        批量匹配结果
    """
    try:
        sources = request.sources or DEFAULT_SOURCES
        logger.info(
            f"批量搜索: {len(request.text.splitlines())} 行, "
            f"sources={sources}, concurrency={request.concurrency}"
        )

        # 创建异步搜索器，添加默认相似度阈值0.3（30%）提高匹配率
        similarity_threshold = 0.3  # 默认30%相似度阈值
        searcher = AsyncConcurrentSearcher(
            concurrency=request.concurrency,
            similarity_threshold=similarity_threshold
        )

        # 执行批量搜索
        import asyncio
        result = await searcher.search_batch(
            batch_text=request.text,
            sources=sources
        )

        # 转换为响应格式
        matches_list = []
        for original_line, batch_match in result['matches'].items():
            if batch_match.current_match:
                match_dict = batch_match.current_match
                # 获取全局排序的所有候选
                all_candidates = batch_match.get_all_candidates()
                # 构建全局排序的候选列表
                all_candidates_list = [
                    {
                        'song_name': c.song_name,
                        'singers': c.singers,
                        'album': c.album,
                        'file_size': c.file_size,
                        'duration': c.duration,
                        'source': c.source,
                        'ext': c.ext,
                        'similarity': c.similarity_score,
                        'download_url': getattr(c, 'download_url', None),
                        'duration_s': getattr(c, 'duration_s', None),
                        'name_similarity': c.name_similarity,
                        'singer_similarity': c.singer_similarity,
                        'album_similarity': c.album_similarity,
                    }
                    for c in all_candidates
                ]

                matches_list.append(BatchMatchInfo(
                    query_name=batch_match.query.get('name', ''),
                    query_singer=batch_match.query.get('singer', ''),
                    song_name=match_dict.song_name,
                    singers=match_dict.singers,
                    album=match_dict.album,
                    size=match_dict.file_size,
                    duration=match_dict.duration,
                    source=match_dict.source,
                    similarity=match_dict.similarity_score,
                    has_candidates=len(all_candidates_list) > 1,
                    # 新增字段
                    download_url=getattr(match_dict, 'download_url', None),
                    duration_s=getattr(match_dict, 'duration_s', None),
                    ext=match_dict.ext,
                    name_similarity=match_dict.name_similarity,
                    singer_similarity=match_dict.singer_similarity,
                    album_similarity=match_dict.album_similarity,
                    all_candidates=all_candidates_list if all_candidates_list else None
                ))
            else:
                # 无匹配结果
                matches_list.append(BatchMatchInfo(
                    query_name=batch_match.query.get('name', ''),
                    query_singer=batch_match.query.get('singer', ''),
                    song_name='',
                    singers='',
                    album='',
                    size='',
                    duration='',
                    source='',
                    similarity=0.0,
                    has_candidates=False
                ))

        logger.info(
            f"批量搜索完成: {result['matched']}/{result['total']} 匹配"
        )

        return BatchSearchResponse(
            success=True,
            total=result['total'],
            matched=result['matched'],
            matches=matches_list
        )

    except Exception as e:
        logger.error(f"批量搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
