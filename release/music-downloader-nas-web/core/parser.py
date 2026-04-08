"""
Batch Parser - 批量文本解析器

将多行文本解析为歌曲列表，支持多种格式。
"""

from typing import List, Dict


class BatchParser:
    """Parse batch input text into song list"""

    MAX_SONGS = 200

    @staticmethod
    def parse(text: str) -> List[Dict[str, str]]:
        """Parse batch input text into song list

        Args:
            text: Multi-line text, format: "song_name - singer"

        Returns:
            [{"name": "song_name", "singer": "singer", "original_line": "original"}, ...]

        Raises:
            ValueError: If input is empty or format is invalid
        """
        if not text or not text.strip():
            raise ValueError("Input cannot be empty")

        lines = [line.strip() for line in text.strip().split('\n')]
        lines = [line for line in lines if line]

        if len(lines) > BatchParser.MAX_SONGS:
            raise ValueError(f"Exceeds maximum songs limit ({BatchParser.MAX_SONGS})")

        songs = []
        for i, line in enumerate(lines, 1):
            if ' - ' in line:
                name, singer = line.split(' - ', 1)
            else:
                raise ValueError(f"Cannot parse line {i}: {line}")

            songs.append({
                'name': name.strip(),
                'singer': singer.strip(),
                'original_line': line
            })

        return songs

    @staticmethod
    def parse_with_album(text: str) -> List[Dict[str, str]]:
        """Parse batch input text with optional album info

        支持格式:
        - "歌名 - 歌手"
        - "歌名 - 歌手 - 专辑"

        Args:
            text: Multi-line text

        Returns:
            [{"name": "song_name", "singer": "singer", "album": "album", "original_line": "original"}, ...]
        """
        if not text or not text.strip():
            raise ValueError("Input cannot be empty")

        lines = [line.strip() for line in text.strip().split('\n')]
        lines = [line for line in lines if line]

        if len(lines) > BatchParser.MAX_SONGS:
            raise ValueError(f"Exceeds maximum songs limit ({BatchParser.MAX_SONGS})")

        songs = []
        for i, line in enumerate(lines, 1):
            parts = line.split(' - ')

            if len(parts) >= 2:
                name = parts[0].strip()
                singer = parts[1].strip()
                album = parts[2].strip() if len(parts) >= 3 else ""
            else:
                raise ValueError(f"Cannot parse line {i}: {line}")

            songs.append({
                'name': name,
                'singer': singer,
                'album': album,
                'original_line': line
            })

        return songs