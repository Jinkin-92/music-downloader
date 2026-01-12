"""Simple test for search"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pyqt_ui.music_downloader import MusicDownloader
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("Testing search for '好不容易'...")
downloader = MusicDownloader()

results = downloader.search("好不容易", sources=['QQMusicClient'])
print(f"\nSearch returned {len(results)} source(s)")

for source, songs in results.items():
    print(f"\n{source}: {len(songs)} songs found")
    for i, song in enumerate(songs[:5], 1):
        print(f"  {i}. {song['song_name']} - {song['singers']} ({song['file_size']})")

if results and any(songs for songs in results.values()):
    print("\n✓ Search test PASSED")
    # Get first song for download test
    first_source = list(results.keys())[0]
    first_song = results[first_source][0]
    print(f"\nPreparing to download: {first_song['song_name']} - {first_song['singers']}")

    print("\nStarting download...")
    downloader.download([first_song])
    print("✓ Download test PASSED")

    # Check if file exists
    from pathlib import Path
    download_dir = Path("musicdl_outputs")
    if download_dir.exists():
        ogg_files = list(download_dir.rglob("*.ogg"))
        if ogg_files:
            print(f"\n✓ Downloaded file found: {ogg_files[-1].name}")
            print(f"  Size: {ogg_files[-1].stat().st_size / 1024 / 1024:.1f} MB")
        else:
            print("\n✗ No .ogg files found in download directory")
    else:
        print("\n✗ Download directory not found")
else:
    print("\n✗ Search test FAILED - no results")
