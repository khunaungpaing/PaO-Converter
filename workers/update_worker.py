"""Background workers for checking and downloading updates in QThread."""
from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path
from threading import Event

from PyQt6.QtCore import QThread, pyqtSignal

from core.updater import ReleaseInfo, fetch_latest_release, get_default_download_path
from core.version import __version__


class CheckUpdateWorker(QThread):
    """Checks GitHub for newer releases in a background thread."""

    finished = pyqtSignal(object)  # Emits ReleaseInfo
    error = pyqtSignal(str)        # Emits error description

    def __init__(
        self,
        repo: str = "khunaungpaing/PaO-Converter",
        current_version: str = __version__,
        timeout: float = 10.0,
    ) -> None:
        super().__init__()
        self.repo = repo
        self.current_version = current_version
        self.timeout = timeout

    def run(self) -> None:
        try:
            info = fetch_latest_release(
                repo=self.repo,
                current_version=self.current_version,
                timeout=self.timeout,
            )
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class DownloadUpdateWorker(QThread):
    """Downloads an update asset chunk-by-chunk with progress reporting."""

    progress = pyqtSignal(int, int, float)  # downloaded_bytes, total_bytes, percentage (0-100)
    finished = pyqtSignal(str)              # local file path
    error = pyqtSignal(str)                 # error description
    cancelled = pyqtSignal()                # emitted on cancellation

    CHUNK_SIZE = 64 * 1024  # 64 KB

    def __init__(
        self,
        url: str,
        filename: str,
        expected_size: int = 0,
        destination_path: Path | None = None,
    ) -> None:
        super().__init__()
        self.url = url
        self.filename = filename
        self.expected_size = expected_size
        self.destination_path = (
            destination_path if destination_path is not None else get_default_download_path(filename)
        )
        self._cancel_event = Event()

    def cancel(self) -> None:
        """Signal cooperative cancellation of the download."""
        self._cancel_event.set()

    def run(self) -> None:
        req = urllib.request.Request(
            self.url,
            headers={"User-Agent": f"PaOConverter/{__version__}"},
        )

        dest = self.destination_path
        # Use a temporary partial file during download
        part_dest = dest.with_suffix(dest.suffix + ".part")

        try:
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)

            with urllib.request.urlopen(req, timeout=30.0) as response:
                content_length = response.headers.get("Content-Length")
                total_bytes = int(content_length) if content_length else self.expected_size
                downloaded_bytes = 0

                with open(part_dest, "wb") as f:
                    while True:
                        if self._cancel_event.is_set():
                            if part_dest.exists():
                                try:
                                    part_dest.unlink()
                                except OSError:
                                    pass
                            self.cancelled.emit()
                            return

                        chunk = response.read(self.CHUNK_SIZE)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded_bytes += len(chunk)

                        pct = (downloaded_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0
                        self.progress.emit(downloaded_bytes, total_bytes, min(pct, 100.0))

            # Atomic move from .part to final destination
            if part_dest.exists():
                part_dest.replace(dest)

            self.finished.emit(str(dest))

        except Exception as e:
            if part_dest.exists():
                try:
                    part_dest.unlink()
                except OSError:
                    pass
            if not self._cancel_event.is_set():
                self.error.emit(f"Download failed: {e}")
