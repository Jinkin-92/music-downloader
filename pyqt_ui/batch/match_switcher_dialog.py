"""匹配结果切换对话框"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QTabWidget,
    QWidget,
    QAbstractItemView,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from .models import MatchCandidate, BatchSongMatch


class MatchSwitcherDialog(QDialog):
    """匹配结果切换对话框"""

    match_changed = pyqtSignal(str, MatchCandidate)

    def __init__(self, song_match: BatchSongMatch, parent=None):
        super().__init__(parent)
        self.song_match = song_match
        self.current_candidate = song_match.current_match
        self.selected_candidate = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(
            f"切换匹配结果 - {self.song_match.query['name']} - {self.song_match.query['singer']}"
        )
        self.setMinimumSize(900, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 查询信息
        query_info = QLabel(
            f"<b>查询:</b> {self.song_match.query['name']} - {self.song_match.query['singer']}"
        )
        layout.addWidget(query_info)

        # 当前匹配信息
        if self.current_candidate:
            current_info = QLabel(
                f"<b>当前匹配:</b> {self.current_candidate.song_name} - {self.current_candidate.singers} "
                f"(来源: {self.current_candidate.source}, 相似度: {self.current_candidate.similarity_score:.2%})"
            )
            current_info.setStyleSheet(
                "background-color: #d4edda; padding: 8px; border-radius: 4px;"
            )
            layout.addWidget(current_info)
        else:
            no_match_info = QLabel("<b>当前无匹配结果</b>")
            no_match_info.setStyleSheet(
                "background-color: #f8d7da; padding: 8px; border-radius: 4px;"
            )
            layout.addWidget(no_match_info)

        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tab 1: 按源分组
        self.setup_by_source_tab()

        # Tab 2: 跨源排序
        self.setup_all_candidates_tab()

        # 按钮区域
        button_layout = QHBoxLayout()

        self.preview_btn = QPushButton("预览当前选择")
        self.preview_btn.clicked.connect(self.on_preview)
        button_layout.addWidget(self.preview_btn)

        self.select_btn = QPushButton("切换到此匹配")
        self.select_btn.clicked.connect(self.on_select)
        self.select_btn.setEnabled(False)
        button_layout.addWidget(self.select_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def setup_by_source_tab(self):
        """设置按源分组的Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.by_source_table = QTableWidget()
        self.by_source_table.setColumnCount(6)
        self.by_source_table.setHorizontalHeaderLabels(
            ["☐", "歌名", "歌手", "专辑", "时长", "相似度"]
        )
        self.by_source_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.by_source_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.by_source_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.by_source_table.setColumnWidth(0, 40)
        self.by_source_table.cellClicked.connect(self.on_by_source_cell_clicked)

        # 填充数据
        for source, candidates in self.song_match.all_matches.items():
            if not candidates:
                continue

            # 添加源标题行
            title_row = self.by_source_table.rowCount()
            self.by_source_table.insertRow(title_row)
            source_label_item = QTableWidgetItem(f"【{source}】{len(candidates)}个匹配")
            source_label_item.setBackground(Qt.GlobalColor.lightGray)
            source_label_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.by_source_table.setItem(title_row, 0, source_label_item)
            self.by_source_table.setSpan(title_row, 0, 1, 6)

            # 添加候选结果
            for candidate in candidates:
                row = self.by_source_table.rowCount()
                self.by_source_table.insertRow(row)

                # Checkbox
                checkbox_item = QTableWidgetItem()
                checkbox_item.setData(Qt.ItemDataRole.UserRole, candidate)
                self.by_source_table.setItem(row, 0, checkbox_item)

                # 歌名
                self.by_source_table.setItem(
                    row, 1, QTableWidgetItem(candidate.song_name)
                )

                # 歌手
                self.by_source_table.setItem(
                    row, 2, QTableWidgetItem(candidate.singers)
                )

                # 专辑
                self.by_source_table.setItem(row, 3, QTableWidgetItem(candidate.album))

                # 时长
                self.by_source_table.setItem(
                    row, 4, QTableWidgetItem(candidate.duration)
                )

                # 相似度
                similarity_item = QTableWidgetItem(f"{candidate.similarity_score:.2%}")
                similarity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if candidate.similarity_score >= 0.8:
                    similarity_item.setForeground(Qt.GlobalColor.darkGreen)
                elif candidate.similarity_score >= 0.6:
                    similarity_item.setForeground(Qt.GlobalColor.darkYellow)
                else:
                    similarity_item.setForeground(Qt.GlobalColor.red)

                self.by_source_table.setItem(row, 5, similarity_item)

                # 如果是当前选中的，高亮显示
                if (
                    self.current_candidate
                    and candidate.song_info_obj == self.current_candidate.song_info_obj
                ):
                    self.by_source_table.selectRow(row)

        layout.addWidget(self.by_source_table)
        self.tab_widget.addTab(tab, "按源分组")

    def setup_all_candidates_tab(self):
        """设置所有候选结果的Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.all_candidates_table = QTableWidget()
        self.all_candidates_table.setColumnCount(7)
        self.all_candidates_table.setHorizontalHeaderLabels(
            ["☐", "歌名", "歌手", "专辑", "来源", "时长", "相似度"]
        )
        self.all_candidates_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.all_candidates_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.all_candidates_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.all_candidates_table.setColumnWidth(0, 40)
        self.all_candidates_table.cellClicked.connect(
            self.on_all_candidates_cell_clicked
        )

        # 获取所有候选并按相似度排序
        all_candidates = self.song_match.get_all_candidates()

        for candidate in all_candidates:
            row = self.all_candidates_table.rowCount()
            self.all_candidates_table.insertRow(row)

            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setData(Qt.ItemDataRole.UserRole, candidate)
            self.all_candidates_table.setItem(row, 0, checkbox_item)

            # 歌名
            self.all_candidates_table.setItem(
                row, 1, QTableWidgetItem(candidate.song_name)
            )

            # 歌手
            self.all_candidates_table.setItem(
                row, 2, QTableWidgetItem(candidate.singers)
            )

            # 专辑
            self.all_candidates_table.setItem(row, 3, QTableWidgetItem(candidate.album))

            # 来源
            source_item = QTableWidgetItem(candidate.source.replace("MusicClient", ""))
            source_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.all_candidates_table.setItem(row, 4, source_item)

            # 时长
            self.all_candidates_table.setItem(
                row, 5, QTableWidgetItem(candidate.duration)
            )

            # 相似度
            similarity_item = QTableWidgetItem(f"{candidate.similarity_score:.2%}")
            similarity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if candidate.similarity_score >= 0.8:
                similarity_item.setForeground(Qt.GlobalColor.darkGreen)
            elif candidate.similarity_score >= 0.6:
                similarity_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                similarity_item.setForeground(Qt.GlobalColor.red)

            self.all_candidates_table.setItem(row, 6, similarity_item)

            # 如果是当前选中的，高亮显示
            if (
                self.current_candidate
                and candidate.song_info_obj == self.current_candidate.song_info_obj
            ):
                self.all_candidates_table.selectRow(row)

        layout.addWidget(self.all_candidates_table)
        self.tab_widget.addTab(tab, "所有候选（按相似度排序）")

    def on_by_source_cell_clicked(self, row, column):
        """处理按源分组表格点击"""
        item = self.by_source_table.item(row, 0)
        if not item:
            return

        candidate = item.data(Qt.ItemDataRole.UserRole)
        if candidate:
            self.selected_candidate = candidate
            self.select_btn.setEnabled(True)
            self.update_preview_text(candidate)

    def on_all_candidates_cell_clicked(self, row, column):
        """处理所有候选表格点击"""
        item = self.all_candidates_table.item(row, 0)
        if not item:
            return

        candidate = item.data(Qt.ItemDataRole.UserRole)
        if candidate:
            self.selected_candidate = candidate
            self.select_btn.setEnabled(True)
            self.update_preview_text(candidate)

    def update_preview_text(self, candidate: MatchCandidate):
        """更新预览文本"""
        preview_text = (
            f"<b>歌名:</b> {candidate.song_name}<br>"
            f"<b>歌手:</b> {candidate.singers}<br>"
            f"<b>专辑:</b> {candidate.album}<br>"
            f"<b>来源:</b> {candidate.source.replace('MusicClient', '')}<br>"
            f"<b>时长:</b> {candidate.duration}<br>"
            f"<b>文件大小:</b> {candidate.file_size}<br>"
            f"<b>格式:</b> {candidate.ext}<br>"
            f"<b>相似度:</b> {candidate.similarity_score:.2%}"
        )
        self.preview_btn.setText(
            f"预览当前选择\n({candidate.song_name} - {candidate.singers})"
        )
        self.preview_btn.setToolTip(preview_text)

    def on_preview(self):
        """预览当前选择"""
        if self.selected_candidate:
            preview_text = (
                f"<b>歌名:</b> {self.selected_candidate.song_name}<br>"
                f"<b>歌手:</b> {self.selected_candidate.singers}<br>"
                f"<b>专辑:</b> {self.selected_candidate.album}<br>"
                f"<b>来源:</b> {self.selected_candidate.source.replace('MusicClient', '')}<br>"
                f"<b>时长:</b> {self.selected_candidate.duration}<br>"
                f"<b>文件大小:</b> {self.selected_candidate.file_size}<br>"
                f"<b>格式:</b> {self.selected_candidate.ext}<br>"
                f"<b>相似度:</b> {self.selected_candidate.similarity_score:.2%}"
            )
            QMessageBox.information(self, "预览匹配结果", preview_text)

    def on_select(self):
        """选择切换到此匹配"""
        if self.selected_candidate:
            self.match_changed.emit(
                self.song_match.query["original_line"], self.selected_candidate
            )
            self.accept()
