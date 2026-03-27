"""
pjmp3.com Music Client Adapter

提供 pjmp3.com 网站的网页抓取功能，作为备用音乐源。

网站结构：
- 搜索: GET /search.php?keyword={keyword}
- 歌曲详情: GET /song.php?id={songId}
- 下载链接: 通过页面中的 APlayer 配置获取

注意：
- 使用网页抓取而非官方 API
- 需要处理反爬虫机制（User-Agent、延迟等）
- 下载链接需要 Referer 头
"""

import re
import time
import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, quote

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logging.warning("beautifulsoup4 not installed, pjmp3 client will not work")

logger = logging.getLogger(__name__)


@dataclass
class Pjmp3SongInfo:
    """pjmp3 歌曲信息（兼容 SongInfo 接口）"""
    song_name: str
    singers: str
    album: str
    file_size: str = ""
    duration: str = ""
    source: str = "Pjmp3Client"
    ext: str = "mp3"
    download_url: Optional[str] = None
    duration_s: int = 0
    song_id: str = ""
    cover_url: str = ""
    preview_url: Optional[str] = None  # 试听URL


class Pjmp3Client:
    """
    pjmp3.com 网页抓取客户端
    """

    BASE_URL = "https://pjmp3.com"
    SEARCH_URL = "/search.php"
    SONG_URL = "/song.php"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        self.enabled = BeautifulSoup is not None

        if not self.enabled:
            logger.warning("Pjmp3Client: beautifulsoup4 not installed")

    def search(self, keyword: str, limit: int = 20) -> List[Pjmp3SongInfo]:
        """搜索歌曲"""
        if not self.enabled or not keyword or not keyword.strip():
            return []

        logger.info(f"Pjmp3Client: 搜索 '{keyword}'")

        try:
            params = {"keyword": keyword.strip()}
            url = urljoin(self.BASE_URL, self.SEARCH_URL)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'lxml')

            # 查找所有歌曲链接
            results = []
            song_items = soup.find_all('a', href=re.compile(r'song\.php\?id=\d+'))

            for item in song_items[:limit]:
                try:
                    song_info = self._parse_song_item(item)
                    if song_info:
                        results.append(song_info)
                except Exception as e:
                    logger.error(f"Pjmp3Client: 解析失败 - {e}")
                    continue

            logger.info(f"Pjmp3Client: 成功解析 {len(results)} 首歌曲")
            return results

        except Exception as e:
            logger.error(f"Pjmp3Client: 搜索失败 - {e}")
            return []

    def search_with_artist_filter(
        self,
        song_name: str,
        artist: str = "",
        limit: int = 10
    ) -> List[Pjmp3SongInfo]:
        """
        搜索并过滤歌手（精准匹配）

        pjmp3 只支持歌曲名搜索，此方法先按歌曲名搜索，然后过滤结果只保留匹配的歌手。
        """
        if not self.enabled:
            return []

        if not artist or not artist.strip():
            return self.search(song_name, limit=limit)

        logger.info(f"Pjmp3Client: 精准搜索 '{song_name}' - '{artist}'")

        # 搜索歌曲名（获取更多结果用于过滤）
        all_results = self.search(song_name, limit=50)
        if not all_results:
            return []

        # 使用相似度匹配过滤歌手
        from difflib import SequenceMatcher

        def calculate_similarity(a: str, b: str) -> float:
            if not a or not b:
                return 0.0
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        filtered_results = []
        artist_normalized = artist.lower().replace(" ", "").replace("&", "").replace("、", "")

        for song in all_results:
            singers_normalized = song.singers.lower().replace(" ", "").replace("&", "").replace("、", "")
            singer_sim = calculate_similarity(artist_normalized, singers_normalized)

            is_match = False

            # 1. 完全包含
            if artist_normalized in singers_normalized or singers_normalized in artist_normalized:
                is_match = True
            # 2. 相似度 >= 60%
            elif singer_sim >= 0.6:
                is_match = True
            # 3. 分词匹配（处理 "刘惜君&王赫野"）
            else:
                artist_parts = artist_normalized.split("&")
                singer_parts = singers_normalized.split("&")
                for a_part in artist_parts:
                    for s_part in singer_parts:
                        if calculate_similarity(a_part, s_part) >= 0.8:
                            is_match = True
                            break
                    if is_match:
                        break

            if is_match:
                filtered_results.append(song)

        # 如果没有匹配结果，返回前几个相似度最高的
        if not filtered_results:
            all_results.sort(
                key=lambda s: calculate_similarity(artist_normalized, s.singers.lower()),
                reverse=True
            )
            if calculate_similarity(artist_normalized, all_results[0].singers.lower()) > 0.3:
                filtered_results = all_results[:3]
            else:
                return []

        logger.info(f"Pjmp3Client: 精准匹配 {len(filtered_results)}/{len(all_results)} 首")
        return filtered_results[:limit]

    def _parse_song_item(self, item) -> Optional[Pjmp3SongInfo]:
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
                song_name = song_name_elem.get_text(strip=True)

            singer_elem = item.find('div', class_=re.compile('singer', re.I))
            if singer_elem:
                singers = singer_elem.get_text(strip=True)

            # 如果没找到，尝试从所有子元素提取
            if song_name == "未知":
                all_texts = [t.strip() for t in item.stripped_strings if t.strip()]
                all_texts = [t for t in all_texts if not (len(t) == 1 and ord(t[0]) > 0xF000)]
                if len(all_texts) >= 2:
                    song_name = all_texts[0]
                    singers = all_texts[1]

            cover_url = ""
            img = item.find('img')
            if img:
                cover_url = img.get('src', '')

            return Pjmp3SongInfo(
                song_name=song_name,
                singers=singers,
                album="",
                song_id=song_id,
                cover_url=cover_url,
            )

        except Exception as e:
            logger.error(f"Pjmp3Client: 解析歌曲项失败 - {e}")
            return None

    def get_song_detail(self, song_id: str) -> Optional[Pjmp3SongInfo]:
        """获取歌曲详情（包含下载链接）"""
        if not self.enabled or not song_id:
            return None

        logger.info(f"Pjmp3Client: 获取歌曲详情 ID={song_id}")

        try:
            url = urljoin(self.BASE_URL, f"{self.SONG_URL}?id={song_id}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'lxml')

            song_name = ""
            singers = ""
            album = ""
            duration = ""
            cover_url = ""
            preview_url = None

            # 歌名
            title_elem = soup.find('div', class_='song-title')
            if title_elem:
                song_name = title_elem.get_text(strip=True)

            # 歌手和专辑
            subtitle_elem = soup.find('div', class_='song-subtitle')
            if subtitle_elem:
                subtitle_text = subtitle_elem.get_text(strip=True)
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

            return Pjmp3SongInfo(
                song_name=song_name,
                singers=singers,
                album=album,
                duration=duration,
                duration_s=duration_s,
                song_id=song_id,
                cover_url=cover_url,
                download_url=preview_url,
                preview_url=preview_url,
            )

        except Exception as e:
            logger.error(f"Pjmp3Client: 获取歌曲详情失败 - {e}")
            return None

    def download_file(self, download_url: str, save_path: str, song_name: str = "") -> bool:
        """下载歌曲文件"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://pjmp3.com/",
                "Accept": "*/*",
            }

            logger.info(f"Pjmp3Client: 开始下载 {song_name}")

            response = requests.get(
                download_url,
                headers=headers,
                timeout=60,
                stream=True
            )
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Pjmp3Client: 下载完成 {save_path}")
            return True

        except Exception as e:
            logger.error(f"Pjmp3Client: 下载失败 - {e}")
            return False


# 全局客户端实例
_pjmp3_client: Optional[Pjmp3Client] = None


def get_pjmp3_client() -> Optional[Pjmp3Client]:
    """获取全局 Pjmp3Client 实例"""
    global _pjmp3_client
    if _pjmp3_client is None:
        _pjmp3_client = Pjmp3Client()
    return _pjmp3_client


def reset_pjmp3_client():
    """重置全局实例"""
    global _pjmp3_client
    _pjmp3_client = None
