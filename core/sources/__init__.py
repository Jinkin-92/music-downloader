"""
Music Sources - 统一音乐源接口

提供抽象基类和具体实现，支持多源音乐搜索和下载。
"""

from core.sources.base import (
    BaseMusicSource,
    SongInfo,
)

# 导入所有源实现
from core.sources.pjmp3_source import Pjmp3Source, get_pjmp3_source
from core.sources.cdp_browser_source import (
    CdpBrowserSource,
    CDP_SITE_CONFIGS,
    create_cdp_source,
    get_all_cdp_sources,
)

__all__ = [
    # 基类
    "BaseMusicSource",
    "SongInfo",
    # pjmp3 源
    "Pjmp3Source",
    "get_pjmp3_source",
    # CDP 浏览器源
    "CdpBrowserSource",
    "CDP_SITE_CONFIGS",
    "create_cdp_source",
    "get_all_cdp_sources",
]
