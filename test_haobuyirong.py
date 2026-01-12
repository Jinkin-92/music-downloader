"""Search and download '好不容易'"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyqt_ui.music_downloader import MusicDownloader
import time

print("=" * 60)
print("DOWNLOAD SONG: 好不容易")
print("=" * 60)

downloader = MusicDownloader()

# Search for '好不容易'
print("\nSearching for '好不容易'...")
results = downloader.search("好不容易", sources=['QQMusicClient', 'NeteaseMusicClient'])

if not results:
    print("ERROR: No search results")
    sys.exit(1)

# Show all results
total_songs = 0
for source, songs in results.items():
    print(f"\n{source}: {len(songs)} songs")
    total_songs += len(songs)
    for i, song in enumerate(songs[:3], 1):
        print(f"  {i}. {song['song_name']} - {song['singers']} ({song['file_size']})")

print(f"\nTotal songs found: {total_songs}")

# Download all songs
all_songs = []
for songs in results.values():
    all_songs.extend(songs)

if all_songs:
    print(f"\nDownloading {len(all_songs)} song(s)...")
    try:
        downloader.download(all_songs)

        # Wait for downloads to complete
        time.sleep(5)

        # Check downloaded files
        download_dir = Path("musicdl_outputs")
        ogg_files = list(download_dir.rglob("*.ogg"))

        if ogg_files:
            # Get latest files
            latest_files = sorted(ogg_files, key=lambda p: p.stat().st_mtime, reverse=True)[:len(all_songs)]

            print("\n" + "=" * 60)
            print("DOWNLOAD COMPLETE!")
            print("=" * 60)
            for f in latest_files:
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"  {f.name}")
                print(f"  Size: {size_mb:.1f} MB")
                print(f"  Path: {f.parent}")
                print()
        else:
            print("WARNING: No files found")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No songs to download")
