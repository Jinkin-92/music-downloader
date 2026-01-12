#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整验证应用启动（不显示GUI）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("Music Downloader - Startup Verification")
    print("=" * 60)
    print()
    
    # 步骤1: 检查Python版本
    print("[Step 1/6] Python Version Check")
    print(f"  Version: {sys.version}")
    print(f"  Executable: {sys.executable}")
    if sys.version_info < (3, 7):
        print("  [FAIL] Requires Python 3.7+")
        return False
    print("  [PASS]")
    print()
    
    # 步骤2: 检查依赖
    print("[Step 2/6] Dependencies Check")
    try:
        import PyQt6
        from PyQt6.QtCore import PYQT_VERSION_STR
        print(f"  PyQt6: {PYQT_VERSION_STR} [PASS]")
    except ImportError as e:
        print(f"  PyQt6: [FAIL] - {e}")
        return False
    
    try:
        import musicdl
        print(f"  musicdl: [PASS]")
    except ImportError as e:
        print(f"  musicdl: [FAIL] - {e}")
        return False
    print()
    
    # 步骤3: 检查文件存在
    print("[Step 3/6] Files Check")
    required_files = [
        'pyqt_ui/main.py',
        'pyqt_ui/workers.py',
        'pyqt_ui/batch/models.py',
        'pyqt_ui/batch/match_switcher_dialog.py',
        'pyqt_ui/batch/parser.py',
        'pyqt_ui/batch/matcher.py',
        'pyqt_ui/batch/duplicate.py',
    ]
    
    for file in required_files:
        exists = os.path.exists(file)
        status = "[PASS]" if exists else "[FAIL]"
        print(f"  {file}: {status}")
        if not exists:
            return False
    print()
    
    # 步骤4: 导入模块
    print("[Step 4/6] Module Import Check")
    try:
        from pyqt_ui import main as main_module
        print("  pyqt_ui.main: [PASS]")
    except Exception as e:
        print(f"  pyqt_ui.main: [FAIL] - {e}")
        return False
    print()
    
    # 步骤5: 创建QApplication
    print("[Step 5/6] QApplication Creation")
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        print("  QApplication: [PASS]")
    except Exception as e:
        print(f"  QApplication: [FAIL] - {e}")
        return False
    print()
    
    # 步骤6: 创建MainWindow
    print("[Step 6/6] MainWindow Creation")
    try:
        from pyqt_ui.main import MainWindow
        window = MainWindow()
        print(f"  Window title: {window.windowTitle()}")
        print(f"  Window size: {window.size().width()}x{window.size().height()}")
        print(f"  MainWindow: [PASS]")
    except Exception as e:
        print(f"  MainWindow: [FAIL] - {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    print("=" * 60)
    print("ALL CHECKS PASSED - Application is ready to start!")
    print("=" * 60)
    print()
    print("To launch the application with GUI, run:")
    print("  1. Python script: python run_app.py")
    print("  2. Python module: python -m pyqt_ui.main")
    print("  3. Batch file (if fixed): 启动_修复版.bat")
    print()
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
