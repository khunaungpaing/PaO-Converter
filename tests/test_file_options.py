"""Tests for file conversion font options."""

import unittest

from core.file_options import (
    DEFAULT_SOURCE_FONTS,
    font_names_match,
    mapped_font_size,
    parse_size_mapping,
)


class TestFileOptions(unittest.TestCase):
    def test_parses_default_mapping(self) -> None:
        self.assertEqual(
            parse_size_mapping("16:12, 18 -> 14; 20=16"),
            {16.0: 12.0, 18.0: 14.0, 20.0: 16.0},
        )

    def test_matches_pdf_subset_and_style_names(self) -> None:
        self.assertTrue(font_names_match("ABCDEF+KothuPaOh1-Regular", "kothupaoh1"))
        self.assertFalse(font_names_match("Helvetica", "kothupaoh1"))

    def test_maps_only_configured_sizes(self) -> None:
        mapping = {16.0: 12.0, 18.0: 14.0, 20.0: 16.0}
        self.assertEqual(mapped_font_size(18.01, mapping), 14.0)
        self.assertEqual(mapped_font_size(24.0, mapping), 24.0)

    def test_default_source_fonts_contains_expected_fonts(self) -> None:
        self.assertIsInstance(DEFAULT_SOURCE_FONTS, list)
        expected = [
            "kothupaoh Number 1 Renew",
            "kothupaoh1",
            "kothupaoh1 Number Renew",
            "kothupaoh1 Numbering Renew",
            "kothupaoh1 Renew",
            "kothupaoh1Alphabet Renew",
            "kothupaoh2 Renew",
            "kothupaoh3 Renew",
            "kothupaoh4 Renew",
            "kothupaoh5 renew",
        ]
        for font in expected:
            self.assertIn(font, DEFAULT_SOURCE_FONTS)

    def test_empty_source_font_matches_all(self) -> None:
        # Empty string or None matches any font in document
        self.assertTrue(font_names_match("Helvetica", ""))
        self.assertTrue(font_names_match("Times New Roman", None))
        self.assertTrue(font_names_match("kothupaoh1", ""))

    def test_file_convert_tab_completer(self) -> None:
        import sys
        from PyQt6.QtWidgets import QApplication
        from ui.file_tab import FileConvertTab

        app = QApplication.instance() or QApplication(sys.argv)
        tab = FileConvertTab()
        self.assertEqual(tab.source_font_edit.text(), "")
        completer = tab.source_font_edit.completer()
        self.assertIsNotNone(completer)
        self.assertEqual(completer.model().stringList(), DEFAULT_SOURCE_FONTS)

    def test_file_convert_tab_actions(self) -> None:
        import sys
        from PyQt6.QtWidgets import QApplication
        from ui.file_tab import FileConvertTab

        app = QApplication.instance() or QApplication(sys.argv)
        tab = FileConvertTab()

        # Initial state: no file loaded
        self.assertFalse(tab.convert_btn.isEnabled())
        self.assertFalse(tab.clear_btn.isEnabled())
        self.assertTrue(tab.select_btn.isEnabled())
        self.assertFalse(tab.cancel_btn.isEnabled())

        # Select a file
        tab._set_selected_file("/fake/path/sample.docx")
        self.assertEqual(tab._selected_file_path, "/fake/path/sample.docx")
        self.assertTrue(tab.convert_btn.isEnabled())
        self.assertTrue(tab.clear_btn.isEnabled())
        self.assertTrue(tab.select_btn.isEnabled())

        # Clear the file
        tab._on_clear()
        self.assertIsNone(tab._selected_file_path)
        self.assertFalse(tab.convert_btn.isEnabled())
        self.assertFalse(tab.clear_btn.isEnabled())

        # Simulate restored controls after conversion
        tab._set_selected_file("/fake/path/sample.docx")
        tab._restore_controls()
        self.assertTrue(tab.convert_btn.isEnabled())
        self.assertTrue(tab.clear_btn.isEnabled())
        self.assertTrue(tab.select_btn.isEnabled())
        self.assertTrue(tab.drop_zone.isEnabled())
        self.assertTrue(tab.drop_zone.acceptDrops())

        # When worker is running, selecting or dropping files is guarded
        FakeWorker = type("FakeWorker", (), {"isRunning": lambda s: True})
        tab._worker = FakeWorker()
        tab._on_file_selected("/fake/path/another.docx")
        self.assertEqual(tab._selected_file_path, "/fake/path/sample.docx")

