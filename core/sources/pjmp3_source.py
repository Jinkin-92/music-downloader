"""
pjmp3 Source - pjmp3.com 音乐源实现

基于 HTTP API 的直链音乐源，提供稳定的搜索和下载功能。
"""

import logging
import os
import re
from typing import List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.sources.base import BaseMusicSource, SongInfo

logger = logging.getLogger(__name__)


def _clean_string(s: str) -> str:
    """清理字符串中的无效Unicode字符和Python unicode转义序列"""
    if not s:
        return s
    try:
        # Step 1: 解码 Python unicode 转义序列 \uXXXX
        # pjmp3.com 返回的 HTML 中包含字面 \u5468\u6770\u4f26 形式的转义
        s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)

        # Step 2: 清理无效的 surrogate 字符
        # 修复字符串中任何残留的孤立 surrogate
        try:
            # surrogatepass 允许编码孤立 surrogates
            b = s.encode('utf-8', errors='surrogatepass')
            # 过滤掉 UTF-8 编码中 0xD8-0xDF 范围内的前导字节
            b = bytes(c for c in b if c < 0xD8 or c > 0xDF)
            return b.decode('utf-8', errors='ignore')
        except UnicodeEncodeError:
            # 如果编码失败，使用更安全的方式清理
            return ''.join(c for c in s if not (0xD800 <= ord(c) <= 0xDFFF))
    except:
        return s


def _env_int(name: str, default: int) -> int:
    """从环境变量获取整数配置"""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid integer for %s: %s, using %s", name, value, default)
        return default


