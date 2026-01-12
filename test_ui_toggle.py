#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test for toggle_advanced_options"""

import sys
from PyQt6.QtWidgets import QApplication


def test_toggle():
    """Test toggle_advanced_options method"""
    app = QApplication(sys.argv)

    from pyqt_ui.main import MainWindow

    window = MainWindow()
    window.show()  # Show the window first!

    print("Initial state:")
    print(f"  advanced_options visible: {window.advanced_options_widget.isVisible()}")
    print(f"  advanced_options hidden: {window.advanced_options_widget.isHidden()}")
    print(f"  toggle button text: {window.toggle_advanced_btn.text()}")

    print("\nCalling toggle_advanced_options() directly...")
    window.toggle_advanced_options()

    # Process events to let UI update
    app.processEvents()

    print(f"  advanced_options visible: {window.advanced_options_widget.isVisible()}")
    print(f"  advanced_options hidden: {window.advanced_options_widget.isHidden()}")
    print(f"  toggle button text: {window.toggle_advanced_btn.text()}")

    # Note: isVisible() may return False if parent is not visible yet
    # Check isHidden() instead - this should change when we call setVisible
    initially_hidden = window.advanced_options_widget.isHidden()
    window.toggle_advanced_options()  # Toggle back
    app.processEvents()
    toggled_hidden = window.advanced_options_widget.isHidden()

    print(f"\nAfter second toggle:")
    print(f"  advanced_options hidden: {toggled_hidden}")

    # The key is that the hidden state should change
    if initially_hidden == toggled_hidden:
        print("\nERROR: hidden state should change after toggle")
        return False

    print("\n[PASS] Test passed!")
    return True


if __name__ == "__main__":
    success = test_toggle()
    sys.exit(0 if success else 1)
