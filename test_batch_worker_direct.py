"""Direct test of BatchSearchWorker without UI"""
import sys
from pyqt_ui.workers import BatchSearchWorker
from PyQt6.QtWidgets import QApplication


def test_batch_worker_direct():
    """Test BatchSearchWorker directly"""
    app = QApplication(sys.argv)

    # Test data
    batch_text = """七里香 - 周杰伦
夜曲 - 周杰伦"""

    sources = ['QQMusicClient']

    print("=" * 60)
    print("BATCH SEARCH WORKER DIRECT TEST")
    print("=" * 60)
    print(f"Batch text:\n{batch_text}")
    print(f"Sources: {sources}")

    # Create worker
    worker = BatchSearchWorker(batch_text, sources)

    results = {'completed': False, 'data': None, 'error': None}

    def on_started():
        print("✓ Search started signal received")

    def on_progress(message):
        print(f"  Progress: {message}")

    def on_finished(matched_results):
        print(f"\n✓ Search finished signal received")
        print(f"✓ Matched {len(matched_results)} songs")
        for original, result in matched_results.items():
            parsed = result['parsed']
            print(f"  - {parsed['name']} - {parsed['singer']}")
        results['completed'] = True
        results['data'] = matched_results
        app.quit()

    def on_error(error_msg):
        print(f"\n✗ Search error signal received: {error_msg}")
        results['completed'] = True
        results['error'] = error_msg
        app.quit()

    # Connect signals
    worker.search_started.connect(on_started)
    worker.search_progress.connect(on_progress)
    worker.search_finished.connect(on_finished)
    worker.search_error.connect(on_error)

    # Start worker
    print("\nStarting worker...")
    worker.start()

    # Run event loop
    app.exec()

    # Report results
    print("\n" + "=" * 60)
    if results['completed'] and not results['error']:
        print("✓ TEST PASSED - BatchSearchWorker works correctly")
        print("=" * 60)
        return 0
    else:
        print("✗ TEST FAILED")
        if results['error']:
            print(f"Error: {results['error']}")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(test_batch_worker_direct())
