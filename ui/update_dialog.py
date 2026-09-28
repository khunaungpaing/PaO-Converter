"""Software Update Dialog for Pa-O Converter with Dark/Light mode support."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.updater import ReleaseAsset, ReleaseInfo
from core.version import APP_NAME, __version__
from workers.update_worker import CheckUpdateWorker, DownloadUpdateWorker


class UpdateDialog(QDialog):
    """Modern, adaptive software update dialog for Pa-O Converter."""

    STATE_CHECKING = 0
    STATE_UP_TO_DATE = 1
    STATE_UPDATE_AVAILABLE = 2
    STATE_DOWNLOADING = 3
    STATE_COMPLETE = 4
    STATE_ERROR = 5

    def __init__(
        self,
        parent: QWidget | None = None,
        release_info: ReleaseInfo | None = None,
        silent_mode: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Software Update — {APP_NAME}")
        self.setFixedSize(540, 480)

        self._is_dark = self.palette().window().color().lightness() < 128
        self._silent_mode = silent_mode
        self._release_info: ReleaseInfo | None = release_info
        self._downloaded_file: str | None = None

        self._check_worker: CheckUpdateWorker | None = None
        self._download_worker: DownloadUpdateWorker | None = None

        self._build_ui()

        if release_info is not None:
            if release_info.is_newer:
                self._show_update_available(release_info)
            else:
                self._show_up_to_date(release_info.version)
        else:
            self._start_check()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 18, 22, 18)
        main_layout.setSpacing(14)

        # Header area: App Icon + Titles
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        icon_label = QLabel()
        icon_path = (
            Path(__file__).resolve().parents[1] / "assets" / "img" / "app.png"
        )
        if icon_path.is_file():
            pixmap = QPixmap(str(icon_path)).scaled(
                54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
        header_layout.addWidget(icon_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        self.title_label = QLabel("Checking for Updates...")
        title_color = "#ffffff" if self._is_dark else "#1f2328"
        self.title_label.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {title_color};")
        title_col.addWidget(self.title_label)

        self.subtitle_label = QLabel("Connecting to GitHub Releases...")
        sub_color = "#8b949e" if self._is_dark else "#57606a"
        self.subtitle_label.setStyleSheet(f"font-size: 12px; color: {sub_color};")
        self.subtitle_label.setWordWrap(True)
        title_col.addWidget(self.subtitle_label)

        header_layout.addLayout(title_col)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Separator line
        sep = QLabel()
        sep.setFixedHeight(1)
        sep_color = "rgba(255, 255, 255, 0.12)" if self._is_dark else "#e1e4e8"
        sep.setStyleSheet(f"background-color: {sep_color};")
        main_layout.addWidget(sep)

        # Stacked pages for each state
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_checking_page())         # 0
        self.stack.addWidget(self._build_up_to_date_page())       # 1
        self.stack.addWidget(self._build_update_available_page())  # 2
        self.stack.addWidget(self._build_downloading_page())      # 3
        self.stack.addWidget(self._build_complete_page())         # 4
        self.stack.addWidget(self._build_error_page())            # 5
        main_layout.addWidget(self.stack, 1)

        # Bottom buttons layout
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(8)
        main_layout.addLayout(self.bottom_layout)

        self._update_buttons(self.STATE_CHECKING)

    # -------------------------------------------------------------------------
    # State Pages
    # -------------------------------------------------------------------------

    def _build_checking_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)

        self.checking_bar = QProgressBar()
        self.checking_bar.setRange(0, 0)  # Indeterminate animation
        self.checking_bar.setFixedHeight(6)
        self.checking_bar.setFixedWidth(320)
        self.checking_bar.setTextVisible(False)
        self._style_progress_bar(self.checking_bar)
        layout.addWidget(self.checking_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        msg = QLabel("Querying GitHub for the newest version...")
        msg.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(msg, alignment=Qt.AlignmentFlag.AlignCenter)
        return widget

    def _build_up_to_date_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        card = QWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(16, 14, 16, 14)

        if self._is_dark:
            card.setStyleSheet(
                "background-color: #1e1e1e; border: 1px solid rgba(255, 255, 255, 0.08); "
                "border-radius: 8px;"
            )
        else:
            card.setStyleSheet(
                "background-color: #f6f8fa; border: 1px solid #d0d7de; "
                "border-radius: 8px;"
            )

        badge_row = QHBoxLayout()
        check_badge = QLabel("✓ Up to date")
        if self._is_dark:
            check_badge.setStyleSheet(
                "background-color: #143520; color: #3fb950; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: bold;"
            )
        else:
            check_badge.setStyleSheet(
                "background-color: #dafbe1; color: #1a7f37; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: bold;"
            )
        badge_row.addWidget(check_badge)
        badge_row.addStretch()
        card_layout.addLayout(badge_row)

        desc = QLabel(
            f"<b>{APP_NAME} v{__version__}</b> is currently the newest version available.<br>"
            "You have all the latest character mappings, performance improvements, and bug fixes."
        )
        desc.setStyleSheet("font-size: 12.5px; line-height: 140%;")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _build_update_available_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(10)

        # Version & Asset info card
        info_card = QWidget()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(6)

        if self._is_dark:
            info_card.setStyleSheet(
                "background-color: #1e1e1e; border: 1px solid rgba(255, 255, 255, 0.08); "
                "border-radius: 6px;"
            )
        else:
            info_card.setStyleSheet(
                "background-color: #f6f8fa; border: 1px solid #e1e4e8; "
                "border-radius: 6px;"
            )

        self.version_diff_label = QLabel()
        self.version_diff_label.setStyleSheet("font-size: 12.5px; font-weight: 500;")
        info_layout.addWidget(self.version_diff_label)

        self.asset_info_label = QLabel()
        sub_color = "#8b949e" if self._is_dark else "#57606a"
        self.asset_info_label.setStyleSheet(f"font-size: 11.5px; color: {sub_color};")
        info_layout.addWidget(self.asset_info_label)

        layout.addWidget(info_card)

        # Release notes section
        notes_hdr = QLabel("<b>What's New:</b>")
        notes_hdr.setStyleSheet("font-size: 12px;")
        layout.addWidget(notes_hdr)

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setReadOnly(True)
        font = QFont()
        font.setPointSize(10)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        self.notes_edit.setFont(font)

        if self._is_dark:
            self.notes_edit.setStyleSheet(
                "QPlainTextEdit {"
                "  background-color: #161b22;"
                "  color: #c9d1d9;"
                "  border: 1px solid rgba(255, 255, 255, 0.1);"
                "  border-radius: 6px;"
                "  padding: 8px;"
                "  line-height: 1.4;"
                "}"
            )
        else:
            self.notes_edit.setStyleSheet(
                "QPlainTextEdit {"
                "  background-color: #ffffff;"
                "  color: #24292f;"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 6px;"
                "  padding: 8px;"
                "  line-height: 1.4;"
                "}"
            )
        layout.addWidget(self.notes_edit, 1)

        return widget

    def _build_downloading_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)

        self.download_file_label = QLabel("Downloading update installer...")
        self.download_file_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        layout.addWidget(self.download_file_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.download_bar = QProgressBar()
        self.download_bar.setRange(0, 100)
        self.download_bar.setValue(0)
        self.download_bar.setFixedHeight(12)
        self.download_bar.setFixedWidth(360)
        self._style_progress_bar(self.download_bar)
        layout.addWidget(self.download_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.download_status_label = QLabel("0% (0 MB / 0 MB)")
        sub_color = "#8b949e" if self._is_dark else "#57606a"
        self.download_status_label.setStyleSheet(f"font-size: 11.5px; color: {sub_color};")
        layout.addWidget(self.download_status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        return widget

    def _build_complete_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        card = QWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(16, 14, 16, 14)

        if self._is_dark:
            card.setStyleSheet(
                "background-color: #1e1e1e; border: 1px solid rgba(255, 255, 255, 0.08); "
                "border-radius: 8px;"
            )
        else:
            card.setStyleSheet(
                "background-color: #f6f8fa; border: 1px solid #d0d7de; "
                "border-radius: 8px;"
            )

        badge_row = QHBoxLayout()
        done_badge = QLabel("✓ Download Ready")
        if self._is_dark:
            done_badge.setStyleSheet(
                "background-color: #143520; color: #3fb950; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: bold;"
            )
        else:
            done_badge.setStyleSheet(
                "background-color: #dafbe1; color: #1a7f37; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: bold;"
            )
        badge_row.addWidget(done_badge)
        badge_row.addStretch()
        card_layout.addLayout(badge_row)

        self.complete_desc = QLabel()
        self.complete_desc.setStyleSheet("font-size: 12.5px; line-height: 140%;")
        self.complete_desc.setWordWrap(True)
        card_layout.addWidget(self.complete_desc)

        self.saved_path_label = QLabel()
        sub_color = "#8b949e" if self._is_dark else "#57606a"
        self.saved_path_label.setStyleSheet(f"font-size: 11px; color: {sub_color};")
        self.saved_path_label.setWordWrap(True)
        card_layout.addWidget(self.saved_path_label)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _build_error_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        card = QWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(16, 14, 16, 14)

        if self._is_dark:
            card.setStyleSheet(
                "background-color: #271d1d; border: 1px solid rgba(255, 120, 120, 0.2); "
                "border-radius: 8px;"
            )
        else:
            card.setStyleSheet(
                "background-color: #fff8f8; border: 1px solid #f85149; "
                "border-radius: 8px;"
            )

        err_badge = QLabel("⚠ Notice")
        if self._is_dark:
            err_badge.setStyleSheet(
                "background-color: #491818; color: #ff7b72; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: bold;"
            )
        else:
            err_badge.setStyleSheet(
                "background-color: #ffebe9; color: #cf222e; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: bold;"
            )
        card_layout.addWidget(err_badge)

        self.error_desc_label = QLabel("Unable to connect to GitHub releases.")
        self.error_desc_label.setStyleSheet("font-size: 12px; line-height: 140%;")
        self.error_desc_label.setWordWrap(True)
        card_layout.addWidget(self.error_desc_label)

        hint = QLabel(
            "Please check your internet connection, or you can manually download the latest "
            "release directly from the GitHub releases page."
        )
        sub_color = "#8b949e" if self._is_dark else "#57606a"
        hint.setStyleSheet(f"font-size: 11.5px; color: {sub_color};")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    # -------------------------------------------------------------------------
    # Stylesheet Helpers
    # -------------------------------------------------------------------------

    def _style_progress_bar(self, bar: QProgressBar) -> None:
        if self._is_dark:
            bar.setStyleSheet(
                "QProgressBar {"
                "  border: 1px solid rgba(255, 255, 255, 0.12);"
                "  border-radius: 4px;"
                "  background-color: #161b22;"
                "  text-align: center;"
                "}"
                "QProgressBar::chunk {"
                "  background-color: #238636;"
                "  border-radius: 3px;"
                "}"
            )
        else:
            bar.setStyleSheet(
                "QProgressBar {"
                "  border: 1px solid #d0d7de;"
                "  border-radius: 4px;"
                "  background-color: #eaeef2;"
                "  text-align: center;"
                "}"
                "QProgressBar::chunk {"
                "  background-color: #1f883d;"
                "  border-radius: 3px;"
                "}"
            )

    def _style_button(self, btn: QPushButton, variant: str = "default") -> None:
        if variant == "primary":
            if self._is_dark:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #238636; color: #ffffff;"
                    "  border: 1px solid rgba(255, 255, 255, 0.2);"
                    "  border-radius: 6px; padding: 6px 14px; font-weight: 600; font-size: 12px;"
                    "}"
                    "QPushButton:hover { background-color: #2ea043; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #1f883d; color: #ffffff;"
                    "  border: 1px solid rgba(27, 31, 36, 0.15);"
                    "  border-radius: 6px; padding: 6px 14px; font-weight: 600; font-size: 12px;"
                    "}"
                    "QPushButton:hover { background-color: #1a7f37; }"
                )
        else:
            if self._is_dark:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #30363d; color: #c9d1d9;"
                    "  border: 1px solid rgba(255, 255, 255, 0.12);"
                    "  border-radius: 6px; padding: 6px 14px; font-size: 12px;"
                    "}"
                    "QPushButton:hover { background-color: #3c444d; color: #ffffff; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #f6f8fa; color: #24292f;"
                    "  border: 1px solid #d0d7de;"
                    "  border-radius: 6px; padding: 6px 14px; font-size: 12px;"
                    "}"
                    "QPushButton:hover { background-color: #eaeef2; border-color: #afb8c1; }"
                )

    # -------------------------------------------------------------------------
    # Button Bar Updates
    # -------------------------------------------------------------------------

    def _update_buttons(self, state: int) -> None:
        # Clear existing buttons
        while self.bottom_layout.count():
            item = self.bottom_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if state == self.STATE_CHECKING:
            self.bottom_layout.addStretch()
            cancel_btn = QPushButton("Cancel")
            self._style_button(cancel_btn, "default")
            cancel_btn.clicked.connect(self.reject)
            self.bottom_layout.addWidget(cancel_btn)

        elif state == self.STATE_UP_TO_DATE:
            self.bottom_layout.addStretch()
            close_btn = QPushButton("OK")
            self._style_button(close_btn, "primary")
            close_btn.clicked.connect(self.accept)
            self.bottom_layout.addWidget(close_btn)

        elif state == self.STATE_UPDATE_AVAILABLE:
            later_btn = QPushButton("Later")
            self._style_button(later_btn, "default")
            later_btn.clicked.connect(self.reject)
            self.bottom_layout.addWidget(later_btn)

            self.bottom_layout.addStretch()

            web_btn = QPushButton("View on GitHub")
            self._style_button(web_btn, "default")
            web_btn.clicked.connect(self._open_web_release)
            self.bottom_layout.addWidget(web_btn)

            # Only show Download button if an asset exists for current platform
            if self._release_info and self._release_info.asset:
                download_btn = QPushButton("Download & Update")
                self._style_button(download_btn, "primary")
                download_btn.clicked.connect(self._start_download)
                self.bottom_layout.addWidget(download_btn)

        elif state == self.STATE_DOWNLOADING:
            self.bottom_layout.addStretch()
            cancel_download_btn = QPushButton("Cancel Download")
            self._style_button(cancel_download_btn, "default")
            cancel_download_btn.clicked.connect(self._cancel_download)
            self.bottom_layout.addWidget(cancel_download_btn)

        elif state == self.STATE_COMPLETE:
            later_btn = QPushButton("Close")
            self._style_button(later_btn, "default")
            later_btn.clicked.connect(self.accept)
            self.bottom_layout.addWidget(later_btn)

            self.bottom_layout.addStretch()

            folder_btn = QPushButton("Show in Folder")
            self._style_button(folder_btn, "default")
            folder_btn.clicked.connect(self._show_download_folder)
            self.bottom_layout.addWidget(folder_btn)

            action_text = "Install & Restart" if sys.platform.startswith("win") else "Open Installer"
            install_btn = QPushButton(action_text)
            self._style_button(install_btn, "primary")
            install_btn.clicked.connect(self._install_and_launch)
            self.bottom_layout.addWidget(install_btn)

        elif state == self.STATE_ERROR:
            self.bottom_layout.addStretch()
            close_btn = QPushButton("Close")
            self._style_button(close_btn, "default")
            close_btn.clicked.connect(self.reject)
            self.bottom_layout.addWidget(close_btn)

            web_btn = QPushButton("Open GitHub Releases")
            self._style_button(web_btn, "primary")
            web_btn.clicked.connect(self._open_web_release)
            self.bottom_layout.addWidget(web_btn)

    # -------------------------------------------------------------------------
    # Actions & Logic
    # -------------------------------------------------------------------------

    def _start_check(self) -> None:
        self.stack.setCurrentIndex(self.STATE_CHECKING)
        self._update_buttons(self.STATE_CHECKING)

        self._check_worker = CheckUpdateWorker(current_version=__version__)
        self._check_worker.finished.connect(self._on_check_finished)
        self._check_worker.error.connect(self._on_check_error)
        self._check_worker.start()

    def _on_check_finished(self, info: ReleaseInfo) -> None:
        self._release_info = info
        if info.is_newer:
            if self._silent_mode and not self.isVisible():
                self.show()
            self._show_update_available(info)
        else:
            if self._silent_mode:
                self.close()
                return
            self._show_up_to_date(info.version)

    def _on_check_error(self, error_msg: str) -> None:
        if self._silent_mode:
            self.close()
            return
        self.title_label.setText("Update Check Failed")
        self.subtitle_label.setText("Could not contact GitHub releases.")
        self.error_desc_label.setText(error_msg)
        self.stack.setCurrentIndex(self.STATE_ERROR)
        self._update_buttons(self.STATE_ERROR)

    def _show_up_to_date(self, version: str) -> None:
        self.title_label.setText("You're Up to Date!")
        self.subtitle_label.setText(f"{APP_NAME} v{version} is currently the newest version.")
        self.stack.setCurrentIndex(self.STATE_UP_TO_DATE)
        self._update_buttons(self.STATE_UP_TO_DATE)

    def _show_update_available(self, info: ReleaseInfo) -> None:
        self.title_label.setText(f"New Version Available: v{info.version}")
        self.subtitle_label.setText(f"A new update of {APP_NAME} is available to download.")

        self.version_diff_label.setText(
            f"<b>Current Version:</b> v{info.current_version} &nbsp; ➔ &nbsp; "
            f"<b>New Version:</b> <span style='color: #2da44e;'>v{info.version}</span>"
        )

        if info.asset:
            self.asset_info_label.setText(
                f"<b>Package:</b> {info.asset.name} &nbsp; ({info.asset.size_str})"
            )
        else:
            self.asset_info_label.setText(
                "<i>No standalone binary found for your OS. Visit GitHub to download source.</i>"
            )

        self.notes_edit.setPlainText(info.body)
        self.stack.setCurrentIndex(self.STATE_UPDATE_AVAILABLE)
        self._update_buttons(self.STATE_UPDATE_AVAILABLE)

    def _start_download(self) -> None:
        if not self._release_info or not self._release_info.asset:
            return

        asset = self._release_info.asset
        self.title_label.setText("Downloading Update...")
        self.subtitle_label.setText(f"Downloading {asset.name}...")
        self.download_file_label.setText(f"Downloading {asset.name}")
        self.download_bar.setValue(0)
        self.download_status_label.setText(f"0% (0.0 MB / {asset.size_str})")

        self.stack.setCurrentIndex(self.STATE_DOWNLOADING)
        self._update_buttons(self.STATE_DOWNLOADING)

        self._download_worker = DownloadUpdateWorker(
            url=asset.download_url,
            filename=asset.name,
            expected_size=asset.size,
        )
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.error.connect(self._on_download_error)
        self._download_worker.cancelled.connect(self._on_download_cancelled)
        self._download_worker.start()

    def _on_download_progress(self, downloaded: int, total: int, pct: float) -> None:
        self.download_bar.setValue(int(pct))
        down_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        self.download_status_label.setText(f"{pct:.1f}% ({down_mb:.1f} MB / {tot_mb:.1f} MB)")

    def _on_download_finished(self, file_path: str) -> None:
        self._downloaded_file = file_path
        self.title_label.setText("Update Ready to Install")
        self.subtitle_label.setText("The new version has been downloaded successfully.")

        if sys.platform.startswith("win"):
            self.complete_desc.setText(
                f"<b>{Path(file_path).name}</b> is ready to install.<br><br>"
                "Click <b>Install & Restart</b> to launch the setup wizard. "
                "Pa-O Converter will close while the installer upgrades your installation."
            )
        else:
            self.complete_desc.setText(
                f"<b>{Path(file_path).name}</b> is ready.<br><br>"
                "Click <b>Open Installer</b> to mount the disk image, then drag the application "
                "to your Applications folder to replace the older version."
            )

        self.saved_path_label.setText(f"<b>Saved to:</b> {file_path}")
        self.stack.setCurrentIndex(self.STATE_COMPLETE)
        self._update_buttons(self.STATE_COMPLETE)

    def _on_download_error(self, err_msg: str) -> None:
        self.title_label.setText("Download Failed")
        self.subtitle_label.setText("Could not complete downloading update.")
        self.error_desc_label.setText(err_msg)
        self.stack.setCurrentIndex(self.STATE_ERROR)
        self._update_buttons(self.STATE_ERROR)

    def _on_download_cancelled(self) -> None:
        if self._release_info:
            self._show_update_available(self._release_info)

    def _cancel_download(self) -> None:
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.cancel()

    def _open_web_release(self) -> None:
        url = (
            self._release_info.html_url
            if self._release_info
            else f"https://github.com/khunaungpaing/PaO-Converter/releases/latest"
        )
        QDesktopServices.openUrl(QUrl(url))

    def _show_download_folder(self) -> None:
        if not self._downloaded_file:
            return
        folder = Path(self._downloaded_file).parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _install_and_launch(self) -> None:
        if not self._downloaded_file or not os.path.exists(self._downloaded_file):
            return

        file_path = self._downloaded_file

        if sys.platform.startswith("win"):
            # Launch Inno Setup installer executable and exit app
            subprocess.Popen([file_path], shell=False)
            QApplication.quit()
        elif sys.platform == "darwin":
            # Mount disk image and open Finder window
            subprocess.Popen(["open", file_path])
            self.accept()
        else:
            # Generic Linux open
            subprocess.Popen(["xdg-open", file_path])
            self.accept()

    def closeEvent(self, event) -> None:
        # Ensure any background workers stop cleanly
        if self._check_worker and self._check_worker.isRunning():
            self._check_worker.terminate()
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.cancel()
        super().closeEvent(event)
