"""
E2E 测试套件全局重置脚本
清空下载历史数据库与测试下载目录，保证套件可重复执行。
仅清理测试夹具目录 test_downloads/ 与测试产生的下载历史，不影响真实下载记录（真实下载目录不在清理范围）。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.models.download_history import DownloadHistoryDB  # noqa: E402

# 1. 清空下载历史数据库
history = DownloadHistoryDB()
records = history.get_all_records()
for r in records:
    history.delete_record(r.id)
print(f"[reset] 下载历史已清空: {len(records)} 条")

# 2. 清理测试下载目录（仅测试夹具目录）
dl_dir = ROOT / "test_downloads"
if dl_dir.exists():
    removed = 0
    for f in dl_dir.iterdir():
        if f.is_file():
            f.unlink()
            removed += 1
    print(f"[reset] 测试下载目录已清理: {removed} 个文件")
else:
    print("[reset] 测试下载目录不存在，跳过")
