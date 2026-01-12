"""Verify GUI can run without crashing"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from pyqt_ui.main import MainWindow
import time

print("Testing GUI application...")

app = QApplication(sys.argv)

try:
    window = MainWindow()
    print("Window created successfully")

    window.show()
    print("Window shown")

    # Test searching
    from pyqt_ui.music_downloader import MusicDownloader

    print("\nTesting search from GUI context...")
    downloader = MusicDownloader()
    results = downloader.search("test", sources=['QQMusicClient'])
    print(f"Search test: {len(results)} source(s)")

    print("\n" + "=" * 60)
    print("GUI TEST PASSED - Application is ready to use!")
    print("=" * 60)
    print("\nYou can now run: python -m pyqt_ui.main")

    # Close window after 2 seconds
    time.sleep(2)
    window.close()
    sys.exit(0)

except Exception as e:
    print(f"\nGUI TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
