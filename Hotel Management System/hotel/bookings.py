from datetime import date

from hotel.database import Database


def _stay_dates(check_in: str | date, check_out: str | date) -> tuple[str, str]:
    try:
        start = date.fromisoformat(check_in) if isinstance(check_in, str) else check_in
        end = date.fromisoformat(check_out) if isinstance(check_out, str) else check_out
    except ValueError as error:
        raise ValueError("Enter dates in YYYY-MM-DD format.") from error
    if not isinstance(start, date) or not isinstance(end, date):
        raise ValueError("Enter dates in YYYY-MM-DD format.")
    if end <= start:
        raise ValueError("Check-out must be after check-in.")
    return start.isoformat(), end.isoformat()


class BookingService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        customer_id: int,
        room_id: int,
        check_in: str | date,
        check_out: str | date,
    ) -> dict:
        start, end = _stay_dates(check_in, check_out)
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            customer = connection.execute(
                "SELECT id FROM customers WHERE id = ?", (customer_id,)
            ).fetchone()
            if customer is None:
                raise ValueError("Select an existing customer.")
            room = connection.execute(
                "SELECT id, nightly_rate_cents FROM rooms WHERE id = ?", (room_id,)
            ).fetchone()
            if room is None:
                raise ValueError("Select an existing room.")
            conflict = connection.execute(
                """SELECT 1 FROM bookings
                   WHERE room_id = ?
                     AND status IN ('reserved', 'checked_in')
                     AND check_in < ?
                     AND check_out > ?
                   LIMIT 1""",
                (room_id, end, start),
            ).fetchone()
            if conflict is not None:
                raise ValueError("Room is not available for those dates.")
            cursor = connection.execute(
                """INSERT INTO bookings
                   (customer_id, room_id, check_in, check_out, nightly_rate_cents)
                   VALUES (?, ?, ?, ?, ?)""",
                (customer_id, room_id, start, end, room["nightly_rate_cents"]),
            )
            booking_id = cursor.lastrowid
        return self.get(booking_id)

    def get(self, booking_id: int) -> dict:
        with self.database.connect() as connection:
            row = connection.execute(
                """SELECT bookings.*, customers.name AS customer_name,
                          customers.phone AS customer_phone, rooms.number AS room_number,
                          rooms.room_type AS room_type
                   FROM bookings
                   JOIN customers ON customers.id = bookings.customer_id
                   JOIN rooms ON rooms.id = bookings.room_id
                   WHERE bookings.id = ?""",
                (booking_id,),
            ).fetchone()
        if row is None:
            raise ValueError("Booking no longer exists.")
        return dict(row)

    def update(
        self,
        booking_id: int,
        customer_id: int,
        room_id: int,
        check_in: str | date,
        check_out: str | date,
    ) -> dict:
        start, end = _stay_dates(check_in, check_out)
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                """SELECT room_id, nightly_rate_cents FROM bookings
                   WHERE id = ? AND status = 'reserved'""",
                (booking_id,),
            ).fetchone()
            if current is None:
                exists = connection.execute(
                    "SELECT 1 FROM bookings WHERE id = ?", (booking_id,)
                ).fetchone()
                if exists is None:
                    raise ValueError("Booking no longer exists.")
                raise ValueError("Only reserved bookings can be edited.")
            if connection.execute(
                "SELECT 1 FROM customers WHERE id = ?", (customer_id,)
            ).fetchone() is None:
                raise ValueError("Select an existing customer.")
            room = connection.execute(
                "SELECT nightly_rate_cents FROM rooms WHERE id = ?", (room_id,)
            ).fetchone()
            if room is None:
                raise ValueError("Select an existing room.")
            conflict = connection.execute(
                """SELECT 1 FROM bookings
                   WHERE room_id = ? AND id != ?
                     AND status IN ('reserved', 'checked_in')
                     AND check_in < ? AND check_out > ?
                   LIMIT 1""",
                (room_id, booking_id, end, start),
            ).fetchone()
            if conflict is not None:
                raise ValueError("Room is not available for those dates.")
            rate = (
                current["nightly_rate_cents"]
                if current["room_id"] == room_id else room["nightly_rate_cents"]
            )
            connection.execute(
                """UPDATE bookings
                   SET customer_id = ?, room_id = ?, check_in = ?, check_out = ?,
                       nightly_rate_cents = ?
                   WHERE id = ?""",
                (customer_id, room_id, start, end, rate, booking_id),
            )
        return self.get(booking_id)

    def delete(self, booking_id: int) -> None:
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            booking = connection.execute(
                "SELECT status FROM bookings WHERE id = ?", (booking_id,)
            ).fetchone()
            if booking is None:
                raise ValueError("Booking no longer exists.")
            if booking["status"] != "reserved":
                raise ValueError("Only reserved bookings can be deleted; cancel completed history instead.")
            connection.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))

    def search(self, term: str = "") -> list[dict]:
        term = term.strip()
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT bookings.*, customers.name AS customer_name,
                          customers.phone AS customer_phone, rooms.number AS room_number,
                          rooms.room_type AS room_type
                   FROM bookings
                   JOIN customers ON customers.id = bookings.customer_id
                   JOIN rooms ON rooms.id = bookings.room_id
                   WHERE ? = '' OR customers.name LIKE ? ESCAPE '\\' COLLATE NOCASE
                      OR customers.phone LIKE ? ESCAPE '\\'
                      OR rooms.number LIKE ? ESCAPE '\\' COLLATE NOCASE
                      OR bookings.status LIKE ? ESCAPE '\\' COLLATE NOCASE
                   ORDER BY bookings.check_in DESC, bookings.id DESC""",
                (term, pattern, pattern, pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def _transition(self, booking_id: int, current: str, target: str) -> dict:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "UPDATE bookings SET status = ? WHERE id = ? AND status = ?",
                (target, booking_id, current),
            )
            if cursor.rowcount == 0:
                exists = connection.execute(
                    "SELECT 1 FROM bookings WHERE id = ?", (booking_id,)
                ).fetchone()
                if exists is None:
                    raise ValueError("Booking no longer exists.")
                raise ValueError(
                    f"Booking cannot be {target.replace('_', ' ')}; "
                    f"only {current.replace('_', ' ')} bookings can be {target.replace('_', ' ')}."
                )
        return self.get(booking_id)

    def check_in(self, booking_id: int) -> dict:
        return self._transition(booking_id, "reserved", "checked_in")

    def check_out(self, booking_id: int) -> dict:
        return self._transition(booking_id, "checked_in", "checked_out")

    def cancel(self, booking_id: int) -> dict:
        return self._transition(booking_id, "reserved", "cancelled")
