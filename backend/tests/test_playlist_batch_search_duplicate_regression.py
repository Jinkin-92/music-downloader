import unittest
from unittest.mock import patch

from backend.api.playlist import (
    PlaylistBatchSearchRequest,
    start_batch_search_background,
)
from backend.api.task_manager import task_manager


class PlaylistBatchSearchDuplicateRegressionTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        task_manager._tasks.clear()

    async def test_returns_completed_task_when_duplicate_filter_skips_all_songs(self):
        request = PlaylistBatchSearchRequest(
            songs=[{
                'name': '夜曲',
                'artist': '周杰伦',
                'album': '',
            }],
            sources=['QQ音乐'],
            concurrency=5,
            filter_duplicates=True,
            similarity_threshold=0.6,
        )

        with patch('backend.api.playlist.history_service.check_duplicate', return_value=True):
            response = await start_batch_search_background(request)

        self.assertEqual(response['status'], 'completed')
        self.assertEqual(response['total'], 0)

        task = task_manager.get_task_dict(response['task_id'])
        self.assertIsNotNone(task)
        self.assertEqual(task['status'], 'completed')
        self.assertEqual(task['result']['total'], 0)
        self.assertEqual(task['result']['matched'], 0)
        self.assertEqual(task['result']['matches'], {})
        self.assertEqual(len(task['result']['skipped_songs']), 1)
        self.assertEqual(task['result']['skipped_songs'][0]['name'], '夜曲')
        self.assertEqual(task['result']['skipped_songs'][0]['artist'], '周杰伦')


if __name__ == '__main__':
    unittest.main()
