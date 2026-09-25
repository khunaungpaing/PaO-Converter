"""Background worker for SQLite database migration."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from migration.sqlite_migrator import migrate_sqlite


class DbMigrateWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, src: str, dst: str, table: str, columns: list[str]) -> None:
        super().__init__()
        self.src = src
        self.dst = dst
        self.table = table
        self.columns = columns

    def run(self) -> None:
        try:
            self.progress.emit(10)
            count = migrate_sqlite(self.src, self.dst, self.table, self.columns)
            self.progress.emit(100)
            self.finished.emit(f"Migrated {count} row(s) → {self.dst}")
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))
