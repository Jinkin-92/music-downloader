"""Test download path selection feature"""
import pytest
from PyQt6.QtWidgets import QLabel, QPushButton
from pyqt_ui.main import MainWindow


class TestDownloadPathSelection:
    """Test download path selection UI and functionality"""

    def test_download_path_label_exists(self, qtbot):
        """Test that download path label exists in batch mode"""
        window = MainWindow()
        qtbot.add_widget(window)

        # Check if download path label exists
        assert hasattr(window, 'download_path_label'), "MainWindow should have download_path_label"
        assert isinstance(window.download_path_label, QLabel), "download_path_label should be QLabel"

    def test_select_path_button_exists(self, qtbot):
        """Test that select path button exists"""
        window = MainWindow()
        qtbot.add_widget(window)

        # Check if select path button exists
        assert hasattr(window, 'select_path_btn'), "MainWindow should have select_path_btn"
        assert isinstance(window.select_path_btn, QPushButton), "select_path_btn should be QPushButton"
