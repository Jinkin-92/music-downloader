"""Complete test: search and download '七里香'"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyqt_ui.music_downloader import MusicDownloader
import time

print("=" * 60)
print("SEARCH AND DOWNLOAD TEST")
print("=" * 60)

downloader = MusicDownloader()

# Step 1: Search
print("\n[Step 1] Searching for '七里香'...")
results = downloader.search("七里香", sources=['QQMusicClient'])

if not results or 'QQMusicClient' not in results:
    print("ERROR: No search results from QQMusicClient")
    sys.exit(1)

songs = results['QQMusicClient']
print(f"Found {len(songs)} songs")

# Show first 3 results
for i, song in enumerate(songs[:3], 1):
    print(f"  {i}. {song['song_name']} - {song['singers']} ({song['file_size']})")

# Step 2: Download first song
first_song = songs[0]
print(f"\n[Step 2] Downloading: {first_song['song_name']} - {first_song['singers']}")

try:
    downloader.download([first_song])
    print("Download command completed successfully")

    # Step 3: Verify download
    print("\n[Step 3] Verifying download...")
    time.sleep(3)  # Wait for file to be written

    download_dir = Path("musicdl_outputs")
    ogg_files = list(download_dir.rglob("*.ogg"))

    if ogg_files:
        # Get latest file
        latest_file = max(ogg_files, key=lambda p: p.stat().st_mtime)
        size_mb = latest_file.stat().st_size / 1024 / 1024

        print(f"SUCCESS! Downloaded file:")
        print(f"  Path: {latest_file}")
        print(f"  Size: {size_mb:.1f} MB")

        if size_mb > 1:  # Reasonable size check
            print("\n" + "=" * 60)
            print("TEST PASSED - Download verified!")
            print("=" * 60)
        else:
            print("\nWARNING: File size too small")
    else:
        print("ERROR: No .ogg files found in download directory")
        sys.exit(1)

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
