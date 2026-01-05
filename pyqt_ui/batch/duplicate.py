"""Duplicate file detection"""
from pathlib import Path
from typing import List, Dict, Set


class DuplicateChecker:
    """Check for duplicate files in download directory"""

    @staticmethod
    def check_duplicates(songs: List[Dict], download_dir: Path) -> Set[int]:
        """Check which songs already exist as files

        Args:
            songs: List of song dicts with 'name' and 'singer' keys
            download_dir: Directory to check for existing files

        Returns:
            Set of indices (from songs list) that are duplicates
        """
        existing_files = set()
        if download_dir.exists():
            for f in download_dir.iterdir():
                if f.is_file():
                    existing_files.add(DuplicateChecker._normalize_filename(f.name))

        duplicates = set()
        for i, song in enumerate(songs):
            expected_name = DuplicateChecker._generate_filename(song)
            expected_norm = DuplicateChecker._normalize_filename(expected_name)
            if expected_norm in existing_files:
                duplicates.add(i)

        return duplicates

    @staticmethod
    def _generate_filename(song: Dict) -> str:
        """Generate expected filename from song dict"""
        name = song.get('name', 'Unknown')
        singer = song.get('singer', 'Unknown')
        return f"{name} - {singer}"

    @staticmethod
    def _normalize_filename(filename: str) -> str:
        """Normalize filename for comparison (case-insensitive, no extension)"""
        import os
        import re
        name = os.path.splitext(filename)[0]
        name = name.lower()
        name = re.sub(r'[^\w]', '', name)
        return name
