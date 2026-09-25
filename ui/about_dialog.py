"""About & License Dialog for Pa-O Converter with Dark/Light mode support."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QTextBlockFormat, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.version import (
    APP_NAME,
    COPYRIGHT,
    DESCRIPTION,
    LICENSE_NAME,
    LICENSE_TEXT,
    WEBSITE,
    __version__,
)


class AboutDialog(QDialog):
    """Modern, adaptive About & License dialog supporting both Dark and Light themes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(530, 490)

        # Detect system theme (Dark vs Light)
        self._is_dark = self.palette().window().color().lightness() < 128

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Tab widget styling based on Dark/Light theme
        self.tabs = QTabWidget()

        if self._is_dark:
            self.tabs.setStyleSheet(
                "QTabWidget::pane {"
                "  border: 1px solid rgba(255, 255, 255, 0.12);"
                "  border-radius: 8px;"
                "  background-color: #242424;"
                "  top: -1px;"
                "}"
                "QTabBar::tab {"
                "  background-color: #1a1a1a;"
                "  border: 1px solid rgba(255, 255, 255, 0.1);"
                "  border-bottom: none;"
                "  padding: 7px 18px;"
                "  margin-right: 4px;"
                "  border-top-left-radius: 6px;"
                "  border-top-right-radius: 6px;"
                "  color: #a0a0a0;"
                "  font-weight: 500;"
                "}"
                "QTabBar::tab:selected {"
                "  background-color: #242424;"
                "  border-bottom-color: #242424;"
                "  color: #58a6ff;"
                "  font-weight: bold;"
                "}"
                "QTabBar::tab:hover:!selected {"
                "  background-color: #2c2c2c;"
                "  color: #e0e0e0;"
                "}"
            )
        else:
            self.tabs.setStyleSheet(
                "QTabWidget::pane {"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 8px;"
                "  background-color: #ffffff;"
                "  top: -1px;"
                "}"
                "QTabBar::tab {"
                "  background-color: #f6f8fa;"
                "  border: 1px solid #d0d7de;"
                "  border-bottom: none;"
                "  padding: 7px 18px;"
                "  margin-right: 4px;"
                "  border-top-left-radius: 6px;"
                "  border-top-right-radius: 6px;"
                "  color: #57606a;"
                "  font-weight: 500;"
                "}"
                "QTabBar::tab:selected {"
                "  background-color: #ffffff;"
                "  border-bottom-color: #ffffff;"
                "  color: #0969da;"
                "  font-weight: bold;"
                "}"
                "QTabBar::tab:hover:!selected {"
                "  background-color: #eaeef2;"
                "}"
            )

        self.tabs.addTab(self._create_about_tab(), "About")
        self.tabs.addTab(self._create_license_tab(), "Open Source License")
        layout.addWidget(self.tabs)

        # Bottom row with Close button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(90)
        close_btn.setFixedHeight(30)

        if self._is_dark:
            close_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #333333;"
                "  color: #ffffff;"
                "  border: 1px solid rgba(255, 255, 255, 0.15);"
                "  border-radius: 6px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: #404040;"
                "  border-color: rgba(255, 255, 255, 0.25);"
                "}"
            )
        else:
            close_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #f6f8fa;"
                "  color: #24292f;"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 6px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: #eaeef2;"
                "  border-color: #afb8c1;"
                "}"
            )

        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)
        layout.addLayout(bottom_layout)

    def _create_about_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        # Header: App Icon + Title & Badges
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_label = QLabel()
        icon_path = (
            Path(__file__).resolve().parents[1] / "assets" / "img" / "app.png"
        )
        if icon_path.is_file():
            pixmap = QPixmap(str(icon_path)).scaled(
                60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
        header_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = QLabel(f"<b>{APP_NAME}</b>")
        title_color = "#ffffff" if self._is_dark else "#1f2328"
        title_label.setStyleSheet(f"font-size: 19px; font-weight: bold; color: {title_color};")
        title_layout.addWidget(title_label)

        # Badges row (Version + License)
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(8)

        ver_badge = QLabel(f" v{__version__} ")
        if self._is_dark:
            ver_badge.setStyleSheet(
                "background-color: #172b4d; color: #58a6ff; border-radius: 4px; "
                "padding: 2px 7px; font-size: 11px; font-weight: bold;"
            )
        else:
            ver_badge.setStyleSheet(
                "background-color: #ddf4ff; color: #0969da; border-radius: 4px; "
                "padding: 2px 7px; font-size: 11px; font-weight: bold;"
            )
        badge_layout.addWidget(ver_badge)

        lic_badge = QLabel(f" {LICENSE_NAME} ")
        if self._is_dark:
            lic_badge.setStyleSheet(
                "background-color: #143520; color: #3fb950; border-radius: 4px; "
                "padding: 2px 7px; font-size: 11px; font-weight: bold;"
            )
        else:
            lic_badge.setStyleSheet(
                "background-color: #dafbe1; color: #1a7f37; border-radius: 4px; "
                "padding: 2px 7px; font-size: 11px; font-weight: bold;"
            )
        badge_layout.addWidget(lic_badge)
        badge_layout.addStretch()

        title_layout.addLayout(badge_layout)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Description with increased line-height
        desc_color = "#c9d1d9" if self._is_dark else "#3d444d"
        desc_label = QLabel(
            f'<div style="line-height: 150%; color: {desc_color}; font-size: 12.5px;">'
            f'{DESCRIPTION}'
            f'</div>'
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Key Features Card with increased line-height & comfortable spacing
        features_label = QLabel(
            '<div style="line-height: 150%; font-size: 11.5px;">'
            '<b>Key Features:</b>'
            '<div style="margin-top: 3px;">'
            '• Pa-O Win/ASCII → Pa-O Unicode (Experimental Version)<br>'
            '• Real-time interactive text conversion<br>'
            '• Word (.docx) & PDF (.pdf) documents with layout & font preservation'
            '</div>'
            '</div>'
        )
        if self._is_dark:
            features_label.setStyleSheet(
                "background-color: #1e1e1e; border: 1px solid rgba(255, 255, 255, 0.08); "
                "border-radius: 6px; padding: 10px 14px; color: #c9d1d9;"
            )
        else:
            features_label.setStyleSheet(
                "background-color: #f6f8fa; border: 1px solid #e1e4e8; "
                "border-radius: 6px; padding: 10px 14px; color: #333333;"
            )
        layout.addWidget(features_label)

        # Website & Copyright with increased line-height
        link_color = "#58a6ff" if self._is_dark else "#0969da"
        sub_text_color = "#8b949e" if self._is_dark else "#656d76"

        meta_label = QLabel(
            f'<div style="line-height: 170%; font-size: 12px;">'
            f'🌐 <b>Source Code:</b> <a href="{WEBSITE}" style="color: {link_color}; text-decoration: none;">GitHub Repository</a><br>'
            f'<span style="color: {sub_text_color}; font-size: 11px;">{COPYRIGHT}</span>'
            f'</div>'
        )
        meta_label.setOpenExternalLinks(True)
        layout.addWidget(meta_label)

        layout.addStretch()
        return widget

    def _create_license_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Subtitle and Copy button
        sub_layout = QHBoxLayout()
        sub_color = "#3fb950" if self._is_dark else "#1a7f37"
        sub_label = QLabel(f"<b>Free & Open Source Software</b> ({LICENSE_NAME})")
        sub_label.setStyleSheet(f"color: {sub_color}; font-size: 12px;")
        sub_layout.addWidget(sub_label)
        sub_layout.addStretch()

        copy_btn = QPushButton("Copy License")
        copy_btn.setFixedWidth(105)
        copy_btn.setFixedHeight(28)

        if self._is_dark:
            copy_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #333333;"
                "  color: #ffffff;"
                "  border: 1px solid rgba(255, 255, 255, 0.15);"
                "  border-radius: 5px;"
                "  font-size: 11px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: #404040;"
                "  border-color: rgba(255, 255, 255, 0.25);"
                "}"
            )
        else:
            copy_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #f6f8fa;"
                "  color: #24292f;"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 5px;"
                "  font-size: 11px;"
                "  font-weight: 500;"
                "}"
                "QPushButton:hover {"
                "  background-color: #eaeef2;"
                "  border-color: #afb8c1;"
                "}"
            )

        copy_btn.clicked.connect(lambda: self._copy_license(copy_btn))
        sub_layout.addWidget(copy_btn)

        layout.addLayout(sub_layout)

        # Read-only Monospace License Text Editor
        license_edit = QPlainTextEdit()
        license_edit.setPlainText(LICENSE_TEXT)
        license_edit.setReadOnly(True)
        font = QFont("Menlo", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        license_edit.setFont(font)

        if self._is_dark:
            license_edit.setStyleSheet(
                "QPlainTextEdit {"
                "  background-color: #1a1a1a;"
                "  color: #e6edf3;"
                "  border: 1px solid rgba(255, 255, 255, 0.1);"
                "  border-radius: 6px;"
                "  padding: 10px;"
                "  line-height: 1.35;"
                "}"
            )
        else:
            license_edit.setStyleSheet(
                "QPlainTextEdit {"
                "  background-color: #f6f8fa;"
                "  color: #24292f;"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 6px;"
                "  padding: 10px;"
                "  line-height: 1.35;"
                "}"
            )

        layout.addWidget(license_edit)

        return widget

    def _copy_license(self, button: QPushButton) -> None:
        QApplication.clipboard().setText(LICENSE_TEXT)
        original_text = button.text()
        button.setText("Copied ✓")
        QTimer.singleShot(1500, lambda: button.setText(original_text))
