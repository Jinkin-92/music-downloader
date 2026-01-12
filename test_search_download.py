"""Test search and download functionality"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyqt_ui.music_downloader import MusicDownloader
import logging

logging.basicConfig(level=logging.INFO)

def test_search_and_download():
    """Test searching and downloading '好不容易'"""
    downloader = MusicDownloader()

    # Step 1: Search
    print("=" * 60)
    print("Step 1: Searching for '好不容易'...")
    print("=" * 60)

    try:
        results = downloader.search("好不容易", sources=['QQMusicClient'])
        print(f"\nSearch completed! Found results from {len(results)} source(s)")

        for source, songs in results.items():
            print(f"\n{source}: {len(songs)} songs")
            for i, song in enumerate(songs[:3], 1):  # Show first 3
                print(f"  {i}. {song}")

        # Step 2: Get first song and download
        if results and songs:
            first_song = songs[0]
            print("\n" + "=" * 60)
            print("Step 2: Downloading first song...")
            print("=" * 60)
            print(f"Song to download: {first_song}")

            downloader.download([first_song])
            print("\nDownload completed!")
            return True
        else:
            print("No songs found!")
            return False

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_search_and_download()
    sys.exit(0 if success else 1)
