"""Debug test for batch search functionality"""
import sys
import logging
from PyQt6.QtWidgets import QApplication
from pyqt_ui.workers import BatchSearchWorker

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_batch_search_debug():
    """Test batch search with detailed logging"""
    app = QApplication(sys.argv)

    # Test data
    batch_text = """七里香 - 周杰伦
轨迹 - 周杰伦"""

    sources = ['QQMusicClient']

    print("=" * 70)
    print("BATCH SEARCH DEBUG TEST")
    print("=" * 70)
    print(f"Input:\n{batch_text}")
    print(f"Sources: {sources}")
    print("\n" + "=" * 70)

    # Create worker
    worker = BatchSearchWorker(batch_text, sources)

    results = {'completed': False, 'data': None, 'error': None}

    def on_started():
        print("\n[STARTED] Batch search worker started")

    def on_progress(message):
        print(f"[PROGRESS] {message}")

    def on_finished(matched_results):
        print(f"\n[FINISHED] Search completed with {len(matched_results)} results")
        for original, result in matched_results.items():
            parsed = result['parsed']
            matched_name = result.get('matched_song_name', 'N/A')
            matched_singer = result.get('matched_singer', 'N/A')
            print(f"  ✓ {parsed['name']} - {parsed['singer']}")
            print(f"    → Matched: {matched_name} - {matched_singer}")

        results['completed'] = True
        results['data'] = matched_results

        if len(matched_results) == 0:
            print("\n[WARNING] No matches found!")
        else:
            print(f"\n[SUCCESS] Found {len(matched_results)} matches")

        app.quit()

    def on_error(error_msg):
        print(f"\n[ERROR] {error_msg}")
        results['completed'] = True
        results['error'] = error_msg
        app.quit()

    # Connect signals
    worker.search_started.connect(on_started)
    worker.search_progress.connect(on_progress)
    worker.search_finished.connect(on_finished)
    worker.search_error.connect(on_error)

    # Start worker
    print("\n[STARTING] Starting batch search worker...")
    worker.start()

    # Run event loop
    app.exec()

    # Report results
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    if results['error']:
        print(f"✗ FAILED: {results['error']}")
        return 1
    elif results['data'] is not None:
        count = len(results['data'])
        if count > 0:
            print(f"✓ SUCCESS: Found {count} matches")
            return 0
        else:
            print("✗ WARNING: Search completed but no matches found")
            print("\nPossible reasons:")
            print("1. Network connection issues")
            print("2. Music source API limitations")
            print("3. Song matching threshold too strict")
            print("4. Songs not available on selected source")
            return 1
    else:
        print("✗ FAILED: Search did not complete")
        return 1


if __name__ == '__main__':
    sys.exit(test_batch_search_debug())
