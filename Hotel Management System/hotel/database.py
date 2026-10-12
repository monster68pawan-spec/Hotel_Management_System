import os
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY,
    number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    room_type TEXT NOT NULL,
    nightly_rate_cents INTEGER NOT NULL CHECK (nightly_rate_cents > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    nightly_rate_cents INTEGER NOT NULL CHECK (nightly_rate_cents > 0),
    status TEXT NOT NULL DEFAULT 'reserved'
        CHECK (status IN ('reserved', 'checked_in', 'checked_out', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (check_out > check_in)
);

CREATE INDEX IF NOT EXISTS bookings_room_dates
    ON bookings(room_id, check_in, check_out, status);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(id) ON DELETE RESTRICT,
    customer_name TEXT NOT NULL,
    room_number TEXT NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    nights INTEGER NOT NULL CHECK (nights > 0),
    nightly_rate_cents INTEGER NOT NULL CHECK (nightly_rate_cents > 0),
    total_cents INTEGER NOT NULL CHECK (total_cents > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)
        os.chmod(self.path, 0o600)

    def backup(self, destination: str | Path) -> None:
        destination_path = Path(destination)
        if destination_path.resolve() == self.path.resolve():
            raise ValueError("Backup destination must be different from the active database.")

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        source = self.connect()
        target = None
        try:
            target = sqlite3.connect(destination_path)
            source.backup(target)
        finally:
            source.close()
            if target is not None:
                target.close()
        os.chmod(destination_path, 0o600)
