#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify match settings UI creation"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def test_ui_creation():
    """Test that match settings UI can be created without errors"""

    print("Creating QApplication...")
    app = QApplication(sys.argv)

    print("Importing MainWindow...")
    from pyqt_ui.main import MainWindow

    print("Creating MainWindow...")
    window = MainWindow()

    print("Verifying match settings UI components...")

    # Check that the match settings widgets were created
    assert hasattr(window, 'strict_btn'), "strict_btn not found"
    assert hasattr(window, 'standard_btn'), "standard_btn not found"
    assert hasattr(window, 'loose_btn'), "loose_btn not found"
    assert hasattr(window, 'threshold_slider'), "threshold_slider not found"
    assert hasattr(window, 'threshold_label'), "threshold_label not found"
    assert hasattr(window, 'advanced_options_widget'), "advanced_options_widget not found"
    assert hasattr(window, 'toggle_advanced_btn'), "toggle_advanced_btn not found"

    # Check initial state
    assert window.current_match_mode is not None, "current_match_mode should be initialized"
    assert window.current_threshold > 0, "current_threshold should be set"

    # Check that buttons are checkable
    assert window.strict_btn.isCheckable(), "strict_btn should be checkable"
    assert window.standard_btn.isCheckable(), "standard_btn should be checkable"
    assert window.loose_btn.isCheckable(), "loose_btn should be checkable"

    # Check that standard mode is selected by default
    assert window.standard_btn.isChecked(), "standard_btn should be checked by default"

    # Check that advanced options are hidden by default
    assert not window.advanced_options_widget.isVisible(), "advanced_options should be hidden by default"

    print(f"Initial match mode: {window.current_match_mode.value}")
    print(f"Initial threshold: {window.current_threshold:.2%}")

    print("\n=== Test toggle_advanced_options ===")
    # Test toggle functionality
    window.toggle_advanced_btn.click()
    assert window.advanced_options_widget.isVisible(), "advanced_options should be visible after toggle"
    print("PASS: Advanced options visible after toggle")

    window.toggle_advanced_btn.click()
    assert not window.advanced_options_widget.isVisible(), "advanced_options should be hidden after second toggle"
    print("PASS: Advanced options hidden after second toggle")

    print("\n=== Test threshold slider ===")
    # Test threshold slider
    window.threshold_slider.setValue(75)
    assert window.current_threshold == 0.75, f"Threshold should be 0.75, got {window.current_threshold}"
    assert window.threshold_label.text() == "75%", f"Label should be '75%', got '{window.threshold_label.text()}'"
    assert window.current_match_mode.name == "CUSTOM", "Mode should switch to CUSTOM"
    print("PASS: Threshold slider works correctly")

    print("\n=== Test mode buttons ===")
    # Test mode buttons (just verify they can be clicked without errors)
    window.strict_btn.click()
    assert window.strict_btn.isChecked(), "strict_btn should be checked after click"
    print("PASS: Strict mode button clicked")

    window.loose_btn.click()
    assert window.loose_btn.isChecked(), "loose_btn should be checked after click"
    print("PASS: Loose mode button clicked")

    print("\n" + "=" * 50)
    print("All UI creation tests passed!")
    print("=" * 50)

    # Don't show the window
    # window.show()
    # sys.exit(app.exec())


if __name__ == "__main__":
    test_ui_creation()
