"""PDF-to-PDF Pa-O ASCII conversion while retaining original page artwork."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Callable

from core.cancellation import raise_if_cancelled
from core.engine import convert_pao_ascii_to_unicode
from core.file_options import (
    DEFAULT_SIZE_MAPPING,
    font_names_match,
    mapped_font_size,
)


UNICODE_FONT = (
    Path(__file__).resolve().parents[1] / "assets" / "fonts" / "KhamThaton-Exp-Regular-0.2.ttf"
)


def _pdf_color(value: object) -> tuple[float, float, float]:
    """Convert PyMuPDF's packed sRGB integer into PDF RGB components."""
    color = int(value)
    return (
        ((color >> 16) & 255) / 255,
        ((color >> 8) & 255) / 255,
        (color & 255) / 255,
    )


def _pdf_text_rotation(direction: object) -> int:
    """Return the nearest supported rotation for a PDF text-line vector."""
    dx, dy = direction  # type: ignore[misc]
    if abs(dx) >= abs(dy):
        return 0 if dx >= 0 else 180
    return 90 if dy < 0 else 270


def _insert_shaped_text(
    page: object,
    item: dict[str, object],
    font_path: Path,
    font_archive: object,
) -> None:
    """Insert one Unicode span through MuPDF's shaped HTML text engine."""
    import fitz  # PyMuPDF

    bbox = fitz.Rect(item["bbox"])
    size = float(item["size"])
    rotation = int(item["rotate"])
    color = item["color"]
    text = str(item["text"])
    red, green, blue = (round(float(component) * 255) for component in color)

    # Let MuPDF shape Myanmar Unicode directly. Keep the text in the PDF as
    # text, instead of converting it to vector paths.
    text_box = fitz.Rect(bbox.x0, bbox.y0, page.rect.x1, page.rect.y1)
    css = f"""
        @font-face {{ font-family: PaoUnicode; src: url('{font_path.name}'); }}
        * {{
            font-family: PaoUnicode;
            font-size: {size:.4f}pt;
            color: rgb({red}, {green}, {blue});
            line-height: 1;
            white-space: pre;
            margin: 0;
            padding: 0;
        }}
    """
    page.insert_htmlbox(
        text_box,
        f"<div>{escape(text)}</div>",
        css=css,
        archive=font_archive,
        rotate=rotation,
        scale_low=1,
        overlay=True,
    )


def convert_pdf_file(
    src_path: str | Path,
    dst_path: str | Path,
    progress: Callable[[int], None] | None = None,
    source_font: str | None = None,
    output_font_path: str | Path | None = None,
    size_mapping: dict[float, float] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> int:
    """Convert extractable text in a PDF and save another PDF.

    Pages, images, and vector graphics are retained. Unicode is inserted as
    shaped text with the selected output font. The return value is the number
    of text spans processed.
    """
    import fitz  # PyMuPDF

    src = Path(src_path)
    dst = Path(dst_path)
    output_font = Path(output_font_path) if output_font_path else UNICODE_FONT
    sizes = DEFAULT_SIZE_MAPPING if size_mapping is None else size_mapping
    if src.resolve() == dst.resolve():
        raise ValueError("Please choose a different output file for the converted PDF.")
    if not src.is_file():
        raise FileNotFoundError(f"Source PDF not found: {src}")
    if not output_font.is_file():
        raise FileNotFoundError(f"Output font not found: {output_font}")

    doc: fitz.Document = fitz.open(str(src))
    font_archive = fitz.Archive(str(output_font.parent))
    converted_spans = 0
    try:
        total_pages = doc.page_count or 1
        for page_num in range(doc.page_count):
            raise_if_cancelled(cancelled)
            page: fitz.Page = doc[page_num]
            replacements: list[dict[str, object]] = []

            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    raise_if_cancelled(cancelled)
                    rotation = _pdf_text_rotation(line.get("dir", (1, 0)))
                    for span in line.get("spans", []):
                        raise_if_cancelled(cancelled)
                        original = span.get("text", "")
                        if not original or not font_names_match(
                            span.get("font"), source_font
                        ):
                            continue
                        original_size = max(float(span.get("size", 11)), 1.0)
                        replacements.append({
                            "bbox": span["bbox"],
                            "origin": span["origin"],
                            "text": convert_pao_ascii_to_unicode(original),
                            "size": mapped_font_size(original_size, sizes),
                            "color": _pdf_color(span.get("color", 0)),
                            "rotate": rotation,
                        })
                        page.add_redact_annot(
                            fitz.Rect(span["bbox"]), fill=False, cross_out=False
                        )

            if replacements:
                # Apply every redaction before inserting replacement text so
                # overlapping span rectangles cannot erase newly inserted text.
                page.apply_redactions(images=0, graphics=0, text=0)
                for item in replacements:
                    raise_if_cancelled(cancelled)
                    _insert_shaped_text(
                        page,
                        item,
                        output_font,
                        font_archive,
                    )
                converted_spans += len(replacements)

            if progress:
                progress(int((page_num + 1) / total_pages * 90))

        raise_if_cancelled(cancelled)
        doc.save(str(dst), garbage=4, deflate=True)
        if progress:
            progress(100)
    finally:
        doc.close()

    return converted_spans


def convert_pdf_to_txt_file(
    src_path: str | Path,
    dst_path: str | Path,
    progress: Callable[[int], None] | None = None,
    source_font: str | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> int:
    """Extract a PDF in reading order and convert selected legacy-font spans.

    Text outside the selected source font is copied unchanged. Pages are
    separated by a form-feed so page boundaries are retained in the TXT file.
    """
    import fitz  # PyMuPDF

    src = Path(src_path)
    dst = Path(dst_path)
    if src.resolve() == dst.resolve():
        raise ValueError("Please choose a different output file for the converted text.")
    if not src.is_file():
        raise FileNotFoundError(f"Source PDF not found: {src}")

    doc: fitz.Document = fitz.open(str(src))
    converted_spans = 0
    pages: list[str] = []
    try:
        total_pages = doc.page_count or 1
        for page_num in range(doc.page_count):
            raise_if_cancelled(cancelled)
            page = doc[page_num]
            lines: list[str] = []
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    raise_if_cancelled(cancelled)
                    parts: list[str] = []
                    for span in line.get("spans", []):
                        raise_if_cancelled(cancelled)
                        text = str(span.get("text", ""))
                        if font_names_match(span.get("font"), source_font):
                            parts.append(convert_pao_ascii_to_unicode(text))
                            if text:
                                converted_spans += 1
                        else:
                            parts.append(text)
                    lines.append("".join(parts))
            pages.append("\n".join(lines))
            if progress:
                progress(int((page_num + 1) / total_pages * 90))

        raise_if_cancelled(cancelled)
        dst.write_text("\n\f\n".join(pages), encoding="utf-8")
        if progress:
            progress(100)
    finally:
        doc.close()

    return converted_spans
