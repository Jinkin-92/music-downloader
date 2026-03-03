"""
批量下载API端点

提供批量文本解析、匹配等功能。
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from core import BatchParser, SongMatcher, MusicDownloader
# Celery tasks disabled for testing
# from backend.workers.download import batch_search_task

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix='/api/batch',
    tags=['批量']
)

# 全局单例
music_downloader = MusicDownloader()


# ==================== Pydantic模型 ====================

class BatchParseRequest(BaseModel):
    """批量解析请求"""
    text: str = Field(..., min_length=1, description='批量文本')


class ParsedSong(BaseModel):
    """解析后的歌曲"""
    name: str = Field(..., description='歌曲名称')
    singer: str = Field(..., description='歌手')
    album: str = Field(default='', description='专辑')


class BatchParseResponse(BaseModel):
    """批量解析响应"""
    success: bool = Field(..., description='是否成功')
    total: int = Field(..., description='总歌曲数')
    songs: List[ParsedSong] = Field(..., description='解析的歌曲列表')


class BatchMatchRequest(BaseModel):
    """批量匹配请求"""
    songs: List[ParsedSong] = Field(..., description='歌曲列表')
    sources: Optional[List[str]] = Field(
        default=None,
        description='音乐源列表'
    )


class MatchedSong(BaseModel):
    """匹配后的歌曲"""
    name: str = Field(..., description='歌曲名称')
    singer: str = Field(..., description='歌手')
    album: str = Field(..., description='专辑')
    size: str = Field(..., description='文件大小')
    duration: str = Field(..., description='时长')
    source: str = Field(..., description='音乐源')
    similarity: float = Field(..., description='相似度')


class BatchMatchResponse(BaseModel):
    """批量匹配响应"""
    success: bool = Field(..., description='是否成功')
    total: int = Field(..., description='总歌曲数')
    results: List[MatchedSong] = Field(..., description='匹配结果')


# ==================== API端点 ====================

@router.post('/parse', response_model=BatchParseResponse)
async def parse_batch_text(request: BatchParseRequest):
    """
    解析批量文本

    将多行文本解析为歌曲列表，格式："歌名 - 歌手"

    Args:
        request: 批量文本

    Returns:
        解析后的歌曲列表
    """
    try:
        logger.info(f"批量解析: {len(request.text.splitlines())} 行")

        # 使用BatchParser解析
        parser = BatchParser()
        songs = parser.parse(request.text)

        # 转换为响应格式
        parsed_songs = [
            ParsedSong(
                name=song['name'],
                singer=song['singer'],
                album=song.get('album', '')
            )
            for song in songs
        ]

        logger.info(f"解析完成: {len(parsed_songs)} 首歌曲")

        return BatchParseResponse(
            success=True,
            total=len(parsed_songs),
            songs=parsed_songs
        )

    except Exception as e:
        logger.error(f"批量解析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/match', response_model=BatchMatchResponse)
async def batch_match(request: BatchMatchRequest):
    """
    批量匹配

    为每首歌搜索并匹配最佳结果。

    Args:
        request: 批量匹配请求

    Returns:
        匹配结果列表
    """
    try:
        sources = request.sources or ['QQMusicClient', 'NeteaseMusicClient']
        logger.info(f"批量匹配: {len(request.songs)} 首歌曲, sources={sources}")

        results = []
        for song_info in request.songs:
            # 搜索
            search_results = music_downloader.search(
                keyword=f"{song_info.name} {song_info.singer}",
                sources=sources
            )

            # 合并所有结果
            all_results = []
            for source, songs in search_results.items():
                all_results.extend(songs)

            # 匹配最佳结果
            best_match = SongMatcher.find_best_match(
                {
                    'name': song_info.name,
                    'singer': song_info.singer,
                    'album': song_info.album
                },
                all_results
            )

            if best_match:
                results.append(MatchedSong(
                    name=best_match.get('song_name', ''),
                    singer=best_match.get('singers', ''),
                    album=best_match.get('album', ''),
                    size=best_match.get('file_size', ''),
                    duration=best_match.get('duration', ''),
                    source=best_match.get('source', ''),
                    similarity=0.0  # TODO: 计算相似度
                ))
            else:
                # 无匹配结果
                results.append(MatchedSong(
                    name=song_info.name,
                    singer=song_info.singer,
                    album='',
                    size='',
                    duration='',
                    source='',
                    similarity=0.0
                ))

        logger.info(f"批量匹配完成: {len(results)} 首歌曲")

        return BatchMatchResponse(
            success=True,
            total=len(results),
            results=results
        )

    except Exception as e:
        logger.error(f"批量匹配失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
