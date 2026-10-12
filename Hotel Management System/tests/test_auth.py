import tempfile
import unittest
from pathlib import Path

from hotel.auth import AuthError, AuthService
from hotel.database import Database


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "hotel.sqlite3")
        self.database.initialize()
        self.auth = AuthService(self.database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_first_run_setup_stores_only_password_hash(self) -> None:
        self.assertFalse(self.auth.admin_exists())

        self.auth.create_admin("frontdesk", "secure-pass-123")

        self.assertTrue(self.auth.admin_exists())
        with self.database.connect() as connection:
            password_hash = connection.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                ("frontdesk",),
            ).fetchone()["password_hash"]
        self.assertNotEqual(password_hash, "secure-pass-123")
        self.assertTrue(password_hash.startswith("pbkdf2_sha256$"))

    def test_login_is_case_insensitive_and_rejects_invalid_password(self) -> None:
        self.auth.create_admin("frontdesk", "secure-pass-123")

        self.assertTrue(self.auth.login("FRONTDESK", "secure-pass-123"))
        with self.assertRaises(AuthError):
            self.auth.login("frontdesk", "wrong-password")

    def test_rejects_weak_password_and_second_admin_setup(self) -> None:
        with self.assertRaises(ValueError):
            self.auth.create_admin("frontdesk", "short")

        self.auth.create_admin("frontdesk", "secure-pass-123")
        with self.assertRaises(ValueError):
            self.auth.create_admin("another-user", "other-secure-123")


if __name__ == "__main__":
    unittest.main()
