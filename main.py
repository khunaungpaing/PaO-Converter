"""
Pa-O ASCII → Unicode Converter
Entry point: python main.py
"""

from __future__ import annotations

import os
import sys

# Allow sibling-package imports when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.version import APP_NAME, __version__
from ui.about_dialog import AboutDialog
from ui.file_tab import FileConvertTab
from ui.text_tab import TextConvertTab
from utils.fonts import load_application_fonts


def application_icon_path() -> str:
    """Return the native application-icon format for the current platform."""
    image_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "img"
    )
    if sys.platform == "darwin":
        icon_name = "app.icns"
    elif sys.platform.startswith("win"):
        icon_name = "app.ico"
    else:
        icon_name = "app.png"
    return os.path.join(image_dir, icon_name)


class MainWindow(QMainWindow):
    def __init__(self, ascii_family: str, uni_family: str, icon: QIcon) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.resize(980, 660)
        self.setWindowIcon(icon)

        # Setup Menu Bar
        self._build_menu()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        tabs = QTabWidget()
        tabs.addTab(TextConvertTab(ascii_family, uni_family), "Text Convert")
        tabs.addTab(FileConvertTab(), "File Convert")

        # Top-right corner About button for quick access
        about_btn = QPushButton("ⓘ About")
        about_btn.setToolTip("About Pa-O Converter & Version Info")
        is_dark = self.palette().window().color().lightness() < 128
        if is_dark:
            about_btn.setStyleSheet(
                "QPushButton {"
                "  border: 1px solid rgba(255, 255, 255, 0.18);"
                "  border-radius: 5px;"
                "  padding: 4px 12px;"
                "  background-color: rgba(255, 255, 255, 0.08);"
                "  color: #e6edf3;"
                "  font-size: 12px;"
                "  margin-right: 6px;"
                "}"
                "QPushButton:hover {"
                "  background-color: rgba(255, 255, 255, 0.16);"
                "  color: #ffffff;"
                "  border-color: rgba(255, 255, 255, 0.35);"
                "}"
            )
        else:
            about_btn.setStyleSheet(
                "QPushButton {"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 5px;"
                "  padding: 4px 12px;"
                "  background-color: #f6f8fa;"
                "  color: #24292f;"
                "  font-size: 12px;"
                "  margin-right: 6px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #eaeef2;"
                "  color: #0969da;"
                "  border-color: #afb8c1;"
                "}"
            )
        about_btn.clicked.connect(self._show_about)
        tabs.setCornerWidget(about_btn, Qt.Corner.TopRightCorner)

        layout.addWidget(tabs)

    def _build_menu(self) -> None:
        menubar = self.menuBar()
        help_menu = menubar.addMenu("&Help")

        about_action = QAction(f"About {APP_NAME}...", self)
        about_action.setStatusTip(f"Show information about {APP_NAME}")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self) -> None:
        dialog = AboutDialog(self)
        dialog.exec()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    icon = QIcon(application_icon_path())
    app.setWindowIcon(icon)

    ascii_family, uni_family = load_application_fonts()
    window = MainWindow(ascii_family, uni_family, icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
