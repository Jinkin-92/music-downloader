"""BatchSearchWorker tests"""
import pytest
from PyQt6.QtCore import QThreadPool
from pyqt_ui.workers import BatchSearchWorker


class TestBatchSearchWorker:
    """Test BatchSearchWorker thread"""

    def test_batch_search_worker_creation(self, qtbot):
        """Test BatchSearchWorker can be instantiated"""
        batch_text = "七里香 - 周杰伦\n夜曲 - 周杰伦"
        sources = ['QQMusicClient']

        worker = BatchSearchWorker(batch_text, sources)

        assert worker.batch_text == batch_text
        assert worker.sources == sources
        assert hasattr(worker, 'downloader')
        assert hasattr(worker, 'parser')
        assert hasattr(worker, 'matcher')

    def test_batch_search_worker_signals(self, qtbot):
        """Test BatchSearchWorker has required signals"""
        batch_text = "测试 - 测试"
        sources = ['NeteaseMusicClient']

        worker = BatchSearchWorker(batch_text, sources)

        # Check all required signals exist
        assert hasattr(worker, 'search_started')
        assert hasattr(worker, 'search_progress')
        assert hasattr(worker, 'search_finished')
        assert hasattr(worker, 'search_error')
