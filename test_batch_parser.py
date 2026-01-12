"""Test batch parser functionality"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_batch_parser():
    """Test BatchParser.parse() method"""
    print("Testing BatchParser...")

    # Test 1: Basic parsing
    test_input = """没关系 - 容祖儿
告白气球 - 周杰伦"""

    try:
        from pyqt_ui.batch import BatchParser
        results = BatchParser.parse(test_input)

        assert len(results) == 2, f"Expected 2 songs, got {len(results)}"
        assert results[0]['name'] == '没关系', f"Expected '没关系', got {results[0]['name']}"
        assert results[0]['singer'] == '容祖儿', f"Expected '容祖儿', got {results[0]['singer']}"

        print("✓ BatchParser test PASSED")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("  (Expected - module not implemented yet)")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Batch Parser Test")
    print("=" * 50)
    test_batch_parser()
    print("=" * 50)
