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


import re
import time


def _deduplicate_font_resources(doc: fitz.Document) -> None:
    """Redirect Form XObjects referencing duplicate font resources to a single instance.

    MuPDF's page.insert_htmlbox creates an isolated Form XObject and embeds a
    fresh copy of the font for every call. For multi-page documents, this
    creates thousands of redundant font streams. Re-pointing each Form XObject
    to the first font resource allows doc.save(garbage=3) to drop thousands of
    redundant font streams in milliseconds rather than spending minutes in
    pairwise stream comparisons (garbage=4).
    """
    first_font_res_xref: int | None = None
    for x in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(x)
        except Exception:
            continue
        if re.search(r"/Font\s*<<\s*/F0", obj):
            first_font_res_xref = x
            break

    if not first_font_res_xref:
        return

    for x in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(x)
        except Exception:
            continue
        if "/Subtype /Form" in obj and "/Resources" in obj:
            m = re.search(r"/Resources\s+(\d+)\s+0\s+R", obj)
            if m:
                res_id = int(m.group(1))
                if res_id != first_font_res_xref:
                    try:
                        res_obj = doc.xref_object(res_id)
                    except Exception:
                        continue
                    if re.search(r"/Font\s*<<\s*/F0", res_obj):
                        new_obj = re.sub(
                            r"/Resources\s+\d+\s+0\s+R",
                            f"/Resources {first_font_res_xref} 0 R",
                            obj,
                        )
                        doc.update_object(x, new_obj)


def _merge_line_spans(
    spans: list[dict[str, object]],
    source_font: str | None,
    sizes: dict[float, float],
    rotation: int,
) -> tuple[list[dict[str, object]], list[object], int]:
    """Group adjacent line spans sharing font/color/size into single replacement items.

    Returns (replacements, redact_rects, matched_span_count).
    Merging spans on the same line preserves Myanmar syllable shaping across
    fragment boundaries and drastically reduces HTML box insertion calls.
    """
    import fitz

    replacements: list[dict[str, object]] = []
    redact_rects: list[object] = []
    matched_count = 0

    current_group: dict[str, object] | None = None

    def flush_group() -> None:
        nonlocal current_group
        if not current_group:
            return
        texts = current_group["texts"]  # type: ignore[index]
        combined = "".join(texts)
        if combined:
            replacements.append({
                "bbox": tuple(current_group["bbox"]),  # type: ignore[arg-type]
                "origin": current_group["origin"],
                "text": convert_pao_ascii_to_unicode(combined),
                "size": current_group["size"],
                "color": current_group["color"],
                "rotate": rotation,
            })
        current_group = None

    for span in spans:
        original = span.get("text", "")
        if not original or not font_names_match(span.get("font"), source_font):
            flush_group()
            continue

        bbox = list(span["bbox"])
        redact_rects.append(fitz.Rect(bbox))
        matched_count += 1

        color = _pdf_color(span.get("color", 0))
        original_size = max(float(span.get("size", 11)), 1.0)
        size = mapped_font_size(original_size, sizes)

        if current_group is None:
            current_group = {
                "color": color,
                "size": size,
                "bbox": bbox,
                "origin": span.get("origin", (bbox[0], bbox[1])),
                "texts": [original],
            }
        else:
            prev_bbox = current_group["bbox"]  # type: ignore[index]
            texts = current_group["texts"]  # type: ignore[index]

            # Duplicate overlay / faux-bold span at same position
            if (
                abs(bbox[0] - prev_bbox[0]) < 1.0
                and abs(bbox[1] - prev_bbox[1]) < 1.0
                and original == texts[-1]
            ):
                continue

            is_same_style = (
                color == current_group["color"]
                and abs(size - float(current_group["size"])) < 0.2
            )
            gap = bbox[0] - prev_bbox[2]
            is_adjacent = gap <= max(size * 0.4, 4.0) and bbox[0] >= prev_bbox[0] - 1.0

            if is_same_style and is_adjacent:
                texts.append(original)
                prev_bbox[2] = max(prev_bbox[2], bbox[2])
                prev_bbox[3] = max(prev_bbox[3], bbox[3])
                prev_bbox[1] = min(prev_bbox[1], bbox[1])
            else:
                flush_group()
                current_group = {
                    "color": color,
                    "size": size,
                    "bbox": bbox,
                    "origin": span.get("origin", (bbox[0], bbox[1])),
                    "texts": [original],
                }

    flush_group()
    return replacements, redact_rects, matched_count


def convert_pdf_file(
    src_path: str | Path,
    dst_path: str | Path,
    progress: Callable[[int], None] | None = None,
    source_font: str | None = None,
    output_font_path: str | Path | None = None,
    size_mapping: dict[float, float] | None = None,
    cancelled: Callable[[], bool] | None = None,
    status_callback: Callable[[str], None] | None = None,
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
    font_bytes = output_font.read_bytes()
    font_archive = fitz.Archive()
    font_archive.add(font_bytes, output_font.name)

    converted_spans = 0
    try:
        total_pages = doc.page_count or 1
        for page_num in range(doc.page_count):
            raise_if_cancelled(cancelled)
            if status_callback:
                status_callback(f"Converting page {page_num + 1} of {total_pages}…")

            page: fitz.Page = doc[page_num]
            replacements: list[dict[str, object]] = []
            page_redacts: list[object] = []

            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    raise_if_cancelled(cancelled)
                    rotation = _pdf_text_rotation(line.get("dir", (1, 0)))
                    line_replacements, line_redacts, line_matched = _merge_line_spans(
                        line.get("spans", []),
                        source_font=source_font,
                        sizes=sizes,
                        rotation=rotation,
                    )
                    replacements.extend(line_replacements)
                    page_redacts.extend(line_redacts)
                    converted_spans += line_matched

            if replacements:
                for rect in page_redacts:
                    page.add_redact_annot(rect, fill=False, cross_out=False)
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

            if progress:
                progress(int((page_num + 1) / total_pages * 90))

            # Yield GIL to Qt GUI thread so the UI stays responsive and handles events
            time.sleep(0.002)

        raise_if_cancelled(cancelled)
        if status_callback:
            status_callback("Optimizing and saving PDF…")
        if progress:
            progress(92)

        _deduplicate_font_resources(doc)
        doc.save(str(dst), garbage=3, deflate=True)
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
    status_callback: Callable[[str], None] | None = None,
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
            if status_callback:
                status_callback(f"Extracting page {page_num + 1} of {total_pages}…")

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
            time.sleep(0.001)

        raise_if_cancelled(cancelled)
        if status_callback:
            status_callback("Writing text output…")
        dst.write_text("\n\f\n".join(pages), encoding="utf-8")
        if progress:
            progress(100)
    finally:
        doc.close()

    return converted_spans
