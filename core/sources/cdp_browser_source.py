"""
CDP Browser Source - 通用浏览器音乐源

通过 anyclaw CDP 浏览器自动化访问需要 JavaScript 渲染的音乐网站。
支持：jgwav.cc, flmp3.pro, jcpoo.cn, tgws.cc 等。
"""

import json
import logging
import os
import re
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional

from core.sources.base import BaseMusicSource, SongInfo

logger = logging.getLogger(__name__)


# CDP Daemon 默认地址
DEFAULT_CDP_HOST = "localhost"
DEFAULT_CDP_PORT = 3456


def _cdp_request(path: str, host: str = DEFAULT_CDP_HOST, port: int = DEFAULT_CDP_PORT,
                  method: str = "GET", data: Optional[str] = None) -> Optional[str]:
    """向 CDP Daemon 发送请求"""
    import urllib.request
    import urllib.error

    url = f"http://{host}:{port}{path}"
    try:
        if method == "GET" and not data:
            req = urllib.request.Request(url)
        else:
            # 对于 eval 端点，使用 POST 发送脚本数据
            req = urllib.request.Request(url, data=data.encode() if data else None,
                                        method="POST" if data else "GET")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode('utf-8', errors='ignore')
    except (urllib.error.URLError, TimeoutError) as e:
        logger.error(f"CDP 请求失败: {path} - {e}")
        return None


