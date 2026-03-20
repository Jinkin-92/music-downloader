"""Download History Dialog - 下载历史管理对话框

提供下载历史查看和管理功能:
- 显示所有下载记录
- 文件存在性验证
- 清理缺失记录
- 打开文件所在文件夹
- 删除记录和文件
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QMessageBox, QHeaderView,
    QAbstractItemView, QDialogButtonBox, QMenu, QWidget
)
from PyQt6.QtCore import Qt, pyqtSlot, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QAction

from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VerifyWorker(QThread):
    """文件验证工作线程"""
    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(dict)  # stats: {total, valid, missing}
    error = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db

    def run(self):
        try:
            stats = self.db.verify_all_files()
            self.finished.emit(stats)
        except Exception as e:
            self.error.emit(str(e))


class DownloadHistoryDialog(QDialog):
    """下载历史管理对话框"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.verify_worker = None
        self.current_records = []

        # 动画相关
        self._progress_anim = None
        self._status_anim = None
        self._ellipsis_timer = None
        self._ellipsis_count = 0
        self._status_text = ""

        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("下载历史管理")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题和统计信息
        header_layout = QHBoxLayout()
        self.title_label = QLabel("<h2>下载历史记录</h2>")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: gray; padding: 5px;")
        header_layout.addWidget(self.stats_label)
        layout.addLayout(header_layout)

        # 操作按钮组
        button_layout = QHBoxLayout()

        self.verify_btn = QPushButton("🔍 验证文件状态")
        self.verify_btn.setMinimumHeight(35)
        self.verify_btn.clicked.connect(self.on_verify_clicked)
        button_layout.addWidget(self.verify_btn)

        self.clean_btn = QPushButton("🧹 清理缺失记录")
        self.clean_btn.setMinimumHeight(35)
        self.clean_btn.clicked.connect(self.on_clean_clicked)
        button_layout.addWidget(self.clean_btn)

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setMinimumHeight(35)
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        button_layout.addWidget(self.refresh_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            '☐', '#', '歌曲名', '歌手', '文件路径', '来源', '相似度', '下载时间'
        ])
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)

        # 设置列宽
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Index
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Song name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Singer
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # File path
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Source
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Similarity
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Download time

        self.history_table.setColumnWidth(0, 40)
        self.history_table.setColumnWidth(1, 50)
        self.history_table.setColumnWidth(5, 80)
        self.history_table.setColumnWidth(6, 70)
        self.history_table.setColumnWidth(7, 150)

        # 启用右键菜单
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.history_table)

        # 底部按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # 状态栏提示
        self.statusBar_label = QLabel("💡 提示: 右键点击记录可删除文件或打开文件夹")
        self.statusBar_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.statusBar_label)

        # 初始化动画
        self._setup_animations()

    def _setup_animations(self):
        """设置加载动画"""
        # 进度条淡入动画
        self._progress_anim = QPropertyAnimation(self.progress_bar, b"maximumWidth")
        self._progress_anim.setDuration(300)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # 状态标签淡入动画（使用透明度效果）
        self._status_anim = QPropertyAnimation(self.status_label, b"maximumHeight")
        self._status_anim.setDuration(300)
        self._status_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # 动画省略号计时器
        self._ellipsis_timer = QTimer(self)
        self._ellipsis_timer.timeout.connect(self._update_ellipsis)

    def _update_ellipsis(self):
        """更新省略号动画"""
        self._ellipsis_count = (self._ellipsis_count + 1) % 4
        dots = "." * self._ellipsis_count
        self.status_label.setText(f"{self._status_text}{dots}")

    def _start_loading_animation(self, text: str):
        """开始加载动画"""
        self._status_text = text
        self._ellipsis_count = 0
        self._ellipsis_timer.start(500)  # 每500ms更新一次

        # 淡入效果
        self._fade_in_widget(self.progress_bar)
        self._fade_in_widget(self.status_label)

    def _stop_loading_animation(self):
        """停止加载动画"""
        self._ellipsis_timer.stop()

        # 淡出效果
        self._fade_out_widget(self.progress_bar)
        self._fade_out_widget(self.status_label)

    def _fade_in_widget(self, widget: QWidget):
        """淡入显示控件"""
        widget.setVisible(True)
        # 使用样式表动画效果
        widget.setStyleSheet("""
            QProgressBar, QLabel {
                animation: fadeIn 300ms ease-out;
            }
        """)

    def _fade_out_widget(self, widget: QWidget):
        """淡出隐藏控件"""
        widget.setVisible(False)

    @pyqtSlot()
    def load_history(self):
        """加载下载历史"""
        try:
            self.current_records = self.db.get_all_records(include_missing=True)
            self.populate_table()
            self.update_stats()
        except Exception as e:
            logger.error(f"加载下载历史失败：{e}")
            QMessageBox.critical(self, "错误", f"加载下载历史失败:\n{e}")

    def populate_table(self):
        """填充表格"""
        self.history_table.setRowCount(0)

        # 空状态提示
        if len(self.current_records) == 0:
            self.statusBar_label.setText("💡 暂无下载记录，下载歌曲后将自动记录")
            return

        for row, record in enumerate(self.current_records):
            self.history_table.insertRow(row)

            # 列 0: Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            checkbox_item.setData(Qt.ItemDataRole.UserRole, record.id)
            self.history_table.setItem(row, 0, checkbox_item)

            # 列 1: 序号
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(row, 1, num_item)

            # 列 2: 歌曲名
            song_name_item = QTableWidgetItem(record.song_name)
            self.history_table.setItem(row, 2, song_name_item)

            # 列 3: 歌手
            singer_item = QTableWidgetItem(record.singers)
            self.history_table.setItem(row, 3, singer_item)

            # 列 4: 文件路径
            file_path_item = QTableWidgetItem(record.file_path)
            file_path_item.setToolTip(record.file_path)
            self.history_table.setItem(row, 4, file_path_item)

            # 列 5: 来源
            source = record.source.replace('MusicClient', '') if record.source else '-'
            source_item = QTableWidgetItem(source)
            source_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(row, 5, source_item)

            # 列 6: 相似度
            sim_item = QTableWidgetItem(f"{record.similarity:.1%}" if record.similarity else '-')
            sim_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(row, 6, sim_item)

            # 列 7: 下载时间
            time_str = record.download_time.strftime('%Y-%m-%d %H:%M:%S') if record.download_time else '-'
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(row, 7, time_item)

            # 文件不存在时标记
            if not record.file_exists:
                for col in range(2, 8):
                    item = self.history_table.item(row, col)
                    if item:
                        item.setForeground(Qt.GlobalColor.gray)

    def update_stats(self):
        """更新统计信息"""
        total = len(self.current_records)
        valid = sum(1 for r in self.current_records if r.file_exists)
        missing = total - valid

        self.stats_label.setText(f"总计：{total} | 有效：{valid} | 缺失：{missing}")

        # 根据缺失率设置颜色
        missing_rate = missing / total if total > 0 else 0
        if missing_rate > 0.1:
            self.stats_label.setStyleSheet("color: red;")
        elif missing > 0:
            self.stats_label.setStyleSheet("color: orange;")
        else:
            self.stats_label.setStyleSheet("color: green;")

    @pyqtSlot()
    def on_verify_clicked(self):
        """验证文件状态"""
        self.verify_btn.setEnabled(False)
        self.clean_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)  # 不确定进度

        # 使用动画显示加载状态
        self._start_loading_animation("正在验证文件是否存在")

        self.verify_worker = VerifyWorker(self.db)
        self.verify_worker.finished.connect(self.on_verify_finished)
        self.verify_worker.error.connect(self.on_verify_error)
        self.verify_worker.start()

    @pyqtSlot(dict)
    def on_verify_finished(self, stats):
        """验证完成"""
        self.verify_btn.setEnabled(True)
        self.clean_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)

        # 停止动画
        self._stop_loading_animation()

        self.statusBar_label.setText(
            f"✅ 验证完成：共 {stats['total']} 条记录，有效 {stats['valid']} 条，缺失 {stats['missing']} 条"
        )

        # 重新加载历史以更新显示
        self.load_history()

        if stats['missing'] > 0:
            QMessageBox.warning(
                self,
                "发现缺失文件",
                f"发现 {stats['missing']} 条记录对应的文件已丢失。\n"
                f"点击\"🧹 清理缺失记录\"按钮可清理这些记录。"
            )

    @pyqtSlot(str)
    def on_verify_error(self, error_msg):
        """验证错误"""
        self.verify_btn.setEnabled(True)
        self.clean_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)

        # 停止动画
        self._stop_loading_animation()

        QMessageBox.critical(self, "验证失败", f"文件验证失败:\n{error_msg}")

    @pyqtSlot()
    def on_refresh_clicked(self):
        """刷新"""
        self.load_history()
        self.statusBar_label.setText("✅ 已刷新")

    @pyqtSlot()
    def on_clean_clicked(self):
        """清理缺失记录"""
        missing_count = sum(1 for r in self.current_records if not r.file_exists)

        if missing_count == 0:
            QMessageBox.information(self, "无需清理", "没有缺失文件的记录。")
            return

        reply = QMessageBox.question(
            self,
            "确认清理",
            f"确定要清理 {missing_count} 条缺失文件的记录吗？\n\n此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted = self.db.clean_missing_records()
                QMessageBox.information(
                    self,
                    "清理完成",
                    f"已清理 {deleted} 条缺失记录。"
                )
                self.load_history()
            except Exception as e:
                QMessageBox.critical(self, "清理失败", f"清理记录失败:\n{e}")

    def show_context_menu(self, pos):
        """显示右键菜单"""
        row = self.history_table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)

        # 打开文件夹
        open_folder_action = QAction("📂 打开文件所在文件夹", self)
        open_folder_action.triggered.connect(lambda: self.open_folder(row))
        menu.addAction(open_folder_action)

        # 选中文件
        select_file_action = QAction("📁 选中文件", self)
        select_file_action.triggered.connect(lambda: self.select_file(row))
        menu.addAction(select_file_action)

        menu.addSeparator()

        # 删除记录（保留文件）
        delete_record_action = QAction("🗑️ 删除记录 (保留文件)", self)
        delete_record_action.triggered.connect(lambda: self.delete_record(row, delete_file=False))
        menu.addAction(delete_record_action)

        # 删除记录和文件
        delete_all_action = QAction("⚠️ 删除记录和文件", self)
        delete_all_action.triggered.connect(lambda: self.delete_record(row, delete_file=True))
        menu.addAction(delete_all_action)

        menu.exec_(self.history_table.mapToGlobal(pos))

    def open_folder(self, row):
        """打开文件所在文件夹"""
        import subprocess
        import platform

        record = self.current_records[row]
        path = Path(record.file_path)

        if not path.exists():
            QMessageBox.warning(self, "文件不存在", "文件已丢失，无法打开文件夹。")
            return

        try:
            if platform.system() == 'Windows':
                subprocess.run(['explorer', str(path.parent)], check=False)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', str(path.parent)], check=False)
            else:
                subprocess.run(['xdg-open', str(path.parent)], check=False)
        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"打开文件夹失败:\n{e}")

    def select_file(self, row):
        """在文件管理器中选中文件"""
        import subprocess
        import platform

        record = self.current_records[row]
        path = Path(record.file_path)

        if not path.exists():
            QMessageBox.warning(self, "文件不存在", "文件已丢失。")
            return

        try:
            if platform.system() == 'Windows':
                subprocess.run(['explorer', '/select,', str(path)], check=False)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', '-R', str(path)], check=False)
            else:
                # Linux: 只打开文件夹
                subprocess.run(['xdg-open', str(path.parent)], check=False)
        except Exception as e:
            QMessageBox.critical(self, "操作失败", f"选中文件失败:\n{e}")

    def delete_record(self, row, delete_file=False):
        """删除记录

        Args:
            row: 表格行号
            delete_file: 是否同时删除文件
        """
        record = self.current_records[row]

        if delete_file:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除以下记录和文件吗？\n\n"
                f"歌曲：{record.song_name} - {record.singers}\n"
                f"文件：{record.file_path}\n\n"
                f"⚠️ 此操作不可恢复!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self,
                "确认删除记录",
                f"确定要删除以下记录吗？(文件将保留)\n\n"
                f"歌曲：{record.song_name} - {record.singers}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 删除文件
            if delete_file:
                path = Path(record.file_path)
                if path.exists():
                    path.unlink()

            # 删除记录
            self.db.delete_record(record.id)

            # 从表格中移除
            self.history_table.removeRow(row)
            self.current_records.pop(row)

            # 重新编号
            for i in range(row, self.history_table.rowCount()):
                self.history_table.setItem(i, 1, QTableWidgetItem(str(i + 1)))

            self.update_stats()
            self.statusBar_label.setText(f"✅ 已删除: {record.song_name} - {record.singers}")

        except Exception as e:
            QMessageBox.critical(self, "删除失败", f"删除失败:\n{e}")
