"""Tests for file conversion font options."""

import unittest

from core.file_options import (
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
