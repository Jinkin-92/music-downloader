"""Main Application Window"""
import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QHeaderView,
    QMenu, QMessageBox, QAbstractItemView, QTabWidget, QSlider
)
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtCore import Qt, pyqtSlot, QSettings
from .config import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, LOG_DIR,
    SOURCE_LABELS, DEFAULT_SOURCES,
    MatchMode, DEFAULT_MATCH_MODE, DEFAULT_MATCH_THRESHOLD,
    MATCH_THRESHOLDS, MATCH_MODE_LABELS
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

        # Match mode settings (for batch download) - will be loaded from QSettings
        self.current_match_mode = DEFAULT_MATCH_MODE
        self.current_threshold = DEFAULT_MATCH_THRESHOLD

        self.setup_ui()

        # Load user preferences after UI is set up
        self.load_match_preferences()

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

        # Match settings group (collapsible)
        match_settings_group = self.setup_batch_match_settings_ui()
        batch_layout.addWidget(match_settings_group)

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
        
        # Batch download button
        self.batch_download_btn = QPushButton("Download Selected")
        self.batch_download_btn.setMinimumHeight(40)
        self.batch_download_btn.setEnabled(False)
        self.batch_download_btn.clicked.connect(self.on_batch_download_clicked)
        batch_layout.addWidget(self.batch_download_btn)
        
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

    @pyqtSlot(object)
    def on_batch_search_finished(self, search_result):
        """Handle batch search finished - display results"""
        # Re-enable controls
        self.batch_search_btn.setEnabled(True)
        self.batch_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)

        # Store result for later use (e.g., match switching)
        self.current_batch_search_result = search_result

        # Populate batch results table
        self.populate_batch_results_table(search_result)

        total_matched = search_result.get_match_count()
        self.statusBar().showMessage(f'Batch search completed: {total_matched} songs found', 5000)

    @pyqtSlot(str)
    def on_batch_search_error(self, error_msg):
        """Handle batch search error"""
        self.batch_search_btn.setEnabled(True)
        self.batch_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.statusBar().showMessage(error_msg, 5000)


    def on_batch_download_clicked(self):
        """Handle batch download button click"""
        from PyQt6.QtCore import Qt
        
        # Get checked songs
        checked_songs = self.get_checked_batch_songs()
        
        if not checked_songs:
            self.statusBar().showMessage('Please select at least one song', 3000)
            return
        
        # Disable controls
        self.batch_download_btn.setEnabled(False)
        self.batch_results_table.setEnabled(False)
        
        # Use existing download logic
        self.start_download(checked_songs)
    
    def get_checked_batch_songs(self):
        """Get all checked songs from batch results table"""
        from PyQt6.QtCore import Qt
        
        checked_songs = []
        for row in range(self.batch_results_table.rowCount()):
            checkbox_item = self.batch_results_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                # Retrieve song data from UserRole
                song_dict = checkbox_item.data(Qt.ItemDataRole.UserRole)
                if song_dict:
                    checked_songs.append(song_dict)
        
        return checked_songs
    def populate_batch_results_table(self, search_result, min_similarity: float = 0.0):
        """
        Populate batch results table with matched songs

        Args:
            search_result: BatchSearchResult object
            min_similarity: Minimum similarity threshold (optional, for filtering)
        """
        from PyQt6.QtWidgets import QTableWidgetItem
        from PyQt6.QtCore import Qt
        from .batch.models import MatchSource

        # search_result is BatchSearchResult object
        total_songs = search_result.total_songs
        matches = search_result.matches

        self.batch_results_table.setRowCount(total_songs)
        self.batch_results_table.setVisible(True)

        # Enable batch download button if there are results
        if search_result.get_match_count() > 0:
            self.batch_download_btn.setEnabled(True)

        for row, (original_line, song_match) in enumerate(matches.items()):
            # Checkbox column
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)

            # Get current match data
            if song_match.has_match and song_match.current_match:
                # Apply threshold filtering
                # If current match is below threshold, try to auto-select a better one
                if song_match.current_match.similarity_score < min_similarity:
                    best_candidate = song_match.auto_select_best_within_threshold(min_similarity)

                    if best_candidate:
                        # Switch to better candidate
                        song_match.switch_to_candidate(best_candidate, MatchSource.AUTO_FILTERED)
                    else:
                        # No candidate meets threshold - keep current but mark it
                        pass  # Current match is already set

                song_dict = song_match.get_current_match_dict()
                checkbox_item.setData(Qt.ItemDataRole.UserRole, song_dict)
                checkbox_item.setData(Qt.ItemDataRole.UserRole + 1, song_dict)

                # Song name
                self.batch_results_table.setItem(
                    row, 2, QTableWidgetItem(song_match.current_match.song_name)
                )

                # Singer
                self.batch_results_table.setItem(
                    row, 3, QTableWidgetItem(song_match.current_match.singers)
                )

                # Album
                self.batch_results_table.setItem(
                    row, 4, QTableWidgetItem(song_match.current_match.album)
                )

                # Source
                source = song_match.current_match.source.replace('MusicClient', '')
                self.batch_results_table.setItem(row, 5, QTableWidgetItem(source))

                # Similarity with color coding
                similarity_value = song_match.current_match.similarity_score
                similarity_item = QTableWidgetItem(f"{similarity_value:.2%}")
                similarity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Color based on similarity
                if similarity_value >= 0.8:
                    similarity_item.setForeground(Qt.GlobalColor.darkGreen)
                elif similarity_value >= 0.6:
                    similarity_item.setForeground(Qt.GlobalColor.darkYellow)
                else:
                    similarity_item.setForeground(Qt.GlobalColor.red)

                # Mark if below threshold
                if similarity_value < min_similarity:
                    # Italic or different background to indicate below threshold
                    font = similarity_item.font()
                    font.setItalic(True)
                    similarity_item.setFont(font)

                self.batch_results_table.setItem(row, 6, similarity_item)

                # Action button (switch match)
                from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

                switch_btn_widget = QWidget()
                switch_layout = QHBoxLayout(switch_btn_widget)
                switch_layout.setContentsMargins(4, 2, 4, 2)

                switch_btn = QPushButton("Switch")
                switch_btn.setMaximumWidth(60)
                switch_btn.clicked.connect(
                    lambda checked, line=original_line: self.on_switch_match(line)
                )
                switch_layout.addWidget(switch_btn)

                self.batch_results_table.setCellWidget(row, 6, switch_btn_widget)

            else:
                # No match found
                checkbox_item.setData(Qt.ItemDataRole.UserRole, original_line)

                # Song name - show original query
                self.batch_results_table.setItem(
                    row, 2, QTableWidgetItem(song_match.query['name'])
                )

                # Singer
                self.batch_results_table.setItem(
                    row, 3, QTableWidgetItem(song_match.query['singer'])
                )

                # Source - show "Not Found"
                self.batch_results_table.setItem(row, 5, QTableWidgetItem("Not Found"))

                # Similarity
                self.batch_results_table.setItem(row, 6, QTableWidgetItem("N/A"))

                # Action button (retry search)
                from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

                retry_btn_widget = QWidget()
                retry_layout = QHBoxLayout(retry_btn_widget)
                retry_layout.setContentsMargins(4, 2, 4, 2)

                retry_btn = QPushButton("Retry")
                retry_btn.setMaximumWidth(60)
                retry_btn.clicked.connect(
                    lambda checked, line=original_line: self.on_retry_search(line)
                )
                retry_layout.addWidget(retry_btn)

                self.batch_results_table.setCellWidget(row, 6, retry_btn_widget)

            # Index
            self.batch_results_table.setItem(row, 1, QTableWidgetItem(str(row + 1)))

            # Checkbox
            self.batch_results_table.setItem(row, 0, checkbox_item)



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
        self.batch_download_btn.setEnabled(True)
        self.batch_results_table.setEnabled(True)
        self.batch_download_btn.setEnabled(True)
        self.batch_results_table.setEnabled(True)

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
        self.batch_download_btn.setEnabled(True)
        self.batch_results_table.setEnabled(True)

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

    def on_switch_match(self, original_line: str):
        """Open match switcher dialog for batch result"""
        if not hasattr(self, "current_batch_search_result"):
            QMessageBox.warning(self, "Error", "No batch search results found")
            return

        song_match = self.current_batch_search_result.matches.get(original_line)
        if not song_match:
            QMessageBox.warning(self, "Error", "Song match information not found")
            return

        from .batch.match_switcher_dialog import MatchSwitcherDialog

        dialog = MatchSwitcherDialog(song_match, self)
        dialog.match_changed.connect(self.on_match_changed)
        dialog.exec()

    def on_match_changed(self, original_line: str, new_candidate):
        """Handle match change from switcher dialog"""
        if not hasattr(self, "current_batch_search_result"):
            return

        song_match = self.current_batch_search_result.matches.get(original_line)
        if song_match:
            from .batch.models import MatchSource
            song_match.switch_to_candidate(new_candidate, MatchSource.USER_SELECTED)

            # Refresh the batch results table
            self.populate_batch_results_table(self.current_batch_search_result)

            self.statusBar().showMessage(
                f"Switched match: {new_candidate.song_name} - {new_candidate.singers}", 3000
            )

    def on_retry_search(self, original_line: str):
        """Retry searching for a specific song"""
        if not hasattr(self, "current_batch_search_result"):
            QMessageBox.warning(self, "Error", "No batch search results found")
            return

        song_match = self.current_batch_search_result.matches.get(original_line)
        if not song_match:
            return

        # For now, just show a message - full implementation would retry search
        QMessageBox.information(
            self,
            "Retry Search",
            f"Retry search for: {song_match.query['name']} - {song_match.query['singer']}\n\n"
            "This feature is not yet implemented. Use the batch search button to search again."
        )

    def setup_batch_match_settings_ui(self):
        """
        Create match confidence settings UI (collapsible)

        Returns:
            QGroupBox: The settings group widget
        """
        # Main settings group
        settings_group = QGroupBox("Match Settings")
        settings_group.setMaximumHeight(250)

        main_layout = QVBoxLayout()
        settings_group.setLayout(main_layout)

        # Preset mode buttons
        modes_layout = QHBoxLayout()
        modes_layout.setSpacing(10)

        self.strict_btn = QPushButton(MATCH_MODE_LABELS[MatchMode.STRICT])
        self.standard_btn = QPushButton(MATCH_MODE_LABELS[MatchMode.STANDARD])
        self.loose_btn = QPushButton(MATCH_MODE_LABELS[MatchMode.LOOSE])

        # Make buttons checkable and mutually exclusive
        self.strict_btn.setCheckable(True)
        self.standard_btn.setCheckable(True)
        self.loose_btn.setCheckable(True)

        # Set default checked
        self.standard_btn.setChecked(True)

        # Make buttons mutually exclusive
        self.strict_btn.setAutoExclusive(True)
        self.standard_btn.setAutoExclusive(True)
        self.loose_btn.setAutoExclusive(True)

        # Connect signals (placeholder methods, will be implemented in next stage)
        self.strict_btn.clicked.connect(lambda: self.on_match_mode_button_clicked(MatchMode.STRICT))
        self.standard_btn.clicked.connect(lambda: self.on_match_mode_button_clicked(MatchMode.STANDARD))
        self.loose_btn.clicked.connect(lambda: self.on_match_mode_button_clicked(MatchMode.LOOSE))

        modes_layout.addWidget(self.strict_btn)
        modes_layout.addWidget(self.standard_btn)
        modes_layout.addWidget(self.loose_btn)
        modes_layout.addStretch()

        main_layout.addLayout(modes_layout)

        # Advanced options (initially hidden)
        self.advanced_options_widget = QWidget(settings_group)  # Set parent
        advanced_layout = QVBoxLayout()
        self.advanced_options_widget.setLayout(advanced_layout)
        self.advanced_options_widget.setVisible(False)

        # Custom threshold slider
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Custom Threshold:"))

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(int(self.current_threshold * 100))
        self.threshold_slider.valueChanged.connect(self.on_custom_threshold_changed)

        self.threshold_label = QLabel(f"{int(self.current_threshold * 100)}%")
        self.threshold_label.setFixedWidth(40)

        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addStretch()

        advanced_layout.addLayout(threshold_layout)

        # Add note about custom threshold
        note_label = QLabel("Note: Adjusting custom threshold switches to Custom mode")
        note_label.setStyleSheet("color: gray; font-size: 10px;")
        advanced_layout.addWidget(note_label)

        main_layout.addWidget(self.advanced_options_widget)

        # Advanced options toggle button
        self.toggle_advanced_btn = QPushButton("Advanced Options ▼")
        self.toggle_advanced_btn.setCheckable(True)
        self.toggle_advanced_btn.clicked.connect(self.toggle_advanced_options)
        main_layout.addWidget(self.toggle_advanced_btn)

        return settings_group

    def toggle_advanced_options(self):
        """Toggle advanced options visibility"""
        # Use isHidden() instead of isVisible() to get the actual widget state
        # isVisible() returns False if parent is not visible
        is_hidden = self.advanced_options_widget.isHidden()
        new_visibility = is_hidden  # If hidden, make it visible
        self.advanced_options_widget.setVisible(new_visibility)
        self.toggle_advanced_btn.setText(
            "Advanced Options ▲" if new_visibility else "Advanced Options ▼"
        )

        # Adjust group box height based on visibility
        if new_visibility:
            self.advanced_options_widget.parent().setMaximumHeight(350)
        else:
            self.advanced_options_widget.parent().setMaximumHeight(250)

    def on_custom_threshold_changed(self, value: int):
        """
        Custom threshold slider value changed

        Args:
            value: Threshold percentage (0-100)
        """
        threshold = value / 100.0
        self.current_threshold = threshold
        self.threshold_label.setText(f"{value}%")

        # Switch to custom mode
        self.current_match_mode = MatchMode.CUSTOM

        # Uncheck preset buttons
        self.strict_btn.setChecked(False)
        self.standard_btn.setChecked(False)
        self.loose_btn.setChecked(False)

        # If search results exist, refresh table with new threshold
        if hasattr(self, 'current_batch_search_result') and self.current_batch_search_result:
            self.populate_batch_results_table(
                self.current_batch_search_result,
                min_similarity=self.current_threshold
            )

            # Update status bar
            total_matched = self.current_batch_search_result.get_match_count()
            self.statusBar().showMessage(
                f"Applied custom threshold ({threshold:.0%}), "
                f"{total_matched} songs have matches",
                5000
            )

        logger.info(f"Custom threshold changed to {threshold:.2%} (Custom mode)")

        # Save user preferences
        self.save_match_preferences()

    def on_match_mode_button_clicked(self, mode: MatchMode):
        """
        Match mode button clicked

        Args:
            mode: The selected match mode
        """
        self.set_match_mode(mode)

    def set_match_mode(self, mode: MatchMode):
        """
        Set match mode and refresh table if results exist

        Args:
            mode: Match mode enum (STRICT/STANDARD/LOOSE/CUSTOM)
        """
        self.current_match_mode = mode

        # Set threshold based on mode
        self.current_threshold = MATCH_THRESHOLDS.get(mode, DEFAULT_MATCH_THRESHOLD)

        # Update button states
        self.strict_btn.setChecked(mode == MatchMode.STRICT)
        self.standard_btn.setChecked(mode == MatchMode.STANDARD)
        self.loose_btn.setChecked(mode == MatchMode.LOOSE)

        # If search results exist, refresh table with filter
        if hasattr(self, 'current_batch_search_result') and self.current_batch_search_result:
            self.populate_batch_results_table(
                self.current_batch_search_result,
                min_similarity=self.current_threshold
            )

            # Update status bar
            total_matched = self.current_batch_search_result.get_match_count()
            self.statusBar().showMessage(
                f"Applied {mode.value} mode (≥{self.current_threshold:.0%}), "
                f"{total_matched} songs have matches",
                5000
            )
        else:
            # No results yet, just update status
            self.statusBar().showMessage(
                f"Match mode set to {mode.value} (≥{self.current_threshold:.0%})",
                3000
            )

        logger.info(f"Match mode changed to {mode.value} (threshold: {self.current_threshold:.2%})")

        # Save user preferences
        self.save_match_preferences()

    def load_match_preferences(self):
        """Load user match preferences from QSettings"""
        try:
            settings = QSettings("MusicDownloader", "BatchDownload")

            # Load match mode
            mode_str = settings.value("match_mode", DEFAULT_MATCH_MODE.value)
            try:
                self.current_match_mode = MatchMode(mode_str)
            except ValueError:
                self.current_match_mode = DEFAULT_MATCH_MODE

            # Load custom threshold
            custom_threshold = settings.value("custom_threshold", DEFAULT_MATCH_THRESHOLD)
            self.current_threshold = float(custom_threshold)

            # If custom mode, set threshold slider
            if self.current_match_mode == MatchMode.CUSTOM:
                self.threshold_slider.setValue(int(self.current_threshold * 100))
                self.threshold_label.setText(f"{int(self.current_threshold * 100)}%")

            # Update button states to match loaded mode
            if self.current_match_mode == MatchMode.STRICT:
                self.strict_btn.setChecked(True)
            elif self.current_match_mode == MatchMode.STANDARD:
                self.standard_btn.setChecked(True)
            elif self.current_match_mode == MatchMode.LOOSE:
                self.loose_btn.setChecked(True)
            # CUSTOM: none checked

            logger.info(f"Loaded match preferences: {self.current_match_mode.value} (threshold: {self.current_threshold:.2%})")

        except Exception as e:
            logger.error(f"Error loading match preferences: {e}")
            # Use defaults if loading fails
            self.current_match_mode = DEFAULT_MATCH_MODE
            self.current_threshold = DEFAULT_MATCH_THRESHOLD

    def save_match_preferences(self):
        """Save user match preferences to QSettings"""
        try:
            settings = QSettings("MusicDownloader", "BatchDownload")

            # Save match mode
            settings.setValue("match_mode", self.current_match_mode.value)

            # Save custom threshold (always save)
            settings.setValue("custom_threshold", self.current_threshold)

            logger.debug(f"Saved match preferences: {self.current_match_mode.value} (threshold: {self.current_threshold:.2%})")

        except Exception as e:
            logger.error(f"Error saving match preferences: {e}")


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('Music Downloader')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
