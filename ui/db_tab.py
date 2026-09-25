"""SQLite Migrate tab – convert Pa-O ASCII columns in a SQLite database."""
from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QProgressBar,
    QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt

from workers.db_worker import DbMigrateWorker

_DB_FILTER = "SQLite Database (*.db *.sqlite *.sqlite3)"


class DbMigrateTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: DbMigrateWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Source file
        src_row = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText("Path to source .db / .sqlite file…")
        self.src_edit.setReadOnly(True)
        src_browse = QPushButton("Browse…")
        src_browse.clicked.connect(self._browse_src)
        src_row.addWidget(self.src_edit)
        src_row.addWidget(src_browse)
        form.addRow("Source DB:", src_row)

        # Output file
        dst_row = QHBoxLayout()
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText("Path for output .db file…")
        self.dst_edit.setReadOnly(True)
        dst_browse = QPushButton("Browse…")
        dst_browse.clicked.connect(self._browse_dst)
        dst_row.addWidget(self.dst_edit)
        dst_row.addWidget(dst_browse)
        form.addRow("Output DB:", dst_row)

        # Table name
        self.table_edit = QLineEdit()
        self.table_edit.setPlaceholderText("e.g.  articles")
        form.addRow("Table:", self.table_edit)

        # Columns (comma-separated)
        self.cols_edit = QLineEdit()
        self.cols_edit.setPlaceholderText("e.g.  title, body")
        form.addRow("Text Columns:", self.cols_edit)

        layout.addLayout(form)

        # Convert button
        self.convert_btn = QPushButton("Migrate Database ▶")
        self.convert_btn.clicked.connect(self._on_migrate)
        layout.addWidget(self.convert_btn)

        # Progress + status
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    # ------------------------------------------------------------------

    def _browse_src(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Source Database", "", _DB_FILTER)
        if path:
            self.src_edit.setText(path)
            # Auto-suggest output path
            if not self.dst_edit.text():
                base, ext = os.path.splitext(path)
                self.dst_edit.setText(f"{base}_converted{ext}")

    def _browse_dst(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Output Database", "", _DB_FILTER)
        if path:
            self.dst_edit.setText(path)

    def _on_migrate(self) -> None:
        src = self.src_edit.text().strip()
        dst = self.dst_edit.text().strip()
        table = self.table_edit.text().strip()
        cols_raw = self.cols_edit.text().strip()

        if not src or not dst or not table or not cols_raw:
            QMessageBox.warning(self, "Missing Input", "Please fill in all fields before migrating.")
            return

        columns = [c.strip() for c in cols_raw.split(",") if c.strip()]
        if not columns:
            QMessageBox.warning(self, "Missing Input", "Enter at least one column name.")
            return

        self.convert_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status_label.setText("Migrating…")

        self._worker = DbMigrateWorker(src, dst, table, columns)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, message: str) -> None:
        self.progress.setValue(100)
        self.status_label.setText("Done ✓")
        self.convert_btn.setEnabled(True)
        QMessageBox.information(self, "Migration Complete", message)

    def _on_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self.status_label.setText("Failed ✗")
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "Migration Error", message)
