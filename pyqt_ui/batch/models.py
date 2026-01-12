"""批量下载数据模型"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class MatchSource(Enum):
    """匹配来源"""

    AUTO = "auto"  # 自动匹配
    USER_SELECTED = "user_selected"  # 用户手动选择


@dataclass
class MatchCandidate:
    """单个匹配候选"""

    song_name: str
    singers: str
    album: str
    file_size: str
    duration: str
    source: str
    ext: str
    similarity_score: float  # 相似度分数
    song_info_obj: object  # 原始SongInfo对象

    def to_dict(self) -> dict:
        """转换为字典格式（兼容现有代码）"""
        return {
            "song_name": self.song_name,
            "singers": self.singers,
            "album": self.album,
            "file_size": self.file_size,
            "duration": self.duration,
            "source": self.source,
            "ext": self.ext,
            "similarity_score": self.similarity_score,
            "song_info_obj": self.song_info_obj,
        }


@dataclass
class BatchSongMatch:
    """单首歌的所有匹配结果"""

    query: Dict[str, str]  # 原始查询 {name, singer, original_line}
    current_match: Optional[MatchCandidate] = None  # 当前选中的匹配
    current_source: Optional[str] = None  # 当前匹配的源
    match_source_type: MatchSource = MatchSource.AUTO  # 匹配来源类型

    # 所有源的匹配结果：{source: [candidates]}
    all_matches: Dict[str, List[MatchCandidate]] = field(default_factory=dict)

    # 状态标记
    has_match: bool = False
    searched_sources: List[str] = field(default_factory=list)

    def get_current_match_dict(self) -> Optional[dict]:
        """获取当前匹配的字典格式"""
        if not self.current_match:
            return None
        return self.current_match.to_dict()

    def get_all_candidates_from_current_source(self) -> List[MatchCandidate]:
        """获取当前源的所有候选结果"""
        if not self.current_source:
            return []
        return self.all_matches.get(self.current_source, [])

    def get_all_candidates(self) -> List[MatchCandidate]:
        """获取所有源的所有候选结果（跨源）"""
        all_candidates = []
        for candidates in self.all_matches.values():
            all_candidates.extend(candidates)
        # 按相似度降序排序
        all_candidates.sort(key=lambda x: x.similarity_score, reverse=True)
        return all_candidates

    def switch_to_candidate(
        self,
        candidate: MatchCandidate,
        source_type: MatchSource = MatchSource.USER_SELECTED,
    ):
        """切换到指定候选结果"""
        self.current_match = candidate
        self.current_source = candidate.source
        self.match_source_type = source_type
        self.has_match = True


@dataclass
class BatchSearchResult:
    """批量搜索总结果"""

    total_songs: int
    matches: Dict[str, BatchSongMatch]  # {original_line: BatchSongMatch}
    search_time: float = 0.0  # 搜索耗时（秒）
    sources_searched: List[str] = field(default_factory=list)

    def get_match_count(self) -> int:
        """获取已匹配数量"""
        return sum(1 for match in self.matches.values() if match.has_match)

    def get_unmatched_songs(self) -> List[str]:
        """获取未匹配的歌曲"""
        return [line for line, match in self.matches.items() if not match.has_match]
