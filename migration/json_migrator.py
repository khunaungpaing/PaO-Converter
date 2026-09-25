"""
JSON File Migrator
------------------
Recursively traverses a JSON structure and converts every string *value*
from Pa-O ASCII (WinPaOh) to Myanmar Unicode.  Dict keys, numbers,
booleans, and None are left untouched.

Usage:
    from migration.json_migrator import migrate_json_file, migrate_json_value

    # File → File
    migrate_json_file("input.json", "output.json")

    # In-memory dict
    result = migrate_json_value({"name": "WinPaOhString", "age": 25})
"""

import json
import os
from typing import Any

from core.engine import convert_pao_ascii_to_unicode


def migrate_json_value(value: Any) -> Any:
    """
    Recursively convert all string values in *value* from Pa-O ASCII to Unicode.

    - str   → converted string
    - dict  → keys preserved, values recursed
    - list  → each element recursed
    - other → returned as-is (int, float, bool, None)
    """
    if isinstance(value, str):
        return convert_pao_ascii_to_unicode(value)
    if isinstance(value, dict):
        return {k: migrate_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [migrate_json_value(item) for item in value]
    return value


def migrate_json_file(src_path: str, dst_path: str) -> None:
    """
    Read *src_path*, convert all string values, and write to *dst_path*.

    Parameters
    ----------
    src_path : Path to the source JSON file.
    dst_path : Path for the output JSON file (created or overwritten).

    Raises
    ------
    FileNotFoundError : If *src_path* does not exist.
    ValueError        : If *src_path* contains invalid JSON.
    """
    if not os.path.isfile(src_path):
        raise FileNotFoundError(f"Source JSON file not found: {src_path!r}")

    with open(src_path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {src_path!r}: {exc}") from exc

    converted = migrate_json_value(data)

    with open(dst_path, "w", encoding="utf-8") as fh:
        json.dump(converted, fh, ensure_ascii=False, indent=2)
