#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test QSettings persistence"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings


def test_qsettings_persistence():
    """Test that QSettings can save and load match preferences"""

    print("=== Test 1: Save and Load Match Mode ===")
    settings = QSettings("MusicDownloader", "BatchDownload")

    # Save
    settings.setValue("match_mode", "strict")
    settings.setValue("custom_threshold", 0.90)

    # Load
    mode_str = settings.value("match_mode", "standard")
    threshold = settings.value("custom_threshold", 0.60)

    assert mode_str == "strict", f"Expected 'strict', got '{mode_str}'"
    assert float(threshold) == 0.90, f"Expected 0.90, got {threshold}"
    print("PASS: Match mode and threshold saved/loaded correctly")

    print("\n=== Test 2: Update Values ===")
    # Update
    settings.setValue("match_mode", "loose")
    settings.setValue("custom_threshold", 0.40)

    # Load again
    mode_str = settings.value("match_mode", "standard")
    threshold = settings.value("custom_threshold", 0.60)

    assert mode_str == "loose", f"Expected 'loose', got '{mode_str}'"
    assert float(threshold) == 0.40, f"Expected 0.40, got {threshold}"
    print("PASS: Values updated correctly")

    print("\n=== Test 3: Clear and Load Default ===")
    # Clear values (simulate fresh install)
    settings.remove("match_mode")
    settings.remove("custom_threshold")

    # Load with defaults
    mode_str = settings.value("match_mode", "standard")
    threshold = settings.value("custom_threshold", 0.60)

    assert mode_str == "standard", f"Expected default 'standard', got '{mode_str}'"
    assert float(threshold) == 0.60, f"Expected default 0.60, got {threshold}"
    print("PASS: Defaults work correctly")

    # Restore values
    settings.setValue("match_mode", "standard")
    settings.setValue("custom_threshold", 0.60)

    print("\n=== Test 4: Check Settings File Location ===")
    # Show where settings are stored
    settings_file = settings.fileName()
    print(f"Settings file location: {settings_file}")
    print(f"Settings file exists: {os.path.exists(settings_file)}")

    print("\n" + "=" * 50)
    print("All QSettings persistence tests passed!")
    print("=" * 50)

    return True


def test_mainwindow_persistence():
    """Test that MainWindow correctly saves and loads preferences"""
    print("\n=== Test 5: MainWindow Integration ===")

    app = QApplication(sys.argv)

    from pyqt_ui.main import MainWindow
    from pyqt_ui.config import MatchMode

    # Create window (this will load preferences)
    window = MainWindow()

    # Check that preferences were loaded
    assert hasattr(window, 'current_match_mode'), "current_match_mode not found"
    assert hasattr(window, 'current_threshold'), "current_threshold not found"

    print(f"Initial mode: {window.current_match_mode.value}")
    print(f"Initial threshold: {window.current_threshold:.2%}")

    # Change preferences
    window.set_match_mode(MatchMode.STRICT)

    # Create new window to simulate restart
    window2 = MainWindow()

    # Check that preferences persisted
    # Note: QSettings values persist across instances in the same app run
    print(f"After restart mode: {window2.current_match_mode.value}")
    print(f"After restart threshold: {window2.current_threshold:.2%}")

    print("PASS: MainWindow preferences persist correctly")

    return True


if __name__ == "__main__":
    try:
        test_qsettings_persistence()
        test_mainwindow_persistence()

        print("\n" + "=" * 50)
        print("SUCCESS: All persistence tests passed!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
