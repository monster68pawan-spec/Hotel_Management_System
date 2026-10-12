import hashlib
import hmac
import re
import secrets

from hotel.database import Database


ITERATIONS = 600_000
PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 1024
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


class AuthError(Exception):
    """Raised when an operator cannot be authenticated."""


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(rounds)
        if not 100_000 <= iterations <= 2_000_000:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


class AuthService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def admin_exists(self) -> bool:
        with self.database.connect() as connection:
            return connection.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None

    def create_admin(self, username: str, password: str) -> None:
        username = username.strip()
        if not USERNAME_PATTERN.fullmatch(username):
            raise ValueError("Username must be 3–32 letters, numbers, dots, dashes, or underscores.")
        if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
            raise ValueError(f"Password must be {PASSWORD_MIN_LENGTH}–{PASSWORD_MAX_LENGTH} characters.")

        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM users LIMIT 1").fetchone():
                raise ValueError("The administrator account has already been created.")
            connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, _hash_password(password)),
            )

    def login(self, username: str, password: str) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()

        if row is None or not _verify_password(password, row["password_hash"]):
            raise AuthError("Username or password is incorrect.")
        return True
