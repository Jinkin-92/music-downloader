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

