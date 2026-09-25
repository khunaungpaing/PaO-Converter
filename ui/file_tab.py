"""File Convert tab – background conversion of TXT / DOCX / PDF files."""
from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QProgressBar, QLineEdit,
    QFileDialog, QMessageBox, QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase

from core.file_options import DEFAULT_SIZE_MAPPING_TEXT, parse_size_mapping
from migration.pdf_converter import UNICODE_FONT
from workers.file_worker import FileConvertWorker
from .widgets import DropZoneWidget

_FILTER = "Supported Files (*.txt *.docx *.pdf)"
_EXT_SAVE_FILTER = {
    ".txt": "Text File (*.txt)",
    ".docx": "Word Document (*.docx)",
    ".pdf": "PDF Document (*.pdf)",
}


def _find_font_file(family: str) -> str | None:
    """Try to locate a .ttf/.otf file for *family* in system font directories."""
    import sys as _sys
    from pathlib import Path

    dirs: list[Path] = []
    if _sys.platform == "darwin":
        dirs = [
            Path.home() / "Library" / "Fonts",
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
        ]
    elif _sys.platform.startswith("win"):
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs = [Path(windir) / "Fonts"]
    else:
        dirs = [
            Path.home() / ".local" / "share" / "fonts",
            Path.home() / ".fonts",
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
        ]

    target = family.casefold().replace(" ", "").replace("-", "")

    for font_dir in dirs:
        if not font_dir.is_dir():
            continue
        for path in font_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (".ttf", ".otf"):
                continue
            stem = path.stem.casefold().replace(" ", "").replace("-", "")
            if target == stem or target in stem:
                return str(path)

    return None

class FileConvertTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: FileConvertWorker | None = None
        self._output_font_path: str = str(UNICODE_FONT)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(12)

        # -- Drop zone --
        self.drop_zone = DropZoneWidget("Drag & drop a file here\nTXT · DOCX · PDF")
        self.drop_zone.fileDropped.connect(self._handle_source_file)
        layout.addWidget(self.drop_zone)

        # -- Settings --
        font_form = QFormLayout()
        font_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        font_form.setContentsMargins(0, 4, 0, 4)

        self.source_font_edit = QLineEdit("kothupaoh1")
        self.source_font_edit.setFixedWidth(250)
        self.source_font_edit.setPlaceholderText("Leave empty to convert every font")
        self.source_font_edit.setToolTip(
            "Only text using this source font will be converted. "
            "Font matching ignores case, spaces, and PDF subset prefixes."
        )
        font_form.addRow("Convert only font:", self.source_font_edit)

        # Output font: name + choose button in one compact row
        output_row = QHBoxLayout()
        default_font_id = QFontDatabase.addApplicationFont(str(UNICODE_FONT))
        default_families = (
            QFontDatabase.applicationFontFamilies(default_font_id)
            if default_font_id != -1 else []
        )
        self.output_family_edit = QLineEdit(
            default_families[0] if default_families else "KhamThaton-Exp"
        )
        self.output_family_edit.setToolTip(
            "Font family written into converted DOCX runs and used for PDF output. "
            "Click 'Choose Font…' to select a different font file."
        )
        output_browse = QPushButton("Choose Font…")
        font_menu = QMenu(output_browse)
        font_menu.addAction("System Fonts…", self._pick_system_font)
        font_menu.addAction("Font File…", self._browse_font_file)
        output_browse.setMenu(font_menu)
        output_row.addWidget(self.output_family_edit)
        output_row.addWidget(output_browse)
        font_form.addRow("Output font name:", output_row)

        self.size_mapping_edit = QLineEdit(DEFAULT_SIZE_MAPPING_TEXT)
        self.size_mapping_edit.setToolTip(
            "Source-to-output point sizes. Sizes not listed here are preserved."
        )
        font_form.addRow("Size mapping:", self.size_mapping_edit)

        layout.addLayout(font_form)

        # -- Action buttons --
        btn_row = QHBoxLayout()
        self.select_btn = QPushButton("Select File…")
        self.select_btn.clicked.connect(self._on_select)
        btn_row.addWidget(self.select_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        # -- Progress + status --
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    # ------------------------------------------------------------------

    def _pick_system_font(self) -> None:
        """Let the user pick a system-installed font via the platform dialog."""
        from PyQt6.QtWidgets import QFontDialog

        font, ok = QFontDialog.getFont(self)
        if not ok:
            return

        family = font.family()
        self.output_family_edit.setText(family)

        # Try to find the corresponding font file for PDF embedding
        path = _find_font_file(family)
        if path:
            self._output_font_path = path
        else:
            QMessageBox.information(
                self,
                "Font File Not Found",
                f"Could not locate the font file for \"{family}\" automatically.\n\n"
                "The font name has been set for DOCX output.\n"
                "For PDF conversion, please use Choose Font… → Font File… "
                "to select the .ttf / .otf file manually.",
            )

    def _browse_font_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Output Font",
            os.path.dirname(self._output_font_path),
            "Font Files (*.ttf *.otf)",
        )
        if not path:
            return

        font_id = QFontDatabase.addApplicationFont(path)
        families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
        if not families:
            QMessageBox.warning(
                self, "Invalid Font", "The selected font could not be loaded."
            )
            return
        self._output_font_path = path
        self.output_family_edit.setText(families[0])

    def _on_select(self) -> None:
        """Open a file dialog, then forward the chosen path to the handler."""
        src, _ = QFileDialog.getOpenFileName(self, "Select Source File", "", _FILTER)
        if not src:
            return
        self.drop_zone.showFile(os.path.basename(src))
        self._handle_source_file(src)

    def _handle_source_file(self, src: str) -> None:
        """Common handler for both button-select and drag-and-drop."""
        ext = os.path.splitext(src)[1].lower()
        output_ext = ext

        # Ask for output format only when a PDF file is selected
        if ext == ".pdf":
            msg = QMessageBox(self)
            msg.setWindowTitle("PDF Output Format")
            msg.setText(
                f"<b>{os.path.basename(src)}</b><br><br>"
                "Choose the output format for this PDF:"
            )
            msg.setIcon(QMessageBox.Icon.Question)
            pdf_btn = msg.addButton("PDF (.pdf)", QMessageBox.ButtonRole.AcceptRole)
            txt_btn = msg.addButton("Text (.txt)", QMessageBox.ButtonRole.AcceptRole)
            msg.addButton(QMessageBox.StandardButton.Cancel)
            msg.exec()
            clicked = msg.clickedButton()
            if clicked == pdf_btn:
                output_ext = ".pdf"
            elif clicked == txt_btn:
                output_ext = ".txt"
            else:
                return  # user cancelled

        save_filter = _EXT_SAVE_FILTER.get(output_ext, "All Files (*)")
        src_dir = os.path.dirname(src)
        source_name = os.path.splitext(os.path.basename(src))[0]
        default_name = f"converted_{source_name}{output_ext}"
        dst, _ = QFileDialog.getSaveFileName(
            self, "Save Converted File",
            os.path.join(src_dir, default_name),
            save_filter,
        )
        if not dst:
            return

        # Keep the selected output type even when the platform save dialog does
        # not append the selected extension automatically.
        if output_ext and not dst.lower().endswith(output_ext):
            dst += output_ext

        self._start_worker(src, dst)

    def _start_worker(self, src: str, dst: str) -> None:
        try:
            size_mapping = parse_size_mapping(self.size_mapping_edit.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Size Mapping", str(exc))
            return

        output_family = self.output_family_edit.text().strip()
        if not output_family or not self._output_font_path:
            QMessageBox.warning(
                self, "Missing Font", "Please select an output font and font name."
            )
            return

        self.select_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.drop_zone.setAcceptDrops(False)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status_label.setText("Converting…")

        self._worker = FileConvertWorker(
            src,
            dst,
            source_font=self.source_font_edit.text().strip() or None,
            output_font_family=output_family,
            output_font_path=self._output_font_path,
            size_mapping=size_mapping,
        )
        self._worker.progress.connect(self.progress.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.start()

    def _restore_controls(self) -> None:
        """Re-enable buttons and drop zone after conversion ends."""
        self.select_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.drop_zone.setAcceptDrops(True)

    def _on_cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.status_label.setText("Cancelling…")

    def _on_finished(self, message: str) -> None:
        self.progress.setValue(100)
        self.status_label.setText("Done ✓")
        self._restore_controls()
        QMessageBox.information(self, "Conversion Complete", message)

    def _on_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self.status_label.setText("Failed ✗")
        self._restore_controls()
        QMessageBox.critical(self, "Conversion Error", message)

    def _on_cancelled(self, message: str) -> None:
        self.progress.setVisible(False)
        self.status_label.setText("Cancelled")
        self._restore_controls()
        QMessageBox.information(self, "Conversion Cancelled", message)
