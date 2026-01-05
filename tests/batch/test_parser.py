"""BatchParser tests"""
import pytest


class TestBatchParser:
    """Test BatchParser.parse() method"""

    def test_parse_empty_input(self):
        """Test parsing empty input"""
        from pyqt_ui.batch import BatchParser

        with pytest.raises(ValueError):
            BatchParser.parse("")

    def test_parse_single_song_with_dash(self):
        """Test parsing single song with dash separator"""
        from pyqt_ui.batch import BatchParser

        text = "七里香 - 周杰伦"
        result = BatchParser.parse(text)

        assert len(result) == 1
        assert result[0]['name'] == '七里香'
        assert result[0]['singer'] == '周杰伦'
        assert result[0]['original_line'] == text

    def test_parse_exceeds_limit(self):
        """Test parsing more than 200 songs"""
        from pyqt_ui.batch import BatchParser

        # Generate 201 songs
        text = "\n".join([f"Song{i} - Singer{i}" for i in range(201)])

        with pytest.raises(ValueError, match="Exceeds maximum"):
            BatchParser.parse(text)

    def test_parse_invalid_format_no_dash(self):
        """Test parsing without dash separator"""
        from pyqt_ui.batch import BatchParser

        text = "InvalidInputWithoutSeparator"

        with pytest.raises(ValueError, match="Cannot parse line 1"):
            BatchParser.parse(text)
