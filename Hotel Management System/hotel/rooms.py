import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation

from hotel.database import Database


def _date_string(value: str | date) -> str:
    try:
        parsed = date.fromisoformat(value) if isinstance(value, str) else value
    except ValueError as error:
        raise ValueError("Enter dates in YYYY-MM-DD format.") from error
    if not isinstance(parsed, date):
        raise ValueError("Enter dates in YYYY-MM-DD format.")
    return parsed.isoformat()


def _validate_dates(check_in: str | date, check_out: str | date) -> tuple[str, str]:
    start, end = _date_string(check_in), _date_string(check_out)
    if end <= start:
        raise ValueError("Check-out must be after check-in.")
    return start, end


def _rate_to_cents(value: str | Decimal | int | float) -> int:
    try:
        rate = Decimal(str(value))
        cents = rate.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid nightly rate with up to two decimal places.") from None
    if not rate.is_finite() or rate <= 0 or rate != cents:
        raise ValueError("Nightly rate must be positive and have no more than two decimal places.")
    cents_value = int(cents * 100)
    if cents_value > 999_999_999:
        raise ValueError("Nightly rate is too large.")
    return cents_value


class RoomService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, number: str, room_type: str, nightly_rate: str | Decimal | int | float) -> dict:
        number, room_type = number.strip(), room_type.strip()
        if not number or len(number) > 20:
            raise ValueError("Room number is required and must be 20 characters or fewer.")
        if not room_type or len(room_type) > 50:
            raise ValueError("Room type is required and must be 50 characters or fewer.")
        rate = _rate_to_cents(nightly_rate)
        try:
            with self.database.connect() as connection:
                cursor = connection.execute(
                    "INSERT INTO rooms (number, room_type, nightly_rate_cents) VALUES (?, ?, ?)",
                    (number, room_type, rate),
                )
                row = connection.execute(
                    "SELECT * FROM rooms WHERE id = ?", (cursor.lastrowid,)
                ).fetchone()
        except sqlite3.IntegrityError as error:
            raise ValueError("That room number is already in use.") from error
        return dict(row)

    def search(self, term: str = "") -> list[dict]:
        term = term.strip()
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT * FROM rooms
                   WHERE ? = '' OR number LIKE ? ESCAPE '\\' COLLATE NOCASE
                      OR room_type LIKE ? ESCAPE '\\' COLLATE NOCASE
                   ORDER BY number COLLATE NOCASE""",
                (term, pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def update(
        self, room_id: int, number: str, room_type: str, nightly_rate: str | Decimal | int | float
    ) -> dict:
        number, room_type = number.strip(), room_type.strip()
        if not number or len(number) > 20:
            raise ValueError("Room number is required and must be 20 characters or fewer.")
        if not room_type or len(room_type) > 50:
            raise ValueError("Room type is required and must be 50 characters or fewer.")
        rate = _rate_to_cents(nightly_rate)
        try:
            with self.database.connect() as connection:
                cursor = connection.execute(
                    """UPDATE rooms SET number = ?, room_type = ?, nightly_rate_cents = ?
                       WHERE id = ?""",
                    (number, room_type, rate, room_id),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Room no longer exists.")
                row = connection.execute(
                    "SELECT * FROM rooms WHERE id = ?", (room_id,)
                ).fetchone()
        except sqlite3.IntegrityError as error:
            raise ValueError("That room number is already in use.") from error
        return dict(row)

    def delete(self, room_id: int) -> None:
        try:
            with self.database.connect() as connection:
                cursor = connection.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
                if cursor.rowcount == 0:
                    raise ValueError("Room no longer exists.")
        except sqlite3.IntegrityError as error:
            raise ValueError("This room has booking history and cannot be deleted.") from error

    def available(
        self,
        check_in: str | date,
        check_out: str | date,
        exclude_booking_id: int | None = None,
    ) -> list[dict]:
        start, end = _validate_dates(check_in, check_out)
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT rooms.* FROM rooms
                   WHERE NOT EXISTS (
                       SELECT 1 FROM bookings
                       WHERE bookings.room_id = rooms.id
                         AND bookings.status IN ('reserved', 'checked_in')
                         AND bookings.check_in < ?
                         AND bookings.check_out > ?
                         AND (? IS NULL OR bookings.id != ?)
                   )
                   ORDER BY rooms.number COLLATE NOCASE""",
                (end, start, exclude_booking_id, exclude_booking_id),
            ).fetchall()
        return [dict(row) for row in rows]
