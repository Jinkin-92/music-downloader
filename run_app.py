#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐下载器启动脚本
替代批处理文件，避免编码问题
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """检查依赖"""
    print("=== Music Downloader Startup ===")
    print()
    
    # 检查Python版本
    print(f"[1/4] Python version: {sys.version}")
    if sys.version_info < (3, 7):
        print("[ERROR] Python 3.7+ required")
        return False
    
    # 检查PyQt6
    print("[2/4] Checking PyQt6...")
    try:
        import PyQt6
        print(f"  PyQt6 version: {PyQt6.Qt.PYQT_VERSION_STR}")
    except ImportError:
        print("[ERROR] PyQt6 not installed. Run: pip install PyQt6")
        return False
    
    # 检查musicdl
    print("[3/4] Checking musicdl...")
    try:
        import musicdl
        print("  musicdl: OK")
    except ImportError:
        print("[ERROR] musicdl not installed. Run: pip install musicdl")
        return False
    
    # 检查文件
    print("[4/4] Checking files...")
    required_files = [
        'pyqt_ui/main.py',
        'pyqt_ui/workers.py',
        'pyqt_ui/batch/models.py',
        'pyqt_ui/batch/match_switcher_dialog.py',
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"[ERROR] {file} not found!")
            return False
        print(f"  {file}: OK")
    
    print()
    print("[SUCCESS] All checks passed!")
    print()
    return True


def main():
    """主函数"""
    if not check_dependencies():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("Starting Music Downloader...")
    print("=" * 50)
    print()
    
    try:
        from PyQt6.QtWidgets import QApplication
        from pyqt_ui.main import MainWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"\n[ERROR] Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == '__main__':
    main()
