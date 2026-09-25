"""
Unit tests for migration.sqlite_migrator and migration.json_migrator.

Run with:
    python -m pytest tests/test_migration.py -v
or:
    python -m unittest tests.test_migration
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest

# Allow running from the project root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migration.sqlite_migrator import migrate_sqlite
from migration.json_migrator import migrate_json_file, migrate_json_value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(path: str, rows: list[tuple]) -> None:
    """Create a minimal test SQLite database with an 'articles' table."""
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE articles (id INTEGER PRIMARY KEY, title TEXT, body TEXT, views INTEGER)"
        )
        conn.executemany("INSERT INTO articles (title, body, views) VALUES (?,?,?)", rows)
        conn.commit()


# ---------------------------------------------------------------------------
# SQLite Migrator Tests
# ---------------------------------------------------------------------------

class TestSQLiteMigrator(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = os.path.join(self.tmp.name, "src.db")
        self.dst = os.path.join(self.tmp.name, "dst.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_basic_migration_returns_row_count(self):
        _make_db(self.src, [("hello", "world", 10), ("foo", "bar", 20)])
        count = migrate_sqlite(self.src, self.dst, "articles", ["title", "body"])
        self.assertEqual(count, 2)

    def test_output_file_is_created(self):
        _make_db(self.src, [("a", "b", 1)])
        migrate_sqlite(self.src, self.dst, "articles", ["title"])
        self.assertTrue(os.path.isfile(self.dst))

    def test_non_text_column_preserved(self):
        """Integer 'views' column must not be altered."""
        _make_db(self.src, [("title1", "body1", 42)])
        migrate_sqlite(self.src, self.dst, "articles", ["title"])
        with sqlite3.connect(self.dst) as conn:
            row = conn.execute("SELECT views FROM articles WHERE id=1").fetchone()
        self.assertEqual(row[0], 42)

    def test_null_values_are_preserved(self):
        """NULL text values must remain NULL after migration."""
        _make_db(self.src, [(None, None, 0)])
        migrate_sqlite(self.src, self.dst, "articles", ["title", "body"])
        with sqlite3.connect(self.dst) as conn:
            row = conn.execute("SELECT title, body FROM articles WHERE id=1").fetchone()
        self.assertIsNone(row[0])
        self.assertIsNone(row[1])

    def test_missing_source_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            migrate_sqlite("/nonexistent/path.db", self.dst, "articles", ["title"])

    def test_missing_table_raises(self):
        _make_db(self.src, [("a", "b", 1)])
        with self.assertRaises(ValueError):
            migrate_sqlite(self.src, self.dst, "no_such_table", ["title"])

    def test_missing_column_raises(self):
        _make_db(self.src, [("a", "b", 1)])
        with self.assertRaises(ValueError):
            migrate_sqlite(self.src, self.dst, "articles", ["no_such_col"])

    def test_chunked_migration(self):
        """Verify chunked processing handles more rows than chunk_size."""
        rows = [(f"title_{i}", f"body_{i}", i) for i in range(50)]
        _make_db(self.src, rows)
        count = migrate_sqlite(self.src, self.dst, "articles", ["title"], chunk_size=10)
        self.assertEqual(count, 50)

    def test_source_file_unchanged(self):
        """Source database must not be modified."""
        _make_db(self.src, [("original", "data", 1)])
        src_mtime_before = os.path.getmtime(self.src)
        migrate_sqlite(self.src, self.dst, "articles", ["title"])
        src_mtime_after = os.path.getmtime(self.src)
        self.assertEqual(src_mtime_before, src_mtime_after)


# ---------------------------------------------------------------------------
# JSON Migrator Tests
# ---------------------------------------------------------------------------

class TestJSONMigratorValue(unittest.TestCase):

    def test_plain_string_is_processed(self):
        # Any string goes through the converter; empty string returns empty.
        result = migrate_json_value("")
        self.assertEqual(result, "")

    def test_integer_unchanged(self):
        self.assertEqual(migrate_json_value(42), 42)

    def test_float_unchanged(self):
        self.assertAlmostEqual(migrate_json_value(3.14), 3.14)

    def test_bool_unchanged(self):
        self.assertIs(migrate_json_value(True), True)
        self.assertIs(migrate_json_value(False), False)

    def test_none_unchanged(self):
        self.assertIsNone(migrate_json_value(None))

    def test_dict_keys_preserved(self):
        data = {"key1": "", "key2": ""}
        result = migrate_json_value(data)
        self.assertIn("key1", result)
        self.assertIn("key2", result)

    def test_list_elements_processed(self):
        result = migrate_json_value(["", "", ""])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_nested_dict_in_list(self):
        data = [{"name": "hello", "score": 99}]
        result = migrate_json_value(data)
        self.assertEqual(result[0]["score"], 99)
        self.assertIsInstance(result[0]["name"], str)

    def test_deeply_nested_structure(self):
        data = {"a": {"b": {"c": {"d": "leaf"}}}}
        result = migrate_json_value(data)
        # Structure must be preserved; leaf must be a string.
        self.assertIsInstance(result["a"]["b"]["c"]["d"], str)

    def test_mixed_list_types_preserved(self):
        data = ["text", 1, True, None, 2.5]
        result = migrate_json_value(data)
        self.assertIsInstance(result[0], str)
        self.assertEqual(result[1], 1)
        self.assertIs(result[2], True)
        self.assertIsNone(result[3])
        self.assertAlmostEqual(result[4], 2.5)


class TestJSONMigratorFile(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _src(self, name: str) -> str:
        return os.path.join(self.tmp.name, name)

    def _write_json(self, name: str, data: object) -> str:
        path = self._src(name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        return path

    def test_output_file_created(self):
        src = self._write_json("in.json", {"k": "v"})
        dst = self._src("out.json")
        migrate_json_file(src, dst)
        self.assertTrue(os.path.isfile(dst))

    def test_output_is_valid_json(self):
        src = self._write_json("in.json", {"k": "v"})
        dst = self._src("out.json")
        migrate_json_file(src, dst)
        with open(dst, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIsInstance(data, dict)

    def test_output_utf8_no_ascii_escape(self):
        src = self._write_json("in.json", {"k": "hello"})
        dst = self._src("out.json")
        migrate_json_file(src, dst)
        raw = open(dst, encoding="utf-8").read()
        self.assertNotIn("\\u", raw)  # ensure_ascii=False

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            migrate_json_file("/no/such/file.json", self._src("out.json"))

    def test_invalid_json_raises(self):
        bad = self._src("bad.json")
        with open(bad, "w") as fh:
            fh.write("{not valid json")
        with self.assertRaises(ValueError):
            migrate_json_file(bad, self._src("out.json"))

    def test_array_root_supported(self):
        src = self._write_json("in.json", ["a", "b", "c"])
        dst = self._src("out.json")
        migrate_json_file(src, dst)
        with open(dst, encoding="utf-8") as fh:
            result = json.load(fh)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_numeric_values_preserved(self):
        src = self._write_json("in.json", {"count": 7, "ratio": 0.5, "flag": False})
        dst = self._src("out.json")
        migrate_json_file(src, dst)
        with open(dst, encoding="utf-8") as fh:
            result = json.load(fh)
        self.assertEqual(result["count"], 7)
        self.assertAlmostEqual(result["ratio"], 0.5)
        self.assertIs(result["flag"], False)


if __name__ == "__main__":
    unittest.main()
