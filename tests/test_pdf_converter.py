"""Integration tests for PDF-to-PDF conversion."""

import os
import tempfile
import unittest

try:
    import fitz
except ImportError:  # The project dependency may not be installed in minimal CI.
    fitz = None

from core.cancellation import ConversionCancelled
from migration.pdf_converter import convert_pdf_file, convert_pdf_to_txt_file


@unittest.skipIf(fitz is None, "PyMuPDF is not installed")
class TestPdfConverter(unittest.TestCase):
    def test_converts_text_and_preserves_page_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "source.pdf")
            dst = os.path.join(tmp, "converted.pdf")

            doc = fitz.open()
            page = doc.new_page(width=400, height=250)
            page.draw_rect(fitz.Rect(30, 30, 370, 220), color=(0, 0, 1))
            page.insert_text((50, 100), "at_m", fontsize=24)
            doc.save(src)
            doc.close()

            count = convert_pdf_file(src, dst)

            self.assertGreater(count, 0)
            self.assertTrue(os.path.isfile(dst))
            result = fitz.open(dst)
            try:
                self.assertEqual(result.page_count, 1)
                self.assertEqual(result[0].rect, fitz.Rect(0, 0, 400, 250))
                self.assertTrue(result[0].get_drawings())
            finally:
                result.close()

    def test_rejects_overwriting_source(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as source:
            with self.assertRaises(ValueError):
                convert_pdf_file(source.name, source.name)

    def test_converts_only_selected_font(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "source.pdf")
            dst = os.path.join(tmp, "converted.pdf")
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 80), "at_m", fontsize=16, fontname="helv")
            page.insert_text((50, 130), "keep", fontsize=16, fontname="cour")
            doc.save(src)
            doc.close()

            count = convert_pdf_file(
                src,
                dst,
                source_font="Helvetica",
                size_mapping={16.0: 12.0},
            )

            self.assertEqual(count, 1)
            result = fitz.open(dst)
            try:
                self.assertIn("keep", result[0].get_text())
                spans = [
                    span
                    for block in result[0].get_text("dict")["blocks"]
                    if block.get("type") == 0
                    for line in block["lines"]
                    for span in line["spans"]
                ]
                converted = next(span for span in spans if span["text"] != "keep")
                self.assertAlmostEqual(converted["size"], 12.0, places=1)
            finally:
                result.close()

    def test_converts_pdf_to_txt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "source.pdf")
            dst = os.path.join(tmp, "converted.txt")
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 80), "at_m", fontsize=16, fontname="helv")
            page.insert_text((50, 120), "keep", fontsize=16, fontname="cour")
            doc.save(src)
            doc.close()

            count = convert_pdf_to_txt_file(src, dst, source_font="Helvetica")

            self.assertEqual(count, 1)
            with open(dst, encoding="utf-8") as output:
                text = output.read()
            self.assertIn("အ", text)
            self.assertIn("keep", text)

    def test_pdf_to_txt_cancellation_does_not_write_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "source.pdf")
            dst = os.path.join(tmp, "converted.txt")
            doc = fitz.open()
            doc.new_page().insert_text((50, 80), "at_m", fontsize=16)
            doc.save(src)
            doc.close()

            with self.assertRaises(ConversionCancelled):
                convert_pdf_to_txt_file(src, dst, cancelled=lambda: True)
            self.assertFalse(os.path.exists(dst))

    def test_pdf_conversion_status_callback_invoked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "source.pdf")
            dst = os.path.join(tmp, "converted.pdf")
            doc = fitz.open()
            doc.new_page().insert_text((50, 80), "at_m", fontsize=16)
            doc.save(src)
            doc.close()

            statuses: list[str] = []
            convert_pdf_file(src, dst, status_callback=statuses.append)

            self.assertTrue(any("page 1" in s.lower() for s in statuses))
            self.assertTrue(any("saving" in s.lower() for s in statuses))

    def test_pdf_converter_merges_adjacent_line_spans(self) -> None:
        from migration.pdf_converter import _merge_line_spans

        spans = [
            {
                "font": "kothupaoh1",
                "size": 16.0,
                "color": 0,
                "bbox": (50.0, 100.0, 80.0, 120.0),
                "origin": (50.0, 115.0),
                "text": "at_",
            },
            {
                "font": "kothupaoh1",
                "size": 16.0,
                "color": 0,
                "bbox": (80.0, 100.0, 100.0, 120.0),
                "origin": (80.0, 115.0),
                "text": "m",
            },
        ]
        replacements, redact_rects, count = _merge_line_spans(
            spans, source_font="kothupaoh1", sizes={16.0: 16.0}, rotation=0
        )
        self.assertEqual(count, 2)
        self.assertEqual(len(redact_rects), 2)
        self.assertEqual(len(replacements), 1)
        # "at_m" converted together
        self.assertIn("အ", replacements[0]["text"])
