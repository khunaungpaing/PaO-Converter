"""Shared custom widgets with Dark/Light mode support."""
from __future__ import annotations

import os

from PyQt6.QtCore import QEvent, QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QMouseEvent
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
    file is dropped, or ``clicked()`` when clicked.
    """

    fileDropped = pyqtSignal(str)
    clicked = pyqtSignal()

    def __init__(
        self,
        placeholder: str = "Drag & drop a file here\nTXT · DOCX · PDF\n(or click to browse)",
        parent: QLabel | None = None,
    ) -> None:
        super().__init__(placeholder, parent)
        self._placeholder = placeholder
        self._has_file = False
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(76)
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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

    def showFile(self, path: str) -> None:
        """Display the selected file name and size with clear re-selection hint."""
        self._has_file = True
        name = os.path.basename(path)
        size_str = ""
        if os.path.isfile(path):
            try:
                sz = os.path.getsize(path)
                if sz < 1024:
                    size_str = f"{sz} B"
                elif sz < 1024 * 1024:
                    size_str = f"{sz / 1024:.1f} KB"
                else:
                    size_str = f"{sz / (1024 * 1024):.1f} MB"
            except OSError:
                pass

        sub_info = f" ({size_str})" if size_str else ""
        sub_color = "#8b949e" if self._is_dark() else "#57606a"
        self.setText(
            f"<div style='line-height: 140%;'>"
            f"<span style='font-size: 14px; font-weight: 600;'>📄  {name}{sub_info}</span><br>"
            f"<span style='font-size: 12px; color: {sub_color};'>Click to change file or drag another here</span>"
            f"</div>"
        )
        self._apply_style("filled")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.isEnabled():
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.EnabledChange:
            self.setCursor(
                Qt.CursorShape.PointingHandCursor if self.isEnabled() else Qt.CursorShape.ArrowCursor
            )
        super().changeEvent(event)

    # -- Drag-and-drop events ------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if not self.isEnabled() or not self.acceptDrops():
            event.ignore()
            return
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_supported(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self._apply_style("hover")
                return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        if not self.isEnabled() or not self.acceptDrops():
            return
        self._apply_style("filled" if self._has_file else "idle")

    def dropEvent(self, event: QDropEvent) -> None:
        if not self.isEnabled() or not self.acceptDrops():
            event.ignore()
            return
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if self._is_supported(path):
                event.acceptProposedAction()
                self.showFile(path)
                self.fileDropped.emit(path)
                return
        event.ignore()
        self._apply_style("filled" if self._has_file else "idle")

    @staticmethod
    def _is_supported(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in _SUPPORTED_EXTENSIONS
