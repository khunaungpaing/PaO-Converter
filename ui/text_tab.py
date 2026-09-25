"""Text Convert tab – live ASCII → Unicode conversion with auto-preview."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QApplication, QLabel, QPushButton, QTextEdit, QSpinBox,
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

from core.engine import convert_pao_ascii_to_unicode
from utils.fonts import make_unicode_font
from .widgets import PlainTextFontEdit


class TextConvertTab(QWidget):
    def __init__(self, ascii_family: str, uni_family: str) -> None:
        super().__init__()
        self.ascii_family = ascii_family
        self.uni_family = uni_family

        # Debounce timer – converts 300 ms after the last keystroke
        self._convert_timer = QTimer()
        self._convert_timer.setSingleShot(True)
        self._convert_timer.setInterval(300)
        self._convert_timer.timeout.connect(self._do_convert)

        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setSpacing(12)

        # --- Input (ASCII) ---
        in_layout = QVBoxLayout()

        in_header = QHBoxLayout()
        in_header.addWidget(QLabel("<b>ASCII Text (Pa-O):</b>"))
        in_header.addStretch()
        in_header.addWidget(QLabel("Font size:"))
        self.input_size = QSpinBox()
        self.input_size.setRange(16, 130)
        self.input_size.setValue(36)
        self.input_size.setSuffix(" pt")
        self.input_size.valueChanged.connect(self._on_input_size_changed)
        in_header.addWidget(self.input_size)
        in_layout.addLayout(in_header)

        self.input_edit = PlainTextFontEdit()
        self.input_edit.setFont(QFont(self.ascii_family, self.input_size.value()))
        self.input_edit.textChanged.connect(self._on_input_changed)
        in_layout.addWidget(self.input_edit)

        in_footer = QHBoxLayout()
        self.input_count = QLabel("0 chars")
        self.input_count.setStyleSheet("color: #999; font-size: 11px;")
        in_footer.addWidget(self.input_count)
        in_footer.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.setToolTip("Clear both input and output")
        clear_btn.clicked.connect(self._on_clear)
        in_footer.addWidget(clear_btn)
        in_layout.addLayout(in_footer)

        root.addLayout(in_layout)

        # --- Output (Unicode) ---
        out_layout = QVBoxLayout()

        out_header = QHBoxLayout()
        out_header.addWidget(QLabel("<b>Unicode Text (Pa-O):</b>"))
        out_header.addStretch()
        out_header.addWidget(QLabel("Font size:"))
        self.output_size = QSpinBox()
        self.output_size.setRange(12, 120)
        self.output_size.setValue(30)
        self.output_size.setSuffix(" pt")
        self.output_size.valueChanged.connect(self._on_output_size_changed)
        out_header.addWidget(self.output_size)
        out_layout.addLayout(out_header)

        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setFont(
            make_unicode_font(self.uni_family, self.output_size.value())
        )
        self.output_edit.setStyleSheet("QTextEdit { line-height: 1.6; padding: 8px; }")
        out_layout.addWidget(self.output_edit)

        out_footer = QHBoxLayout()
        self.output_count = QLabel("0 chars")
        self.output_count.setStyleSheet("color: #999; font-size: 11px;")
        out_footer.addWidget(self.output_count)
        out_footer.addStretch()
        self.copy_btn = QPushButton("Copy Unicode Text")
        self.copy_btn.clicked.connect(self._on_copy)
        out_footer.addWidget(self.copy_btn)
        out_layout.addLayout(out_footer)

        root.addLayout(out_layout)

    # ------------------------------------------------------------------

    def _on_input_size_changed(self, size: int) -> None:
        self.input_edit.setFont(QFont(self.ascii_family, size))

    def _on_output_size_changed(self, size: int) -> None:
        self.output_edit.setFont(make_unicode_font(self.uni_family, size))

    def _on_input_changed(self) -> None:
        """Restart the debounce timer on every text change."""
        count = len(self.input_edit.toPlainText())
        self.input_count.setText(f"{count:,} chars")
        self._convert_timer.start()

    def _do_convert(self) -> None:
        """Run the actual conversion (called by the debounce timer)."""
        text = self.input_edit.toPlainText()
        result = convert_pao_ascii_to_unicode(text) if text else ""
        self.output_edit.setPlainText(result)
        self.output_count.setText(f"{len(result):,} chars")

    def _on_clear(self) -> None:
        self._convert_timer.stop()
        self.input_edit.clear()
        self.output_edit.clear()
        self.input_count.setText("0 chars")
        self.output_count.setText("0 chars")

    def _on_copy(self) -> None:
        text = self.output_edit.toPlainText()
        if not text:
            return
        QApplication.clipboard().setText(text)
        self.copy_btn.setText("Copied ✓")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy Unicode Text"))
