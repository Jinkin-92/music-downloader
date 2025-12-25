"""Main Application Window"""
import sys
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from .config import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, LOG_DIR,
    SOURCE_LABELS, DEFAULT_SOURCES
)

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

        logger.info(f"Search initiated: keyword='{keyword}', sources={selected_sources}")
        self.statusBar().showMessage(f'Searching for "{keyword}"...')

        # TODO: Phase 3 - Implement actual search with worker thread


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('Music Downloader')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
