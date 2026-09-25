"""JSON Migrate tab – recursively convert Pa-O ASCII string values in a JSON file."""

import os
import threading

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QProgressBar,
    QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal

from migration.json_migrator import migrate_json_file

_JSON_FILTER = "JSON Files (*.json)"


class _JsonWorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)


class JsonMigrateTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Source file
        src_row = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText("Path to source .json file…")
        self.src_edit.setReadOnly(True)
        src_browse = QPushButton("Browse…")
        src_browse.clicked.connect(self._browse_src)
        src_row.addWidget(self.src_edit)
        src_row.addWidget(src_browse)
        form.addRow("Source JSON:", src_row)

        # Output file
        dst_row = QHBoxLayout()
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText("Path for output .json file…")
        self.dst_edit.setReadOnly(True)
        dst_browse = QPushButton("Browse…")
        dst_browse.clicked.connect(self._browse_dst)
        dst_row.addWidget(self.dst_edit)
        dst_row.addWidget(dst_browse)
        form.addRow("Output JSON:", dst_row)

        layout.addLayout(form)

        self.convert_btn = QPushButton("Migrate JSON ▶")
        self.convert_btn.clicked.connect(self._on_migrate)
        layout.addWidget(self.convert_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)   # indeterminate spinner
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    # ------------------------------------------------------------------

    def _browse_src(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Source JSON", "", _JSON_FILTER)
        if path:
            self.src_edit.setText(path)
            if not self.dst_edit.text():
                base, ext = os.path.splitext(path)
                self.dst_edit.setText(f"{base}_converted{ext}")

    def _browse_dst(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", "", _JSON_FILTER)
        if path:
            self.dst_edit.setText(path)

    def _on_migrate(self) -> None:
        src = self.src_edit.text().strip()
        dst = self.dst_edit.text().strip()

        if not src or not dst:
            QMessageBox.warning(self, "Missing Input", "Please select both source and output files.")
            return

        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setText("Migrating…")

        signals = _JsonWorkerSignals()
        signals.finished.connect(self._on_finished)
        signals.error.connect(self._on_error)

        def _run() -> None:
            try:
                migrate_json_file(src, dst)
                signals.finished.emit(f"Saved to: {dst}")
            except Exception as exc:  # noqa: BLE001
                signals.error.emit(str(exc))

        # JSON migration is fast I/O — a plain thread is sufficient.
        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def _on_finished(self, message: str) -> None:
        self.progress.setVisible(False)
        self.status_label.setText("Done ✓")
        self.convert_btn.setEnabled(True)
        QMessageBox.information(self, "Migration Complete", message)

    def _on_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self.status_label.setText("Failed ✗")
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "Migration Error", message)
