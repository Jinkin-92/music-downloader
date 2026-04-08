import unittest
from unittest.mock import Mock, patch

from backend.api.download import _is_downloadable_song, _search_download_candidates


class DownloadPlaceholderSkipRegressionTest(unittest.TestCase):
    def test_unmatched_placeholder_row_is_not_downloadable(self):
        self.assertFalse(_is_downloadable_song({
            'song_name': '未找到',
            'singers': '-',
            'source': '-',
        }))

    def test_valid_pjmp3_match_is_downloadable(self):
        self.assertTrue(_is_downloadable_song({
            'song_name': '山海',
            'singers': '草东没有派对',
            'source': 'Pjmp3Client',
            'song_id': '123',
        }))

    def test_pjmp3_fallback_prefers_artist_filtered_search(self):
        fake_client = Mock()
        fake_client.search_with_artist_filter.return_value = [
            Mock(song_name='山海', singers='草东没有派对')
        ]

        with patch('backend.api.download.music_downloader._pjmp3_client', fake_client), \
             patch('backend.api.download.music_downloader._pjmp3_songinfo_to_dict', return_value={'song_name': '山海'}), \
             patch('backend.api.download.music_downloader.search') as generic_search:
            results = _search_download_candidates('山海', '草东没有派对', 'Pjmp3Client')

        fake_client.search_with_artist_filter.assert_called_once_with(
            song_name='山海',
            artist='草东没有派对',
            limit=20
        )
        generic_search.assert_not_called()
        self.assertEqual(results, {'Pjmp3Client': [{'song_name': '山海'}]})


if __name__ == '__main__':
    unittest.main()
