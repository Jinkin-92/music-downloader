"""Main Application Window"""
import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QHeaderView,
    QMenu, QMessageBox, QAbstractItemView, QTabWidget, QSlider
)
from PyQt6.QtGui import QFont, QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, pyqtSlot, QSettings
from .config import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, LOG_DIR, DOWNLOAD_DIR,
    SOURCE_LABELS, DEFAULT_SOURCES,
    MatchMode, DEFAULT_MATCH_MODE, DEFAULT_MATCH_THRESHOLD,
    MATCH_THRESHOLDS, MATCH_MODE_LABELS,
    SIMILARITY_COLORS, SIMILARITY_THRESHOLDS, BUTTON_STYLES, MENU_STYLES,
    BATCH_TABLE_HEADERS, SINGLE_TABLE_HEADERS, CHECKBOX_COL, INDEX_COL
)
from .workers import SearchWorker, DownloadWorker, BatchSearchWorker, ConcurrentSearchWorker, ConcurrentDownloadWorker
from .playlist.workers import PlaylistParseWorker
from .history_dialog import DownloadHistoryDialog
from backend.models.download_history import DownloadHistoryDB

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

        # Undo history for quick switch
        self.switch_history = []  # [(original_line, old_candidate, new_candidate), ...]
        self.max_history_size = 50

        # Download history database
        self.history_db = DownloadHistoryDB()

        self.setup_ui()

        # Setup keyboard shortcuts
        self.setup_shortcuts()

        # Load user preferences after UI is set up
        self.load_match_preferences()

    def setup_ui(self):
        """Setup basic UI"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1200, 800)

        # Setup menu bar
        self.setup_menu()

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

    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件 (&F)")

        # 下载历史
        history_action = QAction("下载历史 (&H)", self)
        history_action.setShortcut(QKeySequence("Ctrl+H"))
        history_action.triggered.connect(self.on_history_action)
        file_menu.addAction(history_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction("退出 (&X)", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        


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
        self.results_table.setColumnCount(len(SINGLE_TABLE_HEADERS))
        self.results_table.setHorizontalHeaderLabels(SINGLE_TABLE_HEADERS)
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

        # 🔄 Phase 4: 添加输入方式Tab切换
        # Tab 1: 📝 文本输入 (现有功能)
        # Tab 2: 🎵 歌单导入 (新增功能)
        self.input_tab_widget = QTabWidget()
        batch_layout.addWidget(self.input_tab_widget)

        # === Tab 1: 文本输入 ===
        text_input_tab = QWidget()
        text_input_layout = QVBoxLayout(text_input_tab)

        # 批量文本输入区域
        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText(
            "输入歌曲信息，每行一首:\n"
            "歌名 - 歌手\n"
            "例如:\n"
            "夜曲 - 周杰伦\n"
            "晴天 - 周杰伦"
        )
        self.batch_input.setMinimumHeight(200)
        text_input_layout.addWidget(self.batch_input)

        # 按钮区
        text_btn_layout = QHBoxLayout()
        self.batch_search_btn = QPushButton("批量搜索")
        self.batch_search_btn.setMinimumHeight(40)
        self.batch_search_btn.clicked.connect(self.on_batch_search_clicked)
        text_btn_layout.addWidget(self.batch_search_btn)

        self.clear_text_btn = QPushButton("清空")
        self.clear_text_btn.setMinimumHeight(40)
        self.clear_text_btn.clicked.connect(self.on_clear_text_input)
        text_btn_layout.addWidget(self.clear_text_btn)

        text_btn_layout.addStretch()
        text_input_layout.addLayout(text_btn_layout)
        text_input_layout.addStretch()

        self.input_tab_widget.addTab(text_input_tab, "📝 文本输入")

        # === Tab 2: 歌单导入 (新增) ===
        playlist_import_tab = QWidget()
        playlist_layout = QVBoxLayout(playlist_import_tab)

        # URL输入区
        url_input_layout = QHBoxLayout()
        url_input_layout.addWidget(QLabel("歌单链接:"))

        self.playlist_url_input = QLineEdit()
        self.playlist_url_input.setPlaceholderText(
            "粘贴网易云/QQ音乐歌单链接...\n"
            "例如: https://music.163.com/m/playlist?id=13210897452"
        )
        url_input_layout.addWidget(self.playlist_url_input)

        self.parse_playlist_btn = QPushButton("解析歌单")
        self.parse_playlist_btn.setMinimumHeight(40)
        self.parse_playlist_btn.clicked.connect(self.on_parse_playlist)
        url_input_layout.addWidget(self.parse_playlist_btn)

        playlist_layout.addLayout(url_input_layout)

        # 支持平台提示
        support_label = QLabel("💡 支持平台: 网易云音乐、QQ音乐")
        support_label.setStyleSheet("color: gray; font-size: 11px; padding: 5px;")
        playlist_layout.addWidget(support_label)

        # 解析状态
        self.playlist_status_label = QLabel()
        self.playlist_status_label.setStyleSheet("padding: 10px; border-radius: 5px;")
        self.playlist_status_label.setWordWrap(True)
        playlist_layout.addWidget(self.playlist_status_label)

        # === 解析结果表格（独立显示区）===
        self.playlist_parsed_table = QTableWidget()
        self.playlist_parsed_table.setColumnCount(4)  # 歌名、歌手、专辑、时长
        self.playlist_parsed_table.setHorizontalHeaderLabels(["歌名", "歌手", "专辑", "时长"])
        self.playlist_parsed_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.playlist_parsed_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.playlist_parsed_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.playlist_parsed_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.playlist_parsed_table.setMinimumHeight(200)
        self.playlist_parsed_table.setVisible(False)
        playlist_layout.addWidget(self.playlist_parsed_table)

        # === 歌单Tab专用的批量搜索按钮 ===
        self.playlist_batch_search_btn = QPushButton("批量搜索")
        self.playlist_batch_search_btn.setMinimumHeight(40)
        self.playlist_batch_search_btn.setEnabled(False)
        self.playlist_batch_search_btn.clicked.connect(self.on_playlist_batch_search_clicked)
        playlist_layout.addWidget(self.playlist_batch_search_btn)

        playlist_layout.addStretch()
        self.input_tab_widget.addTab(playlist_import_tab, "🎵 歌单导入")

        # === 批量匹配设置 (两个Tab共享) ===

        # Match settings group (collapsible)
        match_settings_group = self.setup_batch_match_settings_ui()
        batch_layout.addWidget(match_settings_group)

        # Add stretch to push content to top
        
        # Batch Results Table
        self.batch_results_table = QTableWidget()
        self.batch_results_table.setColumnCount(len(BATCH_TABLE_HEADERS))
        self.batch_results_table.setHorizontalHeaderLabels(BATCH_TABLE_HEADERS)
        self.batch_results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.batch_results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.batch_results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.batch_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.batch_results_table.setColumnWidth(0, 40)
        self.batch_results_table.setColumnWidth(1, 50)
        self.batch_results_table.setVisible(False)

        # ✅ 为相似度列添加工具提示（第6列）
        # 注意：需要在表格显示后才能获取表头项，所以在populate_batch_results_table()中处理
        batch_layout.addWidget(self.batch_results_table)

        # 批量操作按钮组（全选、反选）
        batch_actions_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setMinimumHeight(35)
        self.select_all_btn.clicked.connect(self.on_batch_select_all)
        self.select_all_btn.setEnabled(False)

        self.invert_selection_btn = QPushButton("反选")
        self.invert_selection_btn.setMinimumHeight(35)
        self.invert_selection_btn.clicked.connect(self.on_batch_invert_selection)
        self.invert_selection_btn.setEnabled(False)

        batch_actions_layout.addWidget(self.select_all_btn)
        batch_actions_layout.addWidget(self.invert_selection_btn)
        batch_layout.addLayout(batch_actions_layout)

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
    def on_clear_text_input(self):
        """清空文本输入框"""
        self.batch_input.clear()
        self.statusBar().showMessage('已清空输入', 2000)

    @pyqtSlot()
    def on_parse_playlist(self):
        """解析歌单链接"""
        url = self.playlist_url_input.text().strip()

        if not url:
            self.update_playlist_status("请输入歌单链接", "error")
            return

        # 禁用解析按钮
        self.parse_playlist_btn.setEnabled(False)
        self.parse_playlist_btn.setText("解析中...")
        self.update_playlist_status("正在解析歌单，请稍候...", "info")

        # 创建并启动解析Worker
        self.playlist_parse_worker = PlaylistParseWorker(url)
        self.playlist_parse_worker.progress.connect(self.on_playlist_parse_progress)
        self.playlist_parse_worker.finished.connect(self.on_playlist_parsed)
        self.playlist_parse_worker.error.connect(self.on_playlist_parse_error)
        self.playlist_parse_worker.start()

    @pyqtSlot(str)
    def on_playlist_parse_progress(self, message):
        """歌单解析进度更新"""
        self.update_playlist_status(message, "info")

    @pyqtSlot(list)
    def on_playlist_parsed(self, songs):
        """歌单解析完成"""
        if not songs:
            self.update_playlist_status("歌单为空或解析失败", "error")
            self.parse_playlist_btn.setEnabled(True)
            self.parse_playlist_btn.setText("解析歌单")
            return

        # 更新状态
        self.update_playlist_status(
            f"✅ 解析成功！共找到 {len(songs)} 首歌曲\n"
            f"来源: {songs[0].source_platform if songs else '未知'}\n"
            f"⏳ 请点击下方 '批量搜索' 按钮进行匹配",
            "success"
        )

        # 填充歌单解析结果表格（独立的表格，不是批量搜索结果表格）
        self.add_songs_to_playlist_table(songs)

        # 恢复解析按钮
        self.parse_playlist_btn.setEnabled(True)
        self.parse_playlist_btn.setText("解析歌单")

        # 显示歌单解析结果表格
        self.playlist_parsed_table.setVisible(True)

        # ⚠️ 修复问题1：启用歌单Tab的批量搜索按钮（不是文本输入Tab的按钮）
        self.playlist_batch_search_btn.setEnabled(True)

    @pyqtSlot(str)
    def on_playlist_parse_error(self, error_msg):
        """歌单解析错误"""
        self.update_playlist_status(
            f"❌ 解析失败: {error_msg}\n"
            f"请检查链接是否正确，或尝试其他歌单。",
            "error"
        )
        self.parse_playlist_btn.setEnabled(True)
        self.parse_playlist_btn.setText("解析歌单")

    def update_playlist_status(self, message, status_type):
        """更新歌单解析状态显示

        Args:
            message: 状态消息
            status_type: 状态类型 ("success", "error", "info")
        """
        self.playlist_status_label.setText(message)

        # 根据类型设置样式
        if status_type == "success":
            self.playlist_status_label.setStyleSheet(
                "padding: 10px; border-radius: 5px; "
                "background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;"
            )
        elif status_type == "error":
            self.playlist_status_label.setStyleSheet(
                "padding: 10px; border-radius: 5px; "
                "background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;"
            )
        else:  # info
            self.playlist_status_label.setStyleSheet(
                "padding: 10px; border-radius: 5px; "
                "background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb;"
            )

    def add_songs_to_playlist_table(self, songs):
        """将歌曲添加到歌单解析结果表格（独立的表格）

        这个表格只显示解析结果，不包含checkbox和匹配功能

        Args:
            songs: PlaylistSong对象列表
        """
        from pyqt_ui.playlist.base import PlaylistSong

        if not songs:
            return

        # 清空现有表格
        self.playlist_parsed_table.setRowCount(0)

        # 添加歌曲到表格
        for row, song in enumerate(songs):
            self.playlist_parsed_table.insertRow(row)

            # 列0: 歌名
            song_name_item = QTableWidgetItem(song.song_name)
            self.playlist_parsed_table.setItem(row, 0, song_name_item)

            # 列1: 歌手
            singer_item = QTableWidgetItem(song.singers)
            self.playlist_parsed_table.setItem(row, 1, singer_item)

            # 列2: 专辑
            album_item = QTableWidgetItem(song.album if song.album else "-")
            self.playlist_parsed_table.setItem(row, 2, album_item)

            # 列3: 时长
            duration_item = QTableWidgetItem(song.duration if song.duration else "-")
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playlist_parsed_table.setItem(row, 3, duration_item)

        # 存储解析的歌曲列表供后续批量搜索使用
        self._parsed_playlist_songs = songs

    def add_songs_to_batch_table(self, songs):
        """将歌曲添加到批量表格

        Args:
            songs: PlaylistSong对象列表
        """
        from pyqt_ui.playlist.base import PlaylistSong

        if not songs:
            return

        # 清空现有表格
        self.batch_results_table.setRowCount(0)

        # 添加歌曲到表格
        for row, song in enumerate(songs):
            self.batch_results_table.insertRow(row)

            # 创建匹配格式字符串
            match_format = song.to_match_format()

            # 列0: Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Checked)

            # 存储歌曲信息
            song_data = {
                'original_text': match_format,
                'song_name': song.song_name,
                'artist': song.singers,
                'album': song.album,
                'from_playlist': True,
                'source_platform': song.source_platform
            }
            checkbox_item.setData(Qt.ItemDataRole.UserRole, song_data)

            self.batch_results_table.setItem(row, 0, checkbox_item)

            # 列1: 序号
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.batch_results_table.setItem(row, 1, num_item)

            # 列2: 歌名 - 歌手
            song_item = QTableWidgetItem(match_format)
            self.batch_results_table.setItem(row, 2, song_item)

            # 列3: 来源平台
            source_item = QTableWidgetItem(song.source_platform)
            source_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.batch_results_table.setItem(row, 3, source_item)

            # 列4: 专辑（可选）
            album_item = QTableWidgetItem(song.album)
            self.batch_results_table.setItem(row, 4, album_item)

            # 列5: 时长（可选）
            duration_item = QTableWidgetItem(song.duration)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.batch_results_table.setItem(row, 5, duration_item)

            # 列6-8: 占位（匹配源、相似度、文件大小）
            for col in range(6, 9):
                placeholder = QTableWidgetItem("")
                self.batch_results_table.setItem(row, col, placeholder)

        # 调整列宽
        self.batch_results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.batch_results_table.setColumnWidth(0, 40)
        self.batch_results_table.setColumnWidth(1, 50)
        self.batch_results_table.setColumnWidth(5, 80)

        self.statusBar().showMessage(
            f'已加载 {len(songs)} 首歌曲到表格，请点击"批量搜索"开始匹配',
            5000
        )

    @pyqtSlot()
    def on_playlist_batch_search_clicked(self):
        """处理歌单导入Tab的批量搜索按钮点击

        这个方法从解析的歌单表格中读取歌曲，执行批量搜索，
        然后将搜索结果显示在共享的批量结果表格中
        """
        # 检查是否有解析的歌曲
        if not hasattr(self, '_parsed_playlist_songs') or not self._parsed_playlist_songs:
            self.update_playlist_status(
                "❌ 没有可搜索的歌曲，请先解析歌单",
                "error"
            )
            return

        # 从解析的歌曲列表生成批量文本
        batch_text = "\n".join([
            song.to_match_format()
            for song in self._parsed_playlist_songs
        ])

        # Get selected sources
        selected_sources = [
            source for source, cb in self.source_checkboxes.items()
            if cb.isChecked()
        ]

        if not selected_sources:
            self.statusBar().showMessage('Please select at least one source', 3000)
            return

        # Disable playlist batch search button
        self.playlist_batch_search_btn.setEnabled(False)
        self.parse_playlist_btn.setEnabled(False)

        # Update playlist status
        self.update_playlist_status(
            f"🔍 正在搜索 {len(self._parsed_playlist_songs)} 首歌曲...",
            "info"
        )

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setVisible(True)
        self.status_label.setText(f"Searching {len(self._parsed_playlist_songs)} songs...")
        self.batch_results_table.setVisible(True)

        # Create and start concurrent batch search worker
        self.batch_search_worker = ConcurrentSearchWorker(
            batch_text=batch_text,
            sources=selected_sources,
            search_all_sources=True,
            max_candidates_per_source=5
        )
        self.batch_search_worker.search_started.connect(self.on_batch_search_started)
        self.batch_search_worker.search_progress.connect(self.on_batch_search_progress)
        self.batch_search_worker.search_finished.connect(self.on_playlist_batch_search_finished)
        self.batch_search_worker.search_error.connect(self.on_playlist_batch_search_error)
        self.batch_search_worker.start()

    @pyqtSlot()
    def on_batch_search_clicked(self):
        """Handle batch search button click"""
        # 🔄 Phase 4: 支持从歌单导入的表格数据进行匹配

        # 检查表格中是否已有歌曲（来自歌单导入）
        table_row_count = self.batch_results_table.rowCount()
        has_playlist_songs = table_row_count > 0

        # 准备批量文本
        batch_text = ""

        if has_playlist_songs:
            # 从表格中提取歌曲信息
            songs_from_table = []
            for row in range(table_row_count):
                checkbox_item = self.batch_results_table.item(row, 0)
                if checkbox_item:
                    song_data = checkbox_item.data(Qt.ItemDataRole.UserRole)
                    if song_data and 'original_text' in song_data:
                        songs_from_table.append(song_data['original_text'])

            batch_text = "\n".join(songs_from_table)

            # 提示用户正在使用表格中的歌曲进行匹配
            self.statusBar().showMessage(
                f'使用表格中的 {len(songs_from_table)} 首歌曲进行匹配...',
                3000
            )
        else:
            # 从文本输入框读取
            batch_text = self.batch_input.toPlainText().strip()
            if not batch_text:
                self.statusBar().showMessage('请输入歌曲列表或导入歌单', 3000)
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
        if not has_playlist_songs:
            self.batch_input.setEnabled(False)

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setVisible(True)
        self.status_label.setText("Preparing batch search...")
        self.batch_results_table.setVisible(True)

        # Create and start concurrent batch search worker
        self.batch_search_worker = ConcurrentSearchWorker(
            batch_text=batch_text,
            sources=selected_sources,
            search_all_sources=True,
            max_candidates_per_source=5
        )
        self.batch_search_worker.search_started.connect(self.on_batch_search_started)
        self.batch_search_worker.search_progress.connect(self.on_batch_search_progress)
        self.batch_search_worker.search_finished.connect(self.on_batch_search_finished)
        self.batch_search_worker.search_error.connect(self.on_batch_search_error)
        self.batch_search_worker.start()

    def on_batch_search_started(self):
        """Handle batch search started"""
        self.statusBar().showMessage('Batch search in progress...')

    @pyqtSlot(str, int, int)
    def on_batch_search_progress(self, message, current, total):
        """Handle batch search progress update"""
        self.status_label.setText(message)
        # Update progress bar if we have total count
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)

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

        # Populate batch results table with current threshold setting
        self.populate_batch_results_table(
            search_result,
            min_similarity=self.current_threshold
        )

        total_matched = search_result.get_match_count()
        total_songs = search_result.total_songs

        # ✅ 添加使用提示
        if total_songs > 0:
            hint_msg = (
                f"批量搜索完成: {total_matched}/{total_songs} 首歌曲匹配 | "
                f"提示: 点击相似度列的 ▼ 按钮可切换到其他搜索结果"
            )
            self.statusBar().showMessage(hint_msg, 8000)
        else:
            self.statusBar().showMessage('批量搜索完成: 未找到匹配', 5000)

    @pyqtSlot(str)
    def on_batch_search_error(self, error_msg):
        """Handle batch search error"""
        self.batch_search_btn.setEnabled(True)
        self.batch_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.statusBar().showMessage(error_msg, 5000)

    @pyqtSlot(object)
    def on_playlist_batch_search_finished(self, search_result):
        """处理歌单批量搜索完成 - 显示搜索结果"""
        # Re-enable playlist controls
        self.playlist_batch_search_btn.setEnabled(True)
        self.parse_playlist_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)

        # Store result for later use (e.g., match switching)
        self.current_batch_search_result = search_result

        # Populate batch results table with current threshold setting
        self.populate_batch_results_table(
            search_result,
            min_similarity=self.current_threshold
        )

        total_matched = search_result.get_match_count()
        total_songs = search_result.total_songs

        # 更新歌单状态显示
        if total_matched > 0:
            self.update_playlist_status(
                f"✅ 批量搜索完成！找到 {total_matched}/{total_songs} 首歌曲的匹配\n"
                f"💡 提示: 在下方搜索结果表格中选择歌曲，然后点击 'Download Selected' 下载",
                "success"
            )
        else:
            self.update_playlist_status(
                f"❌ 批量搜索完成，但未找到匹配\n"
                f"💡 建议: 尝试调整匹配阈值或选择更多音乐源",
                "error"
            )

        # 启用批量操作按钮（全选、反选、下载）
        self.select_all_btn.setEnabled(True)
        self.invert_selection_btn.setEnabled(True)
        self.batch_download_btn.setEnabled(True)

        # Status bar message
        if total_songs > 0:
            hint_msg = (
                f"批量搜索完成: {total_matched}/{total_songs} 首歌曲匹配 | "
                f"提示: 点击相似度列的 ▼ 按钮可切换到其他搜索结果"
            )
            self.statusBar().showMessage(hint_msg, 8000)
        else:
            self.statusBar().showMessage('批量搜索完成: 未找到匹配', 5000)

    @pyqtSlot(str)
    def on_playlist_batch_search_error(self, error_msg):
        """处理歌单批量搜索错误"""
        self.playlist_batch_search_btn.setEnabled(True)
        self.parse_playlist_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)

        self.update_playlist_status(
            f"❌ 批量搜索失败: {error_msg}\n"
            f"💡 建议: 检查网络连接或稍后重试",
            "error"
        )

        self.statusBar().showMessage(f"搜索失败: {error_msg}", 5000)


    def on_batch_download_clicked(self):
        """Handle batch download button click"""
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
        from core import MatchSource

        # search_result is BatchSearchResult object
        total_songs = search_result.total_songs
        matches = search_result.matches

        self.batch_results_table.setRowCount(total_songs)
        self.batch_results_table.setVisible(True)

        # ✅ 为相似度列标题添加工具提示
        similarity_header_item = self.batch_results_table.horizontalHeaderItem(6)
        if similarity_header_item is None:
            # 如果表头项不存在，先创建它们
            self.batch_results_table.setHorizontalHeaderLabels(BATCH_TABLE_HEADERS)
            similarity_header_item = self.batch_results_table.horizontalHeaderItem(6)

        if similarity_header_item:
            similarity_header_item.setToolTip(
                "相似度说明\n\n"
                "点击 ▼ 按钮切换到其他搜索结果\n\n"
                "颜色含义：\n"
                "• 绿色 (≥80%): 高度匹配\n"
                "• 黄色 (60-79%): 中等匹配\n"
                "• 红色 (<60%): 低匹配，建议手动确认"
            )

        # Enable batch download button if there are results
        if search_result.get_match_count() > 0:
            self.batch_download_btn.setEnabled(True)
            self.select_all_btn.setEnabled(True)
            self.invert_selection_btn.setEnabled(True)

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

                # ⚠️ 为403错误的多源fallback添加备用候选列表
                # 将all_matches转换为字典格式存储
                all_matches_dict = {
                    source: [c.to_dict() for c in candidates]
                    for source, candidates in song_match.all_matches.items()
                }

                # 在song_dict中添加备用候选列表（排除当前源）
                song_dict['_fallback_candidates'] = [
                    candidate_dict
                    for source, candidates in all_matches_dict.items()
                    if source != song_match.current_source  # 排除当前源
                    for candidate_dict in candidates
                    # 按相似度降序排列（已在get_all_candidates中排序）
                ]

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

                # Similarity column with quick switch button
                similarity_widget = QWidget()
                similarity_layout = QHBoxLayout(similarity_widget)
                similarity_layout.setContentsMargins(4, 2, 4, 2)

                # Similarity label
                similarity_value = song_match.current_match.similarity_score
                similarity_text = f"{similarity_value:.2%}"

                similarity_label = QLabel(similarity_text)
                similarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Color based on similarity
                if similarity_value >= SIMILARITY_THRESHOLDS["high"]:
                    similarity_label.setStyleSheet(f"color: {SIMILARITY_COLORS['high']};")
                elif similarity_value >= SIMILARITY_THRESHOLDS["medium"]:
                    similarity_label.setStyleSheet(f"color: {SIMILARITY_COLORS['medium']};")
                else:
                    similarity_label.setStyleSheet(f"color: {SIMILARITY_COLORS['low']};")

                # Mark if below threshold
                if similarity_value < min_similarity:
                    font = similarity_label.font()
                    font.setItalic(True)
                    similarity_label.setFont(font)

                similarity_layout.addWidget(similarity_label)

                # Quick switch button (if multiple candidates from current source)
                current_source_candidates = song_match.get_all_candidates_from_current_source()

                if len(current_source_candidates) > 1:
                    # Create quick switch button
                    num_candidates = len(current_source_candidates)

                    # Button style based on candidate count
                    if num_candidates > 10:
                        btn_text = f"▼{num_candidates}"
                        btn_style = BUTTON_STYLES["many_candidates"]
                        btn_min_size = (50, 22)
                    elif num_candidates > 3:
                        btn_text = f"▼{num_candidates}"
                        btn_style = BUTTON_STYLES["medium_candidates"]
                        btn_min_size = (45, 22)
                    else:
                        btn_text = "▼"
                        btn_style = BUTTON_STYLES["few_candidates"]
                        btn_min_size = (22, 22)

                    quick_switch_btn = QPushButton(btn_text)
                    quick_switch_btn.setMinimumSize(*btn_min_size)
                    # ✅ 添加清晰的工具提示
                    quick_switch_btn.setToolTip(
                        f"点击切换到其他搜索结果\n"
                        f"当前源 ({song_match.current_source}) 有 {num_candidates} 个候选\n"
                        f"右键点击查看所有源的候选"
                    )

                    # Apply button style
                    quick_switch_btn.setStyleSheet(btn_style)

                    # Connect click event
                    quick_switch_btn.clicked.connect(
                        lambda checked, line=original_line, btn=quick_switch_btn:
                            self.show_quick_switch_menu(line, btn)
                    )

                    similarity_layout.addWidget(quick_switch_btn)

                similarity_layout.addStretch()

                # Set widget to table
                self.batch_results_table.setCellWidget(row, 6, similarity_widget)

            else:
                # No match found (similarity < 0.6) but show best candidate if available
                checkbox_item.setData(Qt.ItemDataRole.UserRole, original_line)

                # 检查是否有任何候选（即使相似度 < 0.6）
                all_candidates = []
                for candidates in song_match.all_matches.values():
                    all_candidates.extend(candidates)

                if all_candidates:
                    # ✅ 直接显示最佳候选（即使低于阈值）
                    best_candidate = max(all_candidates, key=lambda x: x.similarity_score)

                    # 设置为当前匹配（标记为用户可选）
                    song_match.current_match = best_candidate
                    song_match.current_source = best_candidate.source
                    # 保持 has_match=False，表示未达到自动匹配标准

                    # 准备歌曲字典
                    song_dict = best_candidate.to_dict()

                    # ⚠️ 为403错误的多源fallback添加备用候选列表
                    all_matches_dict = {
                        source: [c.to_dict() for c in candidates]
                        for source, candidates in song_match.all_matches.items()
                    }

                    # 添加备用候选列表（排除当前源）
                    song_dict['_fallback_candidates'] = [
                        candidate_dict
                        for source, candidates in all_matches_dict.items()
                        if source != best_candidate.source  # 排除当前源
                        for candidate_dict in candidates
                    ]

                    checkbox_item.setData(Qt.ItemDataRole.UserRole, song_dict)
                    checkbox_item.setData(Qt.ItemDataRole.UserRole + 1, song_dict)

                    # 显示歌曲信息（与已匹配歌曲相同的显示方式）
                    self.batch_results_table.setItem(
                        row, 2, QTableWidgetItem(best_candidate.song_name)
                    )

                    self.batch_results_table.setItem(
                        row, 3, QTableWidgetItem(best_candidate.singers)
                    )

                    self.batch_results_table.setItem(
                        row, 4, QTableWidgetItem(best_candidate.album)
                    )

                    # Source
                    source = best_candidate.source.replace('MusicClient', '')
                    self.batch_results_table.setItem(row, 5, QTableWidgetItem(source))

                    # Similarity column - 红色粗体标记低相似度
                    similarity_widget = QWidget()
                    similarity_layout = QHBoxLayout(similarity_widget)
                    similarity_layout.setContentsMargins(4, 2, 4, 2)

                    similarity_value = best_candidate.similarity_score
                    similarity_text = f"{similarity_value:.2%} (低匹配)"

                    similarity_label = QLabel(similarity_text)
                    similarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # ✅ 红色粗体标记
                    similarity_label.setStyleSheet("color: red; font-weight: bold;")

                    similarity_layout.addWidget(similarity_label)

                    # ✅ 正常显示快速切换按钮（让用户可以查看其他候选）
                    current_source_candidates = song_match.get_all_candidates_from_current_source()
                    if len(current_source_candidates) > 1:
                        quick_switch_btn = QPushButton("▼")
                        quick_switch_btn.setMaximumWidth(30)
                        quick_switch_btn.setToolTip("点击切换到其他搜索结果")
                        quick_switch_btn.clicked.connect(
                            lambda _, line=original_line: self.show_quick_switch_menu(line, quick_switch_btn)
                        )
                        similarity_layout.addWidget(quick_switch_btn)

                    similarity_layout.addStretch()

                    # Set widget to table
                    self.batch_results_table.setCellWidget(row, 6, similarity_widget)
                else:
                    # ❌ 完全没有搜索结果
                    self.batch_results_table.setItem(
                        row, 2, QTableWidgetItem(song_match.query['name'])
                    )

                    self.batch_results_table.setItem(
                        row, 3, QTableWidgetItem(song_match.query['singer'])
                    )

                    self.batch_results_table.setItem(row, 4, QTableWidgetItem(""))

                    # Source - show "Not Found"
                    self.batch_results_table.setItem(row, 5, QTableWidgetItem("Not Found"))

                    # Similarity - show "N/A"
                    self.batch_results_table.setItem(row, 6, QTableWidgetItem("N/A"))

                # Action button (retry search) - add to a new column if needed, or skip for now
                # For now, we'll skip the retry button to focus on quick switch feature

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
        """Start download with concurrent worker thread"""
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
        self.status_label.setText(f"准备下载: {song_name} 等 {len(songs)} 首歌曲...")

        # Start concurrent download worker
        self.download_worker = ConcurrentDownloadWorker(
            songs=songs,
            download_dir=str(DOWNLOAD_DIR),
            max_retries=2
        )
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

        # ⚠️ 修复问题3：检查实际下载结果
        song_count = len(songs)

        if song_count == 0:
            # 所有歌曲都下载失败
            QMessageBox.critical(
                self,
                "Download Failed",
                "❌ 下载失败：没有成功下载任何歌曲。\n\n"
                "可能的原因：\n"
                "• 歌曲尚未进行批量搜索匹配\n"
                "• 所选音乐源没有找到匹配的歌曲\n"
                "• 网络连接问题\n\n"
                "请先点击 '批量搜索' 进行匹配，然后再下载。"
            )
            self.statusBar().showMessage('Download failed: 0 songs downloaded', 5000)
            logger.error("Download failed: 0 successful songs")
        else:
            # 部分或全部成功
            # TODO: 未来可以从Worker获取总歌曲数和失败数，显示更详细的信息
            QMessageBox.information(
                self,
                "Download Complete",
                f"✅ 成功下载 {song_count} 首歌曲！\n\n"
                f"文件保存位置: musicdl_outputs/"
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
            from core import MatchSource
            song_match.switch_to_candidate(new_candidate, MatchSource.USER_SELECTED)

            # Refresh the batch results table
            self.populate_batch_results_table(self.current_batch_search_result)

            self.statusBar().showMessage(
                f"Switched match: {new_candidate.song_name} - {new_candidate.singers}", 3000
            )

    def show_quick_switch_menu(self, original_line: str, button: QPushButton):
        """
        Display quick switch menu (candidates from current source + all sources)

        Args:
            original_line: Original input line (song identifier)
            button: Trigger button (used to position menu)
        """
        if not hasattr(self, "current_batch_search_result"):
            return

        song_match = self.current_batch_search_result.matches.get(original_line)
        if not song_match:
            return

        # Create menu
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLES)

        # ===== Current Source Candidates =====
        current_source = song_match.current_source
        current_candidates = song_match.get_all_candidates_from_current_source()

        # Sort by similarity (descending)
        current_candidates_sorted = sorted(
            current_candidates,
            key=lambda x: x.similarity_score,
            reverse=True
        )

        # Add menu title for current source
        title_action = menu.addAction(
            f"[{current_source}] {len(current_candidates)} candidates"
        )
        title_action.setEnabled(False)

        menu.addSeparator()

        # Add current source candidate items
        for candidate in current_candidates_sorted:
            # Check if this is the current match
            is_current = (
                song_match.current_match and
                candidate.song_name == song_match.current_match.song_name and
                candidate.singers == song_match.current_match.singers and
                candidate.source == song_match.current_match.source
            )

            # Create menu item
            text = (
                f"{candidate.song_name} - {candidate.singers} "
                f"({candidate.similarity_score:.2%})"
            )

            action = menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(is_current)

            # If current, make it bold
            if is_current:
                font = action.font()
                font.setBold(True)
                action.setFont(font)

            # Connect switch event
            action.triggered.connect(
                lambda checked, c=candidate: self.quick_switch_to_candidate(
                    original_line, c
                )
            )

        # ===== All Sources Candidates (Cross-Source) =====
        menu.addSeparator()

        # Add "All Sources" submenu
        all_sources_menu = menu.addMenu("All Sources (by similarity)")

        # Get all candidates from all sources
        all_candidates = song_match.get_all_candidates()

        # Sort by similarity (descending)
        all_candidates_sorted = sorted(
            all_candidates,
            key=lambda x: x.similarity_score,
            reverse=True
        )

        # Limit display count (avoid menu too long)
        max_display = 15
        display_candidates = all_candidates_sorted[:max_display]

        for candidate in display_candidates:
            # Check if this is the current match
            is_current = (
                song_match.current_match and
                candidate.song_name == song_match.current_match.song_name and
                candidate.singers == song_match.current_match.singers and
                candidate.source == song_match.current_match.source
            )

            # Create menu item with source mark
            source_short = candidate.source.replace('MusicClient', '')
            text = (
                f"{candidate.song_name} - {candidate.singers} "
                f"[{source_short}] ({candidate.similarity_score:.2%})"
            )

            action = all_sources_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(is_current)

            if is_current:
                font = action.font()
                font.setBold(True)
                action.setFont(font)

            # Connect switch event
            action.triggered.connect(
                lambda checked, c=candidate: self.quick_switch_to_candidate(
                    original_line, c
                )
            )

        # If there are more candidates, show tip
        if len(all_candidates) > max_display:
            tip_action = all_sources_menu.addAction(
                f"... {len(all_candidates) - max_display} more candidates"
            )
            tip_action.setEnabled(False)

        # Show menu (below button)
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def quick_switch_to_candidate(self, original_line: str, new_candidate):
        """
        Quick switch to specified candidate (via menu)

        Args:
            original_line: Original input line
            new_candidate: Candidate to switch to
        """
        if not hasattr(self, "current_batch_search_result"):
            QMessageBox.warning(self, "Error", "No batch search results found")
            return

        song_match = self.current_batch_search_result.matches.get(original_line)
        if not song_match:
            return

        # Record old candidate (for undo)
        old_candidate = song_match.current_match

        # Perform switch
        from core import MatchSource
        song_match.switch_to_candidate(new_candidate, MatchSource.USER_SELECTED)

        # Add to undo history
        self._add_to_undo_history(original_line, old_candidate, new_candidate)

        # Refresh table (with current threshold if set)
        current_threshold = getattr(self, 'current_threshold', 0.0)
        self.populate_batch_results_table(
            self.current_batch_search_result,
            min_similarity=current_threshold
        )

        # Update status bar
        source_short = new_candidate.source.replace('MusicClient', '')
        self.statusBar().showMessage(
            f"Switched to: {new_candidate.song_name} - {new_candidate.singers} "
            f"({source_short}, {new_candidate.similarity_score:.2%})",
            4000
        )

    def _add_to_undo_history(self, original_line: str, old_candidate, new_candidate):
        """
        Add switch operation to history

        Args:
            original_line: Original input line
            old_candidate: Previous candidate
            new_candidate: New candidate
        """
        self.switch_history.append((original_line, old_candidate, new_candidate))

        # Limit history size
        if len(self.switch_history) > self.max_history_size:
            self.switch_history.pop(0)

    def undo_last_switch(self):
        """Undo last quick switch operation"""
        if not self.switch_history:
            QMessageBox.information(self, "Undo", "No operations to undo")
            return

        original_line, old_candidate, new_candidate = self.switch_history.pop()

        # Check if batch search result still exists
        if not hasattr(self, "current_batch_search_result"):
            QMessageBox.warning(self, "Error", "Batch search results not found")
            return

        song_match = self.current_batch_search_result.matches.get(original_line)
        if not song_match:
            QMessageBox.warning(self, "Error", "Song match information not found")
            return

        # Revert to old candidate
        from core import MatchSource
        song_match.switch_to_candidate(old_candidate, MatchSource.USER_SELECTED)

        # Refresh table
        current_threshold = getattr(self, 'current_threshold', 0.0)
        self.populate_batch_results_table(
            self.current_batch_search_result,
            min_similarity=current_threshold
        )

        # Update status bar
        self.statusBar().showMessage(
            f"Undo: Switched back to {old_candidate.song_name} - {old_candidate.singers}",
            3000
        )

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for batch download"""
        # Ctrl+Z: Undo last switch
        self.undo_shortcut = QShortcut(
            QKeySequence("Ctrl+Z"),
            self
        )
        self.undo_shortcut.activated.connect(self.undo_last_switch)

        # Note: Ctrl+K for quick switch could be added here
        # but requires tracking which row is currently selected

    @pyqtSlot()
    def on_history_action(self):
        """Open download history dialog"""
        try:
            dialog = DownloadHistoryDialog(self.history_db, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"打开下载历史失败：{e}")
            QMessageBox.critical(
                self,
                "错误",
                f"打开下载历史失败:\n{e}"
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

    @pyqtSlot()
    def on_batch_select_all(self):
        """全选：选中批量结果表格中的所有歌曲"""
        for row in range(self.batch_results_table.rowCount()):
            checkbox_item = self.batch_results_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Checked)

        # 更新状态栏
        total_rows = self.batch_results_table.rowCount()
        self.statusBar().showMessage(f"已选中全部 {total_rows} 首歌曲", 3000)
        logger.debug(f"Select All: Checked {total_rows} rows")

    @pyqtSlot()
    def on_batch_invert_selection(self):
        """反选：切换批量结果表格中所有歌曲的选中状态"""
        checked_count = 0
        unchecked_count = 0

        for row in range(self.batch_results_table.rowCount()):
            checkbox_item = self.batch_results_table.item(row, 0)
            if checkbox_item:
                current_state = checkbox_item.checkState()
                # 切换状态：选中→未选中，未选中→选中
                new_state = (Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked
                            else Qt.CheckState.Checked)
                checkbox_item.setCheckState(new_state)

                if new_state == Qt.CheckState.Checked:
                    checked_count += 1
                else:
                    unchecked_count += 1

        # 更新状态栏
        self.statusBar().showMessage(
            f"反选完成：已选中 {checked_count} 首，未选中 {unchecked_count} 首",
            3000
        )
        logger.debug(f"Invert Selection: {checked_count} checked, {unchecked_count} unchecked")


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('Music Downloader')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
