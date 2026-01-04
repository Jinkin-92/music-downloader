"""MainWindow tab widget tests"""
import pytest


class TestMainWindowTabs:
    """Test QTabWidget implementation in MainWindow"""

    def test_main_window_has_tab_widget(self, qtbot):
        """Test MainWindow has QTabWidget"""
        from pyqt_ui.main import MainWindow

        window = MainWindow()
        qtbot.add_widget(window)
        assert hasattr(window, 'mode_tab_widget')
    def test_single_mode_tab_exists(self, qtbot):
        """Test single mode tab exists with correct label"""
        from pyqt_ui.main import MainWindow

        window = MainWindow()
        qtbot.add_widget(window)
        
        # Check that at least one tab exists
        assert window.mode_tab_widget.count() >= 1, "No tabs found"
        
        # Check first tab label
        assert window.mode_tab_widget.tabText(0) == "单曲下载", f"Expected '单曲下载', got '{window.mode_tab_widget.tabText(0)}'"
    def test_batch_mode_tab_exists(self, qtbot):
        """Test batch mode tab exists with correct label"""
        from pyqt_ui.main import MainWindow

        window = MainWindow()
        qtbot.add_widget(window)
        
        # Check that at least 2 tabs exist
        assert window.mode_tab_widget.count() >= 2, f"Expected at least 2 tabs, got {window.mode_tab_widget.count()}"
        
        # Check second tab label
        assert window.mode_tab_widget.tabText(1) == "批量下载", f"Expected '批量下载', got '{window.mode_tab_widget.tabText(1)}'"
        
        # Check that batch tab has a text input area
        assert hasattr(window, 'batch_input'), "Window should have batch_input attribute"

