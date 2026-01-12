"""真实下载测试：验证文件实际下载位置"""
import logging
from pathlib import Path
from pyqt_ui.music_downloader import MusicDownloader
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_download():
    print("="*80)
    print("真实下载测试：验证文件实际位置")
    print("="*80)

    default_dir = Path("musicdl_outputs")
    custom_dir = Path("test_real_custom_download")
    custom_dir.mkdir(exist_ok=True)

    print(f"\n默认目录: {default_dir.absolute()}")
    print(f"自定义目录: {custom_dir.absolute()}")

    # Test with custom directory
    print("\n测试: 下载到自定义目录")
    downloader = MusicDownloader()

    print("  步骤1: 搜索歌曲...")
    try:
        results = downloader.search("七里香", sources=["QQMusicClient"])
        if results and results.get("QQMusicClient"):
            song = results["QQMusicClient"][0]
            print(f"    找到: {song.get('song_name')} - {song.get('singers')}")

            print("  步骤2: 下载到自定义目录...")
            downloader.download([song], download_dir=custom_dir)

            print("  步骤3: 检查文件位置...")
            time.sleep(3)

            if custom_dir.exists():
                files = list(custom_dir.glob("*"))
                print(f"    自定义目录中的文件 ({len(files)} 个):")
                for f in files:
                    print(f"      - {f.name}")

            if default_dir.exists():
                files_default = list(default_dir.glob("*"))
                print(f"    默认目录中的文件 ({len(files_default)} 个):")
                for f in files_default:
                    print(f"      - {f.name}")
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_real_download()
