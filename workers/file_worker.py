"""
Background worker for file conversion (TXT / DOCX / PDF).
Runs in a QThread so the UI stays responsive during heavy I/O.

Signals
-------
progress(int)   – 0-100 percentage
finished(str)   – success message
error(str)      – human-readable error description
"""

from __future__ import annotations

from pathlib import Path
from threading import Event
from PyQt6.QtCore import QThread, pyqtSignal

from core.cancellation import ConversionCancelled, raise_if_cancelled
from core.engine import convert_pao_ascii_to_unicode
from core.file_options import DEFAULT_SIZE_MAPPING
from migration.docx_converter import convert_docx_file
from migration.pdf_converter import UNICODE_FONT, convert_pdf_file, convert_pdf_to_txt_file


class FileConvertWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    cancelled = pyqtSignal(str)

    def __init__(
        self,
        src: str,
        dst: str,
        source_font: str | None = None,
        output_font_family: str = "KhamThaton",
        output_font_path: str | None = None,
        size_mapping: dict[float, float] | None = None,
    ) -> None:
        super().__init__()
        self.src = Path(src)
        self.dst = Path(dst)
        self.source_font = source_font
        self.output_font_family = output_font_family
        self.output_font_path = Path(output_font_path) if output_font_path else UNICODE_FONT
        self.size_mapping = DEFAULT_SIZE_MAPPING if size_mapping is None else size_mapping
        self._cancel_event = Event()

    def cancel(self) -> None:
        """Request cancellation; conversion stops at its next safe boundary."""
        self._cancel_event.set()

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        ext = self.src.suffix.lower()
        try:
            raise_if_cancelled(self._cancel_event.is_set)
            if ext == ".txt":
                self._convert_txt()
            elif ext == ".docx":
                self._convert_docx()
            elif ext == ".pdf":
                if self.dst.suffix.lower() == ".txt":
                    self._convert_pdf_to_txt()
                else:
                    self._convert_pdf()
            else:
                self.error.emit(f"Unsupported file type: {ext}")
                return
        except ConversionCancelled:
            self.cancelled.emit("Conversion cancelled. No output file was saved.")
            return
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))
            return

        self.finished.emit(f"Saved to: {self.dst}")

    # ------------------------------------------------------------------
    # Format handlers
    # ------------------------------------------------------------------

    def _convert_txt(self) -> None:
        text = self.src.read_text(encoding="utf-8")
        raise_if_cancelled(self._cancel_event.is_set)
        self.progress.emit(50)
        converted = convert_pao_ascii_to_unicode(text)
        raise_if_cancelled(self._cancel_event.is_set)
        self.dst.write_text(converted, encoding="utf-8")
        self.progress.emit(100)

    def _convert_docx(self) -> None:
        convert_docx_file(
            self.src,
            self.dst,
            source_font=self.source_font,
            output_font_family=self.output_font_family,
            size_mapping=self.size_mapping,
            progress=self.progress.emit,
            cancelled=self._cancel_event.is_set,
        )

    def _convert_pdf(self) -> None:
        convert_pdf_file(
            self.src,
            self.dst,
            self.progress.emit,
            source_font=self.source_font,
            output_font_path=self.output_font_path,
            size_mapping=self.size_mapping,
            cancelled=self._cancel_event.is_set,
        )

    def _convert_pdf_to_txt(self) -> None:
        convert_pdf_to_txt_file(
            self.src,
            self.dst,
            self.progress.emit,
            source_font=self.source_font,
            cancelled=self._cancel_event.is_set,
        )
