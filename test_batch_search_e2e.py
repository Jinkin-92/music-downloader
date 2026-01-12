"""End-to-end test for batch search functionality"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from pyqt_ui.main import MainWindow


def test_batch_search_e2e():
    """Test batch search end-to-end flow"""
    app = QApplication(sys.argv)

    # Create main window
    window = MainWindow()
    window.show()

    # Switch to batch mode tab
    batch_tab_index = 1  # Second tab
    window.mode_tab_widget.setCurrentIndex(batch_tab_index)

    # Input batch text
    batch_text = """七里香 - 周杰伦
夜曲 - 周杰伦
晴天 - 周杰伦"""

    window.batch_input.setPlainText(batch_text)

    # Select one music source
    for source_name, checkbox in window.source_checkboxes.items():
        if source_name == 'QQ音乐':
            checkbox.setChecked(True)
        else:
            checkbox.setChecked(False)

    print("=" * 60)
    print("BATCH SEARCH E2E TEST")
    print("=" * 60)
    print(f"Batch input text:\n{batch_text}")
    print(f"Selected sources: QQ音乐")
    print("\nTriggering batch search...")

    # Trigger batch search
    window.on_batch_search_clicked()

    # Wait for async operation to complete
    # Use QTimer to allow event loop to process
    test_results = {'completed': False, 'success': False}

    def check_results():
        """Check if search completed successfully"""
        if window.batch_results_table.isVisible():
            row_count = window.batch_results_table.rowCount()
            print(f"\n✓ Batch search completed!")
            print(f"✓ Results table is visible")
            print(f"✓ Found {row_count} matched songs")

            # Print each result
            for row in range(row_count):
                song_name_item = window.batch_results_table.item(row, 2)
                singer_item = window.batch_results_table.item(row, 3)
                source_item = window.batch_results_table.item(row, 5)

                if song_name_item and singer_item and source_item:
                    song_name = song_name_item.text()
                    singer = singer_item.text()
                    source = source_item.text()
                    print(f"  Row {row + 1}: {song_name} - {singer} [{source}]")

            test_results['completed'] = True
            test_results['success'] = row_count > 0
            app.quit()
        else:
            # Check again after delay
            print("Waiting for results...")
            QTimer.singleShot(2000, check_results)

    # Start checking after initial delay
    QTimer.singleShot(3000, check_results)

    # Run event loop
    app.exec()

    # Report results
    print("\n" + "=" * 60)
    if test_results['success']:
        print("✓ BATCH SEARCH E2E TEST PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ BATCH SEARCH E2E TEST FAILED")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(test_batch_search_e2e())
