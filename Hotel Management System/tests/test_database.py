import os
import stat
import tempfile
import unittest
from pathlib import Path

from hotel.database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "hotel.sqlite3")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_initialization_creates_relational_tables_and_enables_foreign_keys(self) -> None:
        self.database.initialize()
        with self.database.connect() as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertTrue({"users", "customers", "rooms", "bookings", "invoices"} <= tables)
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_initialization_is_repeatable(self) -> None:
        self.database.initialize()
        self.database.initialize()

        with self.database.connect() as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0],
                5,
            )

    def test_backup_preserves_database_contents_and_rejects_source_path(self) -> None:
        self.database.initialize()
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO customers (name, phone) VALUES (?, ?)",
                ("Jordan Lee", "5550100"),
            )

        backup_path = Path(self.temp_dir.name) / "backups" / "hotel-backup.sqlite3"
        self.database.backup(backup_path)

        backup = Database(backup_path)
        with backup.connect() as connection:
            customer = connection.execute(
                "SELECT name, phone FROM customers"
            ).fetchone()
        self.assertEqual(tuple(customer), ("Jordan Lee", "5550100"))
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(backup_path.stat().st_mode), 0o600)

        with self.assertRaisesRegex(ValueError, "different"):
            self.database.backup(self.database.path)

    @unittest.skipUnless(os.name == "posix", "POSIX file permissions are platform-specific")
    def test_database_file_is_readable_only_by_current_user(self) -> None:
        self.database.initialize()
        self.assertEqual(stat.S_IMODE(self.database.path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
