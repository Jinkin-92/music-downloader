"""Main Application Window"""
import sys
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSlot
from .config import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, LOG_DIR,
    SOURCE_LABELS, DEFAULT_SOURCES
)
from .workers import SearchWorker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        """Initialize main window"""
        super().__init__()
        self.source_checkboxes = {}
        self.search_worker = None
        self.current_results = {}  # Store search results
        self.setup_ui()

    def setup_ui(self):
        """Setup basic UI"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Source Selection Group
        source_group = QGroupBox("Music Sources")
        source_layout = QHBoxLayout()

        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.setChecked(True)
        self.select_all_cb.stateChanged.connect(self.on_select_all_toggled)
        source_layout.addWidget(self.select_all_cb)

        for source in DEFAULT_SOURCES:
            cb = QCheckBox(SOURCE_LABELS[source])
            cb.setChecked(True)
            self.source_checkboxes[source] = cb
            source_layout.addWidget(cb)

        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)

        # 2. Search Input Group
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter song name, artist, or keywords...")
        self.search_input.setMinimumHeight(35)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumHeight(35)
        self.search_btn.setMinimumWidth(120)
        self.search_btn.clicked.connect(self.on_search_clicked)
        search_layout.addWidget(self.search_btn)

        main_layout.addLayout(search_layout)

        # 3. Progress Bar
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        progress_layout.addWidget(self.status_label)

        main_layout.addLayout(progress_layout)

        # 4. Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            '#', 'Song Name', 'Singer', 'Album', 'Size', 'Duration', 'Source'
        ])
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setColumnWidth(0, 50)  # Index column
        self.results_table.setVisible(False)
        main_layout.addWidget(self.results_table)

        # Status bar
        self.statusBar().showMessage('Ready')

        logger.info("UI components initialized")

    @pyqtSlot(int)
    def on_select_all_toggled(self, state):
        """Handle Select All checkbox"""
        checked = (state == Qt.Checked)
        for cb in self.source_checkboxes.values():
            cb.setChecked(checked)

    @pyqtSlot()
    def on_search_clicked(self):
        """Handle search button click"""
        keyword = self.search_input.text().strip()

        if not keyword:
            self.statusBar().showMessage('Please enter a keyword', 3000)
            return

        # Get selected sources
        selected_sources = [
            source for source, cb in self.source_checkboxes.items()
            if cb.isChecked()
        ]

        if not selected_sources:
            self.statusBar().showMessage('Please select at least one source', 3000)
            return

        # Disable search button
        self.search_btn.setEnabled(False)
        self.search_input.setEnabled(False)

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setVisible(True)
        self.status_label.setText("Searching...")
        self.results_table.setVisible(False)

        # Start worker thread
        self.search_worker = SearchWorker(keyword, selected_sources)
        self.search_worker.search_started.connect(self.on_search_started)
        self.search_worker.search_progress.connect(self.on_search_progress)
        self.search_worker.search_finished.connect(self.on_search_finished)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.start()

    @pyqtSlot()
    def on_search_started(self):
        """Handle search started"""
        self.statusBar().showMessage('Searching...')

    @pyqtSlot(str)
    def on_search_progress(self, message):
        """Handle search progress update"""
        self.status_label.setText(message)

    @pyqtSlot(dict)
    def on_search_finished(self, results):
        """Handle search completion"""
        self.current_results = results
        self.populate_results_table(results)

        # Hide progress
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)

        # Show table
        self.results_table.setVisible(True)

        # Re-enable controls
        self.search_btn.setEnabled(True)
        self.search_input.setEnabled(True)

        total = sum(len(songs) for songs in results.values())
        self.statusBar().showMessage(f'Found {total} songs', 5000)

    @pyqtSlot(str)
    def on_search_error(self, error_msg):
        """Handle search error"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.search_btn.setEnabled(True)
        self.search_input.setEnabled(True)
        self.statusBar().showMessage(error_msg, 5000)

    def populate_results_table(self, results):
        """Populate table with search results"""
        self.results_table.setRowCount(0)

        row = 0
        for source, songs in results.items():
            for song in songs:
                self.results_table.insertRow(row)

                # Index
                idx_item = QTableWidgetItem(str(row + 1))
                idx_item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(row, 0, idx_item)

                # Song name
                self.results_table.setItem(row, 1, QTableWidgetItem(
                    song.get('song_name', 'N/A')
                ))

                # Singer
                self.results_table.setItem(row, 2, QTableWidgetItem(
                    song.get('singers', 'N/A')
                ))

                # Album
                self.results_table.setItem(row, 3, QTableWidgetItem(
                    song.get('album', 'N/A')
                ))

                # Size
                size_item = QTableWidgetItem(song.get('file_size', 'N/A'))
                size_item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(row, 4, size_item)

                # Duration
                duration_item = QTableWidgetItem(song.get('duration', 'N/A'))
                duration_item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(row, 5, duration_item)

                # Source
                source_label = source.replace('MusicClient', '')
                source_item = QTableWidgetItem(source_label)
                source_item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(row, 6, source_item)

                # Store song data in row
                self.results_table.item(row, 0).setData(Qt.UserRole, song)

                row += 1

        logger.info(f"Table populated with {row} results")


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('Music Downloader')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