def _cdp_ensure_daemon(host: str = DEFAULT_CDP_HOST, port: int = DEFAULT_CDP_PORT) -> bool:
    """确保 CDP Daemon 正在运行"""
    # 检查 daemon 状态
    response = _cdp_request("/targets", host, port)
    if response is not None:
        return True

    # 尝试启动 daemon
    try:
        result = subprocess.run(
            ["anyclaw", "daemon", "start"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # 等待 daemon 启动
            for _ in range(10):
                time.sleep(2)
                response = _cdp_request("/targets", host, port)
                if response is not None:
                    return True
        logger.warning(f"CDP Daemon 启动失败: {result.stderr}")
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"无法启动 anyclaw daemon: {e}")

    return False


class CdpBrowserSource(BaseMusicSource):
    r"""
    CDP 浏览器音乐源

    通过 anyclaw CDP 自动化访问 JS 渲染的音乐网站。

    配置示例:
        site_config = {
            "name": "jgwav",
            "display_name": "极光音乐",
            "base_url": "https://www.jgwav.cc",
            "search_url": "/search.html?key={keyword}",
            "search_script": (
                "Array.from(document.querySelectorAll('.song-item')).map(el => ({"
                "song_id: el.dataset.id || '',"
                "song_name: el.querySelector('.song-name')?.textContent?.trim() || '',"
                "singers: el.querySelector('.singer')?.textContent?.trim() || '',"
                "album: el.querySelector('.album')?.textContent?.trim() || '',"
                "}))"
            ),
            "detail_script": (
                "{download_url: document.querySelector('.download-btn')?.dataset.url || '',"
                "cover_url: document.querySelector('.cover-img')?.src || ''}"
            ),
        }
    """

    def __init__(self, site_config: Dict[str, Any]):
        """
        初始化 CDP 浏览器源

        Args:
            site_config: 网站配置字典，包含:
                - name: 内部名称
                - display_name: 显示名称
                - base_url: 基础 URL
                - search_url: 搜索页面 URL 模板
                - search_script: 提取搜索结果的 JS 表达式
                - detail_script: 提取详情的 JS 表达式
        """
        self._config = site_config
        self._cdp_host = site_config.get("cdp_host", DEFAULT_CDP_HOST)
        self._cdp_port = site_config.get("cdp_port", DEFAULT_CDP_PORT)
        self._enabled = True
        self._current_tab: Optional[str] = None

    @property
    def name(self) -> str:
        return self._config.get("name", "CdpBrowser")

    @property
    def display_name(self) -> str:
        return self._config.get("display_name", self.name)

    def is_available(self) -> bool:
        """检查源是否可用（CDP daemon 是否运行）"""
        if not self._enabled:
            return False
        return _cdp_ensure_daemon(self._cdp_host, self._cdp_port)

    def _get_or_create_tab(self) -> Optional[str]:
        """获取或创建浏览器标签页"""
        # 始终创建新标签以确保干净的上下文
        base_url = self._config.get("base_url", "")
        response = _cdp_request(
            f"/new?url={base_url}",
            self._cdp_host,
            self._cdp_port
        )
        if response:
            try:
                data = json.loads(response)
                self._current_tab = data.get("targetId") or data.get("id")
                return self._current_tab
            except json.JSONDecodeError:
                pass

        # 如果创建失败，尝试找一个已存在的标签
        response = _cdp_request("/targets", self._cdp_host, self._cdp_port)
        if response:
            try:
                targets = json.loads(response)
                for t in targets:
                    if t.get("type") == "page" and t.get("id"):
                        self._current_tab = t["id"]
                        return self._current_tab
            except json.JSONDecodeError:
                pass

        return None

    def _navigate_and_wait(self, url: str, timeout: int = 15) -> bool:
        """导航到 URL 并等待页面加载"""
        # 如果没有已有标签，创建新标签
        if not self._current_tab:
            self._current_tab = self._get_or_create_tab()

        tab_id = self._current_tab
        if not tab_id:
            logger.error(f"{self.name}: 无法创建标签页")
            return False

        # URL 编码
        import urllib.parse
        encoded_url = urllib.parse.quote(url, safe=':/?&=')

        # 导航
        response = _cdp_request(
            f"/navigate?target={tab_id}&url={encoded_url}",
            self._cdp_host,
            self._cdp_port
        )
        if not response:
            return False

        # 等待页面加载（简单等待，实际可用更智能的检测）
        time.sleep(timeout)
        return True

    def _eval_js(self, script: str) -> Optional[Any]:
        """在当前标签页执行 JS 并返回结果"""
        if not self._current_tab:
            return None

        # 使用 POST 发送脚本数据
        response = _cdp_request(
            f"/eval?target={self._current_tab}",
            self._cdp_host,
            self._cdp_port,
            method="POST",
            data=script
        )

        if response:
            try:
                data = json.loads(response)
                return data.get("result") or data.get("value")
            except json.JSONDecodeError:
                return None
        return None

    def search(self, keyword: str, limit: int = 20) -> List[SongInfo]:
        """搜索歌曲"""
        if not self.is_available():
            logger.warning(f"{self.name}: CDP 源不可用")
            return []

        logger.info(f"{self.name}: 搜索 '{keyword}'")

        try:
            # 构建搜索 URL
            import urllib.parse
            base_url = self._config.get("base_url", "")
            search_path = self._config.get("search_url", "/search?q={keyword}")
            # 先对关键词进行 URL 编码
            encoded_keyword = urllib.parse.quote(keyword, safe='')
            search_url = search_path.format(keyword=encoded_keyword)
            if not search_url.startswith(("http://", "https://")):
                search_url = base_url + search_url

            # 导航并等待
            if not self._navigate_and_wait(search_url):
                return []

            # 执行提取脚本
            search_script = self._config.get("search_script", "")
            if not search_script:
                logger.error(f"{self.name}: 未配置 search_script")
                return []

            result = self._eval_js(search_script)
            if not result or not isinstance(result, list):
                logger.warning(f"{self.name}: 搜索结果为空或格式错误")
                return []

            # 解析结果
            songs = []
            for item in result[:limit]:
                if isinstance(item, dict):
                    songs.append(SongInfo(
                        song_name=item.get("song_name", ""),
                        singers=item.get("singers", ""),
                        album=item.get("album", ""),
                        song_id=item.get("song_id", ""),
                        cover_url=item.get("cover_url", ""),
                        source=self.name,
                    ))

            logger.info(f"{self.name}: 成功解析 {len(songs)} 首歌曲")
            return songs

        except Exception as e:
            logger.error(f"{self.name}: 搜索失败 - {e}")
            return []

    def get_detail(self, song_id: str) -> Optional[SongInfo]:
        """获取歌曲详情"""
        if not self.is_available() or not song_id:
            return None

        logger.info(f"{self.name}: 获取歌曲详情 ID={song_id}")

        try:
            # 构建详情 URL
            base_url = self._config.get("base_url", "")
            detail_path = self._config.get("detail_url", "/song/{id}")
            detail_url = detail_path.format(id=song_id)
            if not detail_url.startswith(("http://", "https://")):
                detail_url = base_url + detail_url

            # 导航并等待
            if not self._navigate_and_wait(detail_url):
                return None

            # 执行提取脚本
            detail_script = self._config.get("detail_script", "")
            if not detail_script:
                logger.error(f"{self.name}: 未配置 detail_script")
                return None

            result = self._eval_js(detail_script)
            if not result or not isinstance(result, dict):
                return None

            return SongInfo(
                song_id=song_id,
                download_url=result.get("download_url"),
                cover_url=result.get("cover_url"),
                source=self.name,
            )

        except Exception as e:
            logger.error(f"{self.name}: 获取详情失败 - {e}")
            return None

    def download(self, song_id: str, save_path: str) -> bool:
        """
        下载歌曲

        注意：CDP 浏览器源可能不直接支持下载，通常需要先获取下载链接，
        然后使用其他方式下载文件。
        """
        logger.warning(f"{self.name}: CDP 源不支持直接下载，请使用 get_detail 获取下载链接")
        return False

    def close_tab(self):
        """关闭当前标签页"""
        if self._current_tab:
            try:
                _cdp_request(
                    f"/close?target={self._current_tab}",
                    self._cdp_host,
                    self._cdp_port
                )
            except Exception:
                pass
            self._current_tab = None


# 预配置的网站源
CDP_SITE_CONFIGS = {
    "jgwav": {
        "name": "jgwav",
        "display_name": "极光音乐",
        "base_url": "https://www.jgwav.cc",
        "search_url": "/search.html?key={keyword}",
        "search_script": (
            "Array.from(document.querySelectorAll('li')).filter(el => el.querySelector('a[href*=\"/detail/\"]')).map(el => ({"
            "song_id: el.querySelector('a[href*=\"/detail/\"]')?.href?.match(/\\/detail\\/(\\d+)/)?.[1] || '',"
            "song_name: el.querySelector('h2 a')?.title?.replace('免费下载', '').trim() || '',"
            "singers: (() => { const ems = el.querySelectorAll('em'); return ems.length > 1 ? ems[1]?.textContent?.replace('演唱：', '').trim() : ''; })(),"
            "album: '',"
            "})).filter(s => s.song_name)"
        ),
    },
    "flmp3": {
        "name": "flmp3",
        "display_name": "FLMP3",
        "base_url": "https://www.flmp3.pro",
        "search_url": "/search.html?keyword={keyword}",
        "search_script": (
            "Array.from(document.querySelectorAll('a[href*=\"/song/\"]')).filter(a => a.href.match(/\\/song\\/\\d+/)).map(el => ({"
            "song_id: el.href?.match(/\\/song\\/(\\d+)/)?.[1] || '',"
            "song_name: el.innerText?.split('\\n')[0]?.trim() || '',"
            "singers: (() => { const parts = el.innerText?.split('\\n')?.filter(p => p.trim()); return parts?.length > 1 ? parts[1]?.trim() : ''; })(),"
            "album: '',"
            "})).filter(s => s.song_name)"
        ),
    },
    "tgws": {
        "name": "tgws",
        "display_name": "糖果无损音乐",
        "base_url": "https://www.tgws.cc",
        "search_url": "/search?name={keyword}",
        "search_script": (
            "Array.from(document.querySelectorAll('li')).filter(el => el.querySelector('a[href*=\"/musicInfo/\"]')).map(el => ({"
            "song_id: el.querySelector('a[href*=\"/musicInfo/\"]')?.href?.match(/\\/musicInfo\\/(\\d+)/)?.[1] || '',"
            "song_name: (() => { const m = el.querySelector('a')?.title?.match(/(.+?) -/); return m ? m[1]?.trim() : el.querySelector('a')?.title?.split(' -')[0]?.replace('无损下载', '').trim() || ''; })(),"
            "singers: (() => { const m = el.querySelector('a')?.title?.match(/ - (.+?) /); return m ? m[1]?.trim() : ''; })(),"
            "album: '',"
            "})).filter(s => s.song_name)"
        ),
    },
    "jcpoo": {
        "name": "jcpoo",
        "display_name": "JCPOO音乐",
        "base_url": "https://www.jcpoo.cn",
        "search_url": "/search?keyword={keyword}",
        "search_script": (
            "Array.from(document.querySelectorAll('a[href*=\"/music/info.html\"]')).filter(a => a.href.includes('id=MUSIC_')).map(el => ({"
            "song_id: el.href?.match(/id=MUSIC_(\\d+)/)?.[1] || '',"
            "song_name: (() => { const m = el.innerText?.match(/《(.+?)》/); return m ? m[1] : el.innerText?.split(' ')[0]?.trim() || ''; })(),"
            "singers: (() => { const m = el.innerText?.match(/(.+?)《/); return m ? m[1]?.trim() : ''; })(),"
            "album: '',"
            "})).filter(s => s.song_name && s.song_name !== '')"
        ),
    },
}


def create_cdp_source(site_name: str) -> Optional[CdpBrowserSource]:
    """根据网站名称创建 CDP 源"""
    config = CDP_SITE_CONFIGS.get(site_name)
    if config:
        return CdpBrowserSource(config)
    return None


def get_all_cdp_sources() -> List[CdpBrowserSource]:
    """获取所有预配置的 CDP 源"""
    return [CdpBrowserSource(config) for config in CDP_SITE_CONFIGS.values()]
