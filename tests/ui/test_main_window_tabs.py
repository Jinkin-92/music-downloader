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
