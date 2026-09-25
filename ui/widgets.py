"""Shared custom widgets with Dark/Light mode support."""
from __future__ import annotations

import os

from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PyQt6.QtWidgets import QLabel, QTextEdit


class PlainTextFontEdit(QTextEdit):
    """QTextEdit that strips HTML/RTF on paste, preserving only plain text."""

    def insertFromMimeData(self, source: QMimeData) -> None:  # type: ignore[override]
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)


_SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf"}


class DropZoneWidget(QLabel):
    """Theme-adaptive label that accepts file drag-and-drop with visual feedback.

    Emits ``fileDropped(str)`` with the absolute path when a supported
    file is dropped.
    """

    fileDropped = pyqtSignal(str)

    def __init__(
        self,
        placeholder: str = "Drag & drop a file here\nTXT · DOCX · PDF",
        parent: QLabel | None = None,
    ) -> None:
        super().__init__(placeholder, parent)
        self._placeholder = placeholder
        self._has_file = False
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(76)
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        self._apply_style("idle")

    def _is_dark(self) -> bool:
        return self.palette().window().color().lightness() < 128

    def _apply_style(self, state: str) -> None:
        is_dark = self._is_dark()
        if state == "hover":
            if is_dark:
                self.setStyleSheet(
                    "QLabel {"
                    "  border: 2px dashed #58a6ff;"
                    "  border-radius: 8px;"
                    "  padding: 18px;"
                    "  color: #58a6ff;"
                    "  background-color: rgba(88, 166, 255, 0.15);"
                    "}"
                )
            else:
                self.setStyleSheet(
                    "QLabel {"
                    "  border: 2px dashed #0969da;"
                    "  border-radius: 8px;"
                    "  padding: 18px;"
                    "  color: #0969da;"
                    "  background-color: #ddf4ff;"
                    "}"
                )
        elif state == "filled":
            if is_dark:
                self.setStyleSheet(
                    "QLabel {"
                    "  border: 2px solid #388bfd;"
                    "  border-radius: 8px;"
                    "  padding: 16px;"
                    "  color: #e6edf3;"
                    "  background-color: rgba(56, 139, 253, 0.12);"
                    "  font-weight: 500;"
                    "}"
                )
            else:
                self.setStyleSheet(
                    "QLabel {"
                    "  border: 2px solid #54aeff;"
                    "  border-radius: 8px;"
                    "  padding: 16px;"
                    "  color: #1f2328;"
                    "  background-color: #f0f7ff;"
                    "  font-weight: 500;"
                    "}"
                )
        else:  # idle
            if is_dark:
                self.setStyleSheet(
                    "QLabel {"
                    "  border: 2px dashed rgba(255, 255, 255, 0.2);"
                    "  border-radius: 8px;"
                    "  padding: 18px;"
                    "  color: #8b949e;"
                    "  background-color: rgba(255, 255, 255, 0.04);"
                    "}"
                )
            else:
                self.setStyleSheet(
                    "QLabel {"
                    "  border: 2px dashed #c0c4cc;"
                    "  border-radius: 8px;"
                    "  padding: 18px;"
                    "  color: #6e7781;"
                    "  background-color: #fafbfc;"
                    "}"
                )

    def reset(self) -> None:
        """Clear back to the placeholder state."""
        self._has_file = False
        self.setText(self._placeholder)
        self._apply_style("idle")

    def showFile(self, name: str) -> None:
        """Display the selected file name."""
        self._has_file = True
        self.setText(f"📄  {name}")
        self._apply_style("filled")

    # -- Drag-and-drop events ------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_supported(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self._apply_style("hover")
                return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._apply_style("filled" if self._has_file else "idle")

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if self._is_supported(path):
                event.acceptProposedAction()
                self.showFile(os.path.basename(path))
                self.fileDropped.emit(path)
                return
        event.ignore()
        self._apply_style("filled" if self._has_file else "idle")

    @staticmethod
    def _is_supported(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in _SUPPORTED_EXTENSIONS
