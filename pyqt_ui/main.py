"""Main Application Window"""
import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QHeaderView,
    QMenu, QMessageBox, QAbstractItemView, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSlot
from .config import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, LOG_DIR,
    SOURCE_LABELS, DEFAULT_SOURCES
)
from .workers import SearchWorker, DownloadWorker, BatchSearchWorker

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
        self.download_worker = None
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

        # Tab widget for mode switching
        self.mode_tab_widget = QTabWidget()
        main_layout.addWidget(self.mode_tab_widget)

        # Music Source Selection (shared between modes)
        # 1. Source Selection Group
        self.source_group = QGroupBox("Music Sources")
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

        self.source_group.setLayout(source_layout)
        main_layout.addWidget(self.source_group)
        
        # Create single mode tab
        single_tab = QWidget()
        single_layout = QVBoxLayout(single_tab)
        


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

        single_layout.addLayout(search_layout)

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

        single_layout.addLayout(progress_layout)

        # 4. Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            '☐', '#', 'Song Name', 'Singer', 'Album', 'Size', 'Duration', 'Source'
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setColumnWidth(0, 40)  # Checkbox column
        self.results_table.setColumnWidth(1, 50)  # Index column
        self.results_table.setVisible(False)
        single_layout.addWidget(self.results_table)

        # Setup context menu
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(
            self.show_context_menu
        )

        # Setup header click for select all
        self.results_table.horizontalHeader().sectionClicked.connect(
            self.on_header_clicked
        )

        
        # Add single mode tab to tab widget
        self.mode_tab_widget.addTab(single_tab, "单曲下载")
        # Create batch mode tab
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        
        # Batch input area
        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText("Enter songs (format: Song Name - Artist, one per line)")
        self.batch_input.setMinimumHeight(200)
        batch_layout.addWidget(self.batch_input)
        
        # Batch search button
        self.batch_search_btn = QPushButton("Batch Search")
        self.batch_search_btn.setMinimumHeight(40)
        self.batch_search_btn.clicked.connect(self.on_batch_search_clicked)
        batch_layout.addWidget(self.batch_search_btn)
        
        # Add stretch to push content to top
        
        # Batch Results Table
        self.batch_results_table = QTableWidget()
        self.batch_results_table.setColumnCount(6)
        self.batch_results_table.setHorizontalHeaderLabels([
            '[checkbox]', '#', 'Song Name', 'Singer', 'Album', 'Source'
        ])
        self.batch_results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.batch_results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.batch_results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.batch_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.batch_results_table.setColumnWidth(0, 40)
        self.batch_results_table.setColumnWidth(1, 50)
        self.batch_results_table.setVisible(False)
        batch_layout.addWidget(self.batch_results_table)
        
        batch_layout.addStretch()
        
        # Add batch mode tab to tab widget
        self.mode_tab_widget.addTab(batch_tab, "批量下载")
        

        
        # Status bar
        self.statusBar().showMessage('Ready')

        logger.info("UI components initialized")

    @pyqtSlot(int)
    def on_select_all_toggled(self, state):
        """Handle Select All checkbox"""
        checked = (state == Qt.CheckState.Checked.value)
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
    def on_batch_search_clicked(self):
        """Handle batch search button click"""
        batch_text = self.batch_input.toPlainText().strip()

        if not batch_text:
            self.statusBar().showMessage('Please enter song list', 3000)
            return

        # Get selected sources
        selected_sources = [
            source for source, cb in self.source_checkboxes.items()
            if cb.isChecked()
        ]

        if not selected_sources:
            self.statusBar().showMessage('Please select at least one source', 3000)
            return

        # Disable batch search button
        self.batch_search_btn.setEnabled(False)
        self.batch_input.setEnabled(False)

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setVisible(True)
        self.status_label.setText("Preparing batch search...")
        self.batch_results_table.setVisible(False)

        # Create and start batch search worker
        self.batch_search_worker = BatchSearchWorker(batch_text, selected_sources)
        self.batch_search_worker.search_started.connect(self.on_batch_search_started)
        self.batch_search_worker.search_progress.connect(self.on_batch_search_progress)
        self.batch_search_worker.search_finished.connect(self.on_batch_search_finished)
        self.batch_search_worker.search_error.connect(self.on_batch_search_error)
        self.batch_search_worker.start()

    def on_batch_search_started(self):
        """Handle batch search started"""
        self.statusBar().showMessage('Batch search in progress...')

    @pyqtSlot(str)
    def on_batch_search_progress(self, message):
        """Handle batch search progress update"""
        self.status_label.setText(message)

    @pyqtSlot(dict)
    def on_batch_search_finished(self, matched_results):
        """Handle batch search finished - display results"""
        # Re-enable controls
        self.batch_search_btn.setEnabled(True)
        self.batch_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)

        # Populate batch results table
        self.populate_batch_results_table(matched_results)

        total_matched = len(matched_results)
        self.statusBar().showMessage(f'Batch search completed: {total_matched} songs found', 5000)

    @pyqtSlot(str)
    def on_batch_search_error(self, error_msg):
        """Handle batch search error"""
        self.batch_search_btn.setEnabled(True)
        self.batch_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.statusBar().showMessage(error_msg, 5000)

    def populate_batch_results_table(self, matched_results):
        """Populate batch results table with matched songs"""
        from PyQt6.QtWidgets import QTableWidgetItem
        from PyQt6.QtCore import Qt

        self.batch_results_table.setRowCount(len(matched_results))
        self.batch_results_table.setVisible(True)

        for row, (original_text, result) in enumerate(matched_results.items()):
            # Checkbox column
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            self.batch_results_table.setItem(row, 0, checkbox_item)

            # Index
            self.batch_results_table.setItem(row, 1, QTableWidgetItem(str(row + 1)))

            # Song name (matched)
            song_name = result.get('matched_song_name', 'N/A')
            self.batch_results_table.setItem(row, 2, QTableWidgetItem(song_name))

            # Singer (matched)
            singer = result.get('matched_singer', 'N/A')
            self.batch_results_table.setItem(row, 3, QTableWidgetItem(singer))

            # Album
            album = getattr(result['match'], 'album', 'N/A') if 'match' in result else 'N/A'
            self.batch_results_table.setItem(row, 4, QTableWidgetItem(str(album)))

            # Source
            source = getattr(result['match'], 'source', 'N/A') if 'match' in result else 'N/A'
            if source != 'N/A':
                source = source.replace('MusicClient', '')
            self.batch_results_table.setItem(row, 5, QTableWidgetItem(source))



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

                # Column 0: Checkbox
                checkbox_item = QTableWidgetItem()
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                checkbox_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row, 0, checkbox_item)

                # Store song data in checkbox column
                checkbox_item.setData(Qt.ItemDataRole.UserRole, song)

                # Column 1: Index
                idx_item = QTableWidgetItem(str(row + 1))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row, 1, idx_item)

                # Column 2: Song name
                self.results_table.setItem(row, 2, QTableWidgetItem(
                    song.get('song_name', 'N/A')
                ))

                # Column 3: Singer
                self.results_table.setItem(row, 3, QTableWidgetItem(
                    song.get('singers', 'N/A')
                ))

                # Column 4: Album
                self.results_table.setItem(row, 4, QTableWidgetItem(
                    song.get('album', 'N/A')
                ))

                # Column 5: Size
                size_item = QTableWidgetItem(song.get('file_size', 'N/A'))
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row, 5, size_item)

                # Column 6: Duration
                duration_item = QTableWidgetItem(song.get('duration', 'N/A'))
                duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row, 6, duration_item)

                # Column 7: Source
                source_label = source.replace('MusicClient', '')
                source_item = QTableWidgetItem(source_label)
                source_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row, 7, source_item)

                row += 1

        logger.info(f"Table populated with {row} results")

    def show_context_menu(self, pos):
        """Show right-click context menu"""
        if self.results_table.rowCount() == 0:
            return

        menu = QMenu(self)

        # Download Checked (new feature)
        checked_count = self.get_checked_count()
        download_checked_action = menu.addAction(
            f"Download Checked ({checked_count})"
        )
        download_checked_action.triggered.connect(self.download_checked)
        download_checked_action.setEnabled(checked_count > 0)

        # Download Selected (original feature)
        download_selected_action = menu.addAction("Download Selected")
        download_selected_action.triggered.connect(self.download_selected)

        # Download All (original feature)
        download_all_action = menu.addAction("Download All Results")
        download_all_action.triggered.connect(self.download_all)

        menu.addSeparator()

        # Select All (new feature)
        select_all_action = menu.addAction("Select All")
        select_all_action.triggered.connect(self.select_all)

        # Invert Selection (new feature)
        invert_action = menu.addAction("Invert Selection")
        invert_action.triggered.connect(self.on_invert_selection)

        # Uncheck All (new feature)
        uncheck_all_action = menu.addAction("Uncheck All")
        uncheck_all_action.triggered.connect(self.uncheck_all)

        menu.addSeparator()

        # Copy info (original feature)
        copy_action = menu.addAction("Copy Song Info")
        copy_action.triggered.connect(self.copy_song_info)

        menu.exec(self.results_table.mapToGlobal(pos))

    def get_selected_song(self):
        """Get selected row's song data"""
        current_row = self.results_table.currentRow()
        if current_row < 0:
            return None

        item = self.results_table.item(current_row, 0)
        if item is None:
            return None

        song = item.data(Qt.ItemDataRole.UserRole)
        return song

    def download_selected(self):
        """Download selected song"""
        song = self.get_selected_song()
        if song is None:
            QMessageBox.warning(self, "No Selection", "Please select a song first")
            return

        self.start_download([song])

    def download_all(self):
        """Download all results"""
        if self.results_table.rowCount() == 0:
            return

        songs = []
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item:
                song = item.data(Qt.ItemDataRole.UserRole)
                if song:
                    songs.append(song)

        if songs:
            self.start_download(songs)

    def start_download(self, songs):
        """Start download with worker thread"""
        # Disable controls
        self.search_btn.setEnabled(False)
        self.search_input.setEnabled(False)
        self.results_table.setEnabled(False)

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)

        song_name = songs[0].get('song_name', 'Unknown')
        self.status_label.setText(f"Preparing to download: {song_name}...")

        # Start worker
        self.download_worker = DownloadWorker(songs)
        self.download_worker.download_started.connect(self.on_download_started)
        self.download_worker.download_progress.connect(self.on_download_progress)
        self.download_worker.download_finished.connect(self.on_download_finished)
        self.download_worker.download_error.connect(self.on_download_error)
        self.download_worker.start()

    @pyqtSlot()
    def on_download_started(self):
        """Handle download started"""
        self.statusBar().showMessage('Downloading...')

    @pyqtSlot(str, int)
    def on_download_progress(self, message, progress):
        """Handle download progress"""
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)

    @pyqtSlot(list)
    def on_download_finished(self, songs):
        """Handle download completion"""
        # Hide progress
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)

        # Re-enable controls
        self.search_btn.setEnabled(True)
        self.search_input.setEnabled(True)
        self.results_table.setEnabled(True)

        # Show success message
        song_count = len(songs)
        QMessageBox.information(
            self,
            "Download Complete",
            f"Successfully downloaded {song_count} song(s)!\n\n"
            f"Files saved to: musicdl_outputs/"
        )

        self.statusBar().showMessage(f'Downloaded {song_count} song(s)', 5000)
        logger.info(f"Download completed: {song_count} songs")

    @pyqtSlot(str)
    def on_download_error(self, error_msg):
        """Handle download error"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.search_btn.setEnabled(True)
        self.search_input.setEnabled(True)
        self.results_table.setEnabled(True)

        QMessageBox.critical(self, "Download Error", error_msg)
        self.statusBar().showMessage('Download failed', 5000)

    def copy_song_info(self):
        """Copy selected song info to clipboard"""
        song = self.get_selected_song()
        if song is None:
            return

        info = f"{song.get('song_name', '')} - {song.get('singers', '')}"
        clipboard = QApplication.clipboard()
        clipboard.setText(info)
        self.statusBar().showMessage(f'Copied: {info}', 2000)

    def get_checked_count(self):
        """Get number of checked songs"""
        count = 0
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                count += 1
        return count

    def get_checked_songs(self):
        """Get list of checked songs"""
        songs = []
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                song = item.data(Qt.ItemDataRole.UserRole)
                if song:
                    songs.append(song)
        return songs

    @pyqtSlot(int)
    def on_header_clicked(self, logical_index):
        """Handle header click - toggle select all"""
        if logical_index == 0:  # Checkbox column
            # Check if all rows are checked
            all_checked = all(
                self.results_table.item(row, 0).checkState() == Qt.CheckState.Checked
                for row in range(self.results_table.rowCount())
                if self.results_table.item(row, 0) is not None
            )

            new_state = Qt.CheckState.Unchecked if all_checked else Qt.CheckState.Checked

            for row in range(self.results_table.rowCount()):
                item = self.results_table.item(row, 0)
                if item:
                    item.setCheckState(new_state)

            checked_count = self.get_checked_count()
            self.statusBar().showMessage(
                f'{"Uncheck all" if all_checked else "Select all"}: {checked_count} songs',
                2000
            )

    def select_all(self):
        """Select all songs"""
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
        self.statusBar().showMessage(f'Selected {self.results_table.rowCount()} songs', 2000)

    def uncheck_all(self):
        """Uncheck all songs"""
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.statusBar().showMessage('Uncheck all', 2000)

    def on_invert_selection(self):
        """Invert all checkbox states"""
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item:
                current_state = item.checkState()
                new_state = (
                    Qt.CheckState.Checked if current_state == Qt.CheckState.Unchecked
                    else Qt.CheckState.Unchecked
                )
                item.setCheckState(new_state)

        checked_count = self.get_checked_count()
        self.statusBar().showMessage(f'{checked_count} songs selected', 2000)

    def download_checked(self):
        """Download checked songs"""
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "No Results", "No songs to download")
            return

        checked_songs = self.get_checked_songs()

        if not checked_songs:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please check at least one song to download"
            )
            return

        # Confirm download
        reply = QMessageBox.question(
            self,
            "Confirm Download",
            f"Download {len(checked_songs)} checked song(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.start_download(checked_songs)


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('Music Downloader')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
