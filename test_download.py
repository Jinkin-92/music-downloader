import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pyqt_ui.music_downloader import MusicDownloader

print("Test: Download '好不容易'")
downloader = MusicDownloader()

# Search
results = downloader.search("好不容易", sources=['QQMusicClient'])
if not results or not results.get('QQMusicClient'):
    print("ERROR: No search results")
    sys.exit(1)

songs = results['QQMusicClient']
print(f"Found {len(songs)} songs")

# Download first song
first_song = songs[0]
print(f"Downloading: {first_song['song_name']}")

try:
    downloader.download([first_song])
    print("Download initiated successfully")

    # Check for files
    import time
    time.sleep(2)  # Wait a bit

    download_dir = Path("musicdl_outputs")
    ogg_files = list(download_dir.rglob("*.ogg"))
    if ogg_files:
        latest = max(ogg_files, key=lambda p: p.stat().st_mtime)
        print(f"Downloaded: {latest}")
        print(f"Size: {latest.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print("No files found yet")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