class Pjmp3Source(BaseMusicSource):
    """
    pjmp3.com 音乐源

    特点：
    - 直链下载，稳定性高
    - 支持歌曲搜索和详情获取
    - 需要处理反爬机制
    """

    BASE_URL = "https://pjmp3.com"
    SEARCH_URL = "/search.php"
    SONG_URL = "/song.php"

    def __init__(self):
        self._enabled = True
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })

        retry_total = _env_int('PJMP3_RETRY_TOTAL', 4)
        retry = Retry(
            total=retry_total,
            connect=retry_total,
            read=retry_total,
            status=retry_total,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @property
    def name(self) -> str:
        return "Pjmp3Client"

    @property
    def display_name(self) -> str:
        return "PJMP3"

    def is_available(self) -> bool:
        """检查是否可用"""
        return self._enabled

    def search(self, keyword: str, limit: int = 20) -> List[SongInfo]:
        """搜索歌曲"""
        if not self._enabled or not keyword or not keyword.strip():
            return []

        logger.info(f"Pjmp3Source: 搜索 '{keyword}'")

        try:
            from urllib.parse import urljoin
            params = {"keyword": keyword.strip()}
            url = urljoin(self.BASE_URL, self.SEARCH_URL)
            response = self.session.get(url, params=params, timeout=(20, 60))
            response.raise_for_status()
            # 让 BeautifulSoup 自动检测编码

            return self._parse_search_results(response.text, limit)

        except Exception as e:
            logger.error(f"Pjmp3Source: 搜索失败 - {e}")
            return []

    def _parse_search_results(self, html: str, limit: int) -> List[SongInfo]:
        """解析搜索结果HTML"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            results = []
            song_items = soup.find_all('a', href=re.compile(r'song\.php\?id=\d+'))

            for item in song_items[:limit]:
                try:
                    song_info = self._parse_song_item(item)
                    if song_info:
                        results.append(song_info)
                except Exception as e:
                    logger.error(f"Pjmp3Source: 解析失败 - {e}")
                    continue

            logger.info(f"Pjmp3Source: 成功解析 {len(results)} 首歌曲")
            return results

        except ImportError:
            logger.error("Pjmp3Source: beautifulsoup4 未安装")
            self._enabled = False
            return []

    def _parse_song_item(self, item) -> Optional[SongInfo]:
        """解析搜索结果中的歌曲项"""
        try:
            href = item.get('href', '')
            song_id_match = re.search(r'id=(\d+)', href)
            if not song_id_match:
                return None
            song_id = song_id_match.group(1)

            song_name = "未知"
            singers = "未知"

            # 尝试查找歌名和歌手
            song_name_elem = item.find('div', class_=re.compile('song', re.I))
            if song_name_elem:
                song_name = _clean_string(song_name_elem.get_text(strip=True))

            singer_elem = item.find('div', class_=re.compile('singer', re.I))
            if singer_elem:
                singers = _clean_string(singer_elem.get_text(strip=True))

            # 如果没找到，尝试从所有子元素提取
            if song_name == "未知":
                all_texts = [_clean_string(t.strip()) for t in item.stripped_strings if t.strip()]
                all_texts = [t for t in all_texts if not (len(t) == 1 and ord(t[0]) > 0xF000)]
                if len(all_texts) >= 2:
                    song_name = all_texts[0]
                    singers = all_texts[1]

            cover_url = ""
            img = item.find('img')
            if img:
                cover_url = img.get('src', '')

            return SongInfo(
                song_name=song_name,
                singers=singers,
                album="",
                song_id=song_id,
                cover_url=cover_url,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Pjmp3Source: 解析歌曲项失败 - {e}")
            return None

    def get_detail(self, song_id: str) -> Optional[SongInfo]:
        """获取歌曲详情（包含下载链接）"""
        if not self._enabled or not song_id:
            return None

        logger.info(f"Pjmp3Source: 获取歌曲详情 ID={song_id}")

        try:
            from urllib.parse import urljoin
            url = urljoin(self.BASE_URL, f"{self.SONG_URL}?id={song_id}")
            response = self.session.get(url, timeout=(20, 60))
            response.raise_for_status()
            response.encoding = 'utf-8'

            return self._parse_song_detail(response.text, song_id)

        except Exception as e:
            logger.error(f"Pjmp3Source: 获取歌曲详情失败 - {e}")
            return None

    def _parse_song_detail(self, html: str, song_id: str) -> Optional[SongInfo]:
        """解析歌曲详情HTML"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            song_name = ""
            singers = ""
            album = ""
            duration = ""
            cover_url = ""
            preview_url = None

            # 歌名
            title_elem = soup.find('div', class_='song-title')
            if title_elem:
                song_name = _clean_string(title_elem.get_text(strip=True))

            # 歌手和专辑
            subtitle_elem = soup.find('div', class_='song-subtitle')
            if subtitle_elem:
                subtitle_text = _clean_string(subtitle_elem.get_text(strip=True))
                parts = subtitle_text.split()
                if len(parts) >= 1:
                    singers = parts[0]
                if len(parts) >= 2:
                    album = ' '.join(parts[1:])

            # 时长
            text_elem = soup.find('div', class_='song-text')
            if text_elem:
                text = text_elem.get_text(strip=True)
                duration_match = re.search(r'(\d{1,2}:\d{2})', text)
                if duration_match:
                    duration = duration_match.group(1)

            # 封面
            cover_elem = soup.find('div', class_='song-cover')
            if cover_elem:
                style = cover_elem.get('style', '')
                url_match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if url_match:
                    cover_url = url_match.group(1)

            # 提取试听URL（从APlayer配置）
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_text = script.string if script.string else ""
                if 'APlayer' in script_text and 'url:' in script_text:
                    url_match = re.search(r'url:\s*["\'](.*?)["\']', script_text)
                    if url_match:
                        preview_url = url_match.group(1)
                        break

            # 计算时长（秒）
            duration_s = 0
            if duration:
                try:
                    parts = duration.split(':')
                    if len(parts) == 2:
                        duration_s = int(parts[0]) * 60 + int(parts[1])
                except:
                    pass

            return SongInfo(
                song_name=song_name,
                singers=singers,
                album=album,
                duration=duration,
                duration_s=duration_s,
                song_id=song_id,
                cover_url=cover_url,
                download_url=preview_url,
                preview_url=preview_url,
                source=self.name,
            )

        except ImportError:
            logger.error("Pjmp3Source: beautifulsoup4 未安装")
            self._enabled = False
            return None

    def download(self, song_id: str, save_path: str) -> bool:
        """
        下载歌曲到指定路径

        Args:
            song_id: 歌曲ID（也可能是download_url）
            save_path: 保存路径

        Returns:
            下载是否成功
        """
        download_url = None

        # 如果song_id是URL，直接使用；否则获取详情
        if song_id.startswith('http'):
            download_url = song_id
            logger.info(f"Pjmp3Source: 使用直接URL下载")
        else:
            # 先获取详情获取下载链接
            song_info = self.get_detail(song_id)
            if not song_info or not song_info.download_url:
                logger.error(f"Pjmp3Source: 无法获取下载链接 ID={song_id}")
                return False
            download_url = song_info.download_url

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://pjmp3.com/",
                "Accept": "*/*",
            }

            logger.info(f"Pjmp3Source: 开始下载")

            response = requests.get(
                download_url,
                headers=headers,
                timeout=60,
                stream=True
            )
            response.raise_for_status()

            os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Pjmp3Source: 下载完成 {save_path}")
            return True

        except Exception as e:
            logger.error(f"Pjmp3Source: 下载失败 - {e}")
            return False


# 全局源实例
_pjmp3_source: Optional[Pjmp3Source] = None


def get_pjmp3_source() -> Pjmp3Source:
    """获取 Pjmp3Source 单例"""
    global _pjmp3_source
    if _pjmp3_source is None:
        _pjmp3_source = Pjmp3Source()
    return _pjmp3_source
