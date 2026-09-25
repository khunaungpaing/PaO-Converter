"""
SQLite Data Migrator
--------------------
Reads records from a source SQLite table, converts specified text columns
from Pa-O ASCII (WinPaOh) to Myanmar Unicode, and writes the results to an
output SQLite database.

Usage:
    from migration.sqlite_migrator import migrate_sqlite

    migrate_sqlite(
        src_path="input.db",
        dst_path="output.db",
        table="articles",
        text_columns=["title", "body"],
        chunk_size=500,
    )
"""

import sqlite3
import shutil
import os
from typing import List, Sequence

from core.engine import convert_pao_ascii_to_unicode

_CHUNK_SIZE = 500


def _ensure_table_and_columns(
    cursor: sqlite3.Cursor, table: str, columns: Sequence[str]
) -> None:
    """Raise ValueError if the table or any requested column does not exist."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    if cursor.fetchone() is None:
        raise ValueError(f"Table '{table}' not found in database.")

    cursor.execute(f"PRAGMA table_info({table})")  # noqa: S608
    existing = {row[1] for row in cursor.fetchall()}
    missing = set(columns) - existing
    if missing:
        raise ValueError(f"Column(s) {missing} not found in table '{table}'.")


def migrate_sqlite(
    src_path: str,
    dst_path: str,
    table: str,
    text_columns: List[str],
    chunk_size: int = _CHUNK_SIZE,
) -> int:
    """
    Convert Pa-O ASCII text columns in *src_path* and write results to *dst_path*.

    Parameters
    ----------
    src_path    : Path to the source SQLite file.
    dst_path    : Path for the output SQLite file (created or overwritten).
    table       : Name of the table to migrate.
    text_columns: List of column names whose values should be converted.
    chunk_size  : Number of rows fetched per batch (default 500).

    Returns
    -------
    Total number of rows migrated.
    """
    if not os.path.isfile(src_path):
        raise FileNotFoundError(f"Source database not found: {src_path!r}")

    # Copy full schema + data to dst so non-converted columns are preserved.
    shutil.copy2(src_path, dst_path)

    total_rows = 0
    text_col_set = set(text_columns)

    with sqlite3.connect(dst_path) as dst_conn:
        # Use plain tuple rows; rowid is index 0 because we SELECT rowid first.
        cur = dst_conn.cursor()

        _ensure_table_and_columns(cur, table, text_columns)

        # Build column-index map from the table schema.
        cur.execute(f"PRAGMA table_info({table})")  # noqa: S608
        # +1 offset because index 0 is the rowid we prepend in the SELECT.
        col_index = {row[1]: row[0] + 1 for row in cur.fetchall()}

        set_clause = ", ".join(f"{col} = ?" for col in text_columns)
        update_sql = f"UPDATE {table} SET {set_clause} WHERE rowid = ?"  # noqa: S608

        cur.execute(f"SELECT rowid, * FROM {table}")  # noqa: S608
        while True:
            rows = cur.fetchmany(chunk_size)
            if not rows:
                break

            batch: List[tuple] = []
            for row in rows:
                row_id = row[0]  # rowid is always the first projected column
                converted_vals = [
                    convert_pao_ascii_to_unicode(row[col_index[col]])
                    if col in text_col_set and isinstance(row[col_index[col]], str)
                    else row[col_index[col]]
                    for col in text_columns
                ]
                batch.append((*converted_vals, row_id))

            dst_conn.executemany(update_sql, batch)
            total_rows += len(rows)

        dst_conn.commit()

    return total_rows
