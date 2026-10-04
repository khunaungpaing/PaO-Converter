"""File Convert tab – background conversion of TXT / DOCX / PDF files."""
from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QProgressBar, QLineEdit,
    QFileDialog, QMessageBox, QMenu, QCompleter,
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFontDatabase

from core.file_options import (
    DEFAULT_SIZE_MAPPING_TEXT,
    DEFAULT_SOURCE_FONTS,
    parse_size_mapping,
)
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
    """Try to locate a .ttf/.otf/.ttc file for *family* in system and local font directories."""
    import sys as _sys
    from pathlib import Path

    dirs: list[Path] = [
        Path(__file__).resolve().parent.parent / "assets" / "fonts",
    ]
    if _sys.platform == "darwin":
        dirs.extend([
            Path.home() / "Library" / "Fonts",
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
        ])
    elif _sys.platform.startswith("win"):
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs.append(Path(windir) / "Fonts")
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            dirs.append(Path(localappdata) / "Microsoft" / "Windows" / "Fonts")
        else:
            dirs.append(Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts")
    else:
        dirs.extend([
            Path.home() / ".local" / "share" / "fonts",
            Path.home() / ".fonts",
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
        ])

    target = family.casefold().replace(" ", "").replace("-", "")
    partial_match: str | None = None

    for font_dir in dirs:
        if not font_dir.is_dir():
            continue
        for path in font_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (".ttf", ".otf", ".ttc"):
                continue
            stem = path.stem.casefold().replace(" ", "").replace("-", "")
            if target == stem:
                return str(path)
            if (target in stem or stem in target) and partial_match is None:
                partial_match = str(path)

    return partial_match

class FileConvertTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: FileConvertWorker | None = None
        self._output_font_path: str = str(UNICODE_FONT)
        self._selected_file_path: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(12)

        # -- Drop zone --
        self.drop_zone = DropZoneWidget()
        self.drop_zone.fileDropped.connect(self._on_file_selected)
        self.drop_zone.clicked.connect(self._on_select)
        layout.addWidget(self.drop_zone)

        # -- Settings --
        font_form = QFormLayout()
        font_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        font_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        font_form.setContentsMargins(0, 4, 0, 4)

        self.source_font_edit = QLineEdit("")
        self.source_font_edit.setMinimumWidth(280)
        self.source_font_edit.setPlaceholderText("Leave empty to convert every font")
        self.source_font_edit.setToolTip(
            "Only text using this source font will be converted. "
            "Font matching ignores case, spaces, and PDF subset prefixes."
        )
        self.source_font_edit.setClearButtonEnabled(True)

        font_completer = QCompleter(DEFAULT_SOURCE_FONTS, self.source_font_edit)
        font_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        font_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.source_font_edit.setCompleter(font_completer)

        font_form.addRow("Convert only font:", self.source_font_edit)

        # Output font: name + choose button in one compact row
        output_row = QHBoxLayout()
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.setSpacing(8)
        default_font_id = QFontDatabase.addApplicationFont(str(UNICODE_FONT))
        default_families = (
            QFontDatabase.applicationFontFamilies(default_font_id)
            if default_font_id != -1 else []
        )
        self.output_family_edit = QLineEdit(
            default_families[0] if default_families else "KhamThaton-Exp"
        )
        self.output_family_edit.setMinimumWidth(220)
        self.output_family_edit.setToolTip(
            "Font family written into converted DOCX runs and used for PDF output. "
            "Click 'Choose Font…' to select a different font file."
        )
        self.choose_font_btn = QPushButton("Choose Font…")
        font_menu = QMenu(self.choose_font_btn)
        font_menu.addAction("System Fonts…", self._pick_system_font)
        font_menu.addAction("Font File…", self._browse_font_file)
        self.choose_font_btn.setMenu(font_menu)
        output_row.addWidget(self.output_family_edit, 1)
        output_row.addWidget(self.choose_font_btn, 0)
        font_form.addRow("Output font name:", output_row)

        self.size_mapping_edit = QLineEdit(DEFAULT_SIZE_MAPPING_TEXT)
        self.size_mapping_edit.setMinimumWidth(280)
        self.size_mapping_edit.setClearButtonEnabled(True)
        self.size_mapping_edit.setToolTip(
            "Source-to-output point sizes. Sizes not listed here are preserved."
        )
        font_form.addRow("Size mapping:", self.size_mapping_edit)

        layout.addLayout(font_form)

        # -- Action buttons --
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.select_btn = QPushButton("Select File…")
        self.select_btn.setToolTip("Select or change the file to convert")
        self.select_btn.clicked.connect(self._on_select)
        btn_row.addWidget(self.select_btn)

        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setToolTip("Convert the selected file")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self._on_convert)
        btn_row.addWidget(self.convert_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear current file and reset")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(self.clear_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setToolTip("Cancel running conversion")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self._apply_button_styles()

        # -- Progress + status --
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def _is_dark(self) -> bool:
        return self.palette().window().color().lightness() < 128

    def _apply_button_styles(self) -> None:
        """Apply uniform height, radius, and theme-adaptive colors to all action buttons."""
        is_dark = self._is_dark()
        if is_dark:
            neutral_style = (
                "QPushButton {"
                "  border: 1px solid rgba(255, 255, 255, 0.18);"
                "  border-radius: 6px;"
                "  padding: 6px 16px;"
                "  background-color: rgba(255, 255, 255, 0.08);"
                "  color: #e6edf3;"
                "  font-size: 13px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: rgba(255, 255, 255, 0.16);"
                "  color: #ffffff;"
                "  border-color: rgba(255, 255, 255, 0.35);"
                "}"
                "QPushButton:pressed {"
                "  background-color: rgba(255, 255, 255, 0.12);"
                "}"
                "QPushButton:disabled {"
                "  background-color: rgba(255, 255, 255, 0.03);"
                "  color: rgba(255, 255, 255, 0.25);"
                "  border-color: rgba(255, 255, 255, 0.06);"
                "}"
            )
            primary_style = (
                "QPushButton {"
                "  border: 1px solid rgba(255, 255, 255, 0.15);"
                "  border-radius: 6px;"
                "  padding: 6px 16px;"
                "  background-color: #238636;"
                "  color: #ffffff;"
                "  font-size: 13px;"
                "  font-weight: 600;"
                "}"
                "QPushButton:hover {"
                "  background-color: #2ea043;"
                "  border-color: rgba(255, 255, 255, 0.3);"
                "}"
                "QPushButton:pressed {"
                "  background-color: #196c2e;"
                "}"
                "QPushButton:disabled {"
                "  background-color: rgba(255, 255, 255, 0.03);"
                "  color: rgba(255, 255, 255, 0.25);"
                "  border-color: rgba(255, 255, 255, 0.06);"
                "}"
            )
            clear_style = (
                "QPushButton {"
                "  border: 1px solid rgba(255, 255, 255, 0.18);"
                "  border-radius: 6px;"
                "  padding: 6px 16px;"
                "  background-color: rgba(255, 255, 255, 0.08);"
                "  color: #e6edf3;"
                "  font-size: 13px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: rgba(248, 81, 73, 0.15);"
                "  color: #ff7b72;"
                "  border-color: rgba(248, 81, 73, 0.4);"
                "}"
                "QPushButton:pressed {"
                "  background-color: rgba(248, 81, 73, 0.25);"
                "}"
                "QPushButton:disabled {"
                "  background-color: rgba(255, 255, 255, 0.03);"
                "  color: rgba(255, 255, 255, 0.25);"
                "  border-color: rgba(255, 255, 255, 0.06);"
                "}"
            )
        else:
            neutral_style = (
                "QPushButton {"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 6px;"
                "  padding: 6px 16px;"
                "  background-color: #f6f8fa;"
                "  color: #24292f;"
                "  font-size: 13px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: #f3f4f6;"
                "  color: #0969da;"
                "  border-color: #afb8c1;"
                "}"
                "QPushButton:pressed {"
                "  background-color: #e5e7eb;"
                "}"
                "QPushButton:disabled {"
                "  background-color: #f6f8fa;"
                "  color: #8c959f;"
                "  border-color: #e5e7eb;"
                "}"
            )
            primary_style = (
                "QPushButton {"
                "  border: 1px solid rgba(27, 31, 36, 0.15);"
                "  border-radius: 6px;"
                "  padding: 6px 16px;"
                "  background-color: #1f883d;"
                "  color: #ffffff;"
                "  font-size: 13px;"
                "  font-weight: 600;"
                "}"
                "QPushButton:hover {"
                "  background-color: #1a7f37;"
                "}"
                "QPushButton:pressed {"
                "  background-color: #15662b;"
                "}"
                "QPushButton:disabled {"
                "  background-color: #f6f8fa;"
                "  color: #8c959f;"
                "  border-color: #e5e7eb;"
                "}"
            )
            clear_style = (
                "QPushButton {"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 6px;"
                "  padding: 6px 16px;"
                "  background-color: #f6f8fa;"
                "  color: #24292f;"
                "  font-size: 13px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: #ffebe9;"
                "  color: #cf222e;"
                "  border-color: #ff8182;"
                "}"
                "QPushButton:pressed {"
                "  background-color: #ffcecb;"
                "}"
                "QPushButton:disabled {"
                "  background-color: #f6f8fa;"
                "  color: #8c959f;"
                "  border-color: #e5e7eb;"
                "}"
            )

        self.select_btn.setStyleSheet(neutral_style)
        self.convert_btn.setStyleSheet(primary_style)
        self.clear_btn.setStyleSheet(clear_style)
        self.cancel_btn.setStyleSheet(neutral_style)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.PaletteChange:
            self._apply_button_styles()
        super().changeEvent(event)

    # ------------------------------------------------------------------

    def _pick_system_font(self) -> None:
        """Let the user pick a system-installed font via the platform dialog."""
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import QFontDialog

        current_family = self.output_family_edit.text().strip() or "KhamThaton-Exp"
        initial_font = QFont(current_family, 12)

        dialog = QFontDialog(initial_font, self)
        dialog.setWindowTitle("Select System Font")
        # Native macOS NSFontPanel lacks an OK button and closing it rejects the dialog.
        # Explicitly use Qt's dialog so the user has explicit OK and Cancel buttons.
        dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)

        if dialog.exec() != QFontDialog.DialogCode.Accepted:
            return

        family = dialog.selectedFont().family()
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
        """Open a file dialog to choose a source file."""
        if self._worker and self._worker.isRunning():
            return
        src, _ = QFileDialog.getOpenFileName(self, "Select Source File", "", _FILTER)
        if not src:
            return
        self._set_selected_file(src)

    def _on_file_selected(self, path: str) -> None:
        """Handle file dropped onto the drop zone."""
        if self._worker and self._worker.isRunning():
            return
        self._set_selected_file(path)

    def _set_selected_file(self, path: str) -> None:
        """Set active file, update drop zone and action buttons."""
        self._selected_file_path = path
        self.drop_zone.showFile(path)
        self.convert_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.status_label.setText(f"Ready: {os.path.basename(path)}")
        self.progress.setVisible(False)

    def _on_clear(self) -> None:
        """Clear currently loaded file and reset state."""
        self._selected_file_path = None
        self.drop_zone.reset()
        self.convert_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.status_label.setText("")
        self.progress.setVisible(False)

    def _on_convert(self) -> None:
        """Convert the currently selected file."""
        if not self._selected_file_path or not os.path.isfile(self._selected_file_path):
            QMessageBox.warning(self, "No File", "Please select a file to convert first.")
            return
        self._handle_source_file(self._selected_file_path)

    def _handle_source_file(self, src: str) -> None:
        """Prompt destination and run conversion for *src*."""
        self._selected_file_path = src
        self.drop_zone.showFile(src)
        self.convert_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

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
        self.convert_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.drop_zone.setAcceptDrops(False)
        self.drop_zone.setEnabled(False)
        self.source_font_edit.setEnabled(False)
        self.output_family_edit.setEnabled(False)
        self.choose_font_btn.setEnabled(False)
        self.size_mapping_edit.setEnabled(False)
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
        self._worker.status.connect(self.status_label.setText)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.start()

    def _restore_controls(self) -> None:
        """Re-enable buttons, drop zone, and settings after conversion ends."""
        self.select_btn.setEnabled(True)
        self.convert_btn.setEnabled(self._selected_file_path is not None)
        self.clear_btn.setEnabled(self._selected_file_path is not None)
        self.cancel_btn.setEnabled(False)
        self.drop_zone.setEnabled(True)
        self.drop_zone.setAcceptDrops(True)
        self.source_font_edit.setEnabled(True)
        self.output_family_edit.setEnabled(True)
        self.choose_font_btn.setEnabled(True)
        self.size_mapping_edit.setEnabled(True)

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
