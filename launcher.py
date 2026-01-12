#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple launcher for Music Downloader
Double-click this file to start the application
"""

import sys
import os

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def main():
    print("Starting Music Downloader...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from pyqt_ui.main import MainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()
