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
    def test_music_sources_shared_between_modes(self, qtbot):
        """Test music source selection is shared between single and batch modes"""
        from pyqt_ui.main import MainWindow

        window = MainWindow()
        qtbot.add_widget(window)
        
        # Check that source_group is accessible from window
        assert hasattr(window, 'source_group'), "Window should have source_group attribute"
        
        # Check that source_group is a QGroupBox
        from PyQt6.QtWidgets import QGroupBox
        assert isinstance(window.source_group, QGroupBox), "source_group should be a QGroupBox"
        
        # Check that select_all checkbox exists
        assert hasattr(window, 'select_all_cb'), "Window should have select_all_cb attribute"
        
        # Check that source_checkboxes dict exists and has entries
        assert hasattr(window, 'source_checkboxes'), "Window should have source_checkboxes"
        assert len(window.source_checkboxes) > 0, "Should have at least one source checkbox"
    def test_batch_results_table_exists(self, qtbot):
        """Test batch mode has a results table for displaying search results"""
        from pyqt_ui.main import MainWindow

        window = MainWindow()
        qtbot.add_widget(window)
        
        # Check that batch_results_table exists
        assert hasattr(window, 'batch_results_table'), "Window should have batch_results_table attribute"
        
        # Check that it's a QTableWidget
        from PyQt6.QtWidgets import QTableWidget
        assert isinstance(window.batch_results_table, QTableWidget), "batch_results_table should be a QTableWidget"
        
        # Check that it's initially hidden (like single mode results)
        assert not window.batch_results_table.isVisible(), "batch_results_table should be initially hidden"

