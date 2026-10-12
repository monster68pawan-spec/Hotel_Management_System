from datetime import date

from hotel.database import Database


class BillingService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def generate(self, booking_id: int) -> dict:
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM invoices WHERE booking_id = ?", (booking_id,)
            ).fetchone()
            if existing is not None:
                return dict(existing)

            booking = connection.execute(
                """SELECT bookings.*, customers.name AS customer_name,
                          rooms.number AS room_number
                   FROM bookings
                   JOIN customers ON customers.id = bookings.customer_id
                   JOIN rooms ON rooms.id = bookings.room_id
                   WHERE bookings.id = ?""",
                (booking_id,),
            ).fetchone()
            if booking is None:
                raise ValueError("Booking no longer exists.")
            if booking["status"] != "checked_out":
                raise ValueError("An invoice can only be generated after the guest has checked out.")

            nights = (
                date.fromisoformat(booking["check_out"])
                - date.fromisoformat(booking["check_in"])
            ).days
            total_cents = nights * booking["nightly_rate_cents"]
            cursor = connection.execute(
                """INSERT INTO invoices
                   (booking_id, customer_name, room_number, check_in, check_out,
                    nights, nightly_rate_cents, total_cents)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    booking_id,
                    booking["customer_name"],
                    booking["room_number"],
                    booking["check_in"],
                    booking["check_out"],
                    nights,
                    booking["nightly_rate_cents"],
                    total_cents,
                ),
            )
            invoice_id = cursor.lastrowid
        return self.get(invoice_id)

    def get(self, invoice_id: int) -> dict:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
            ).fetchone()
        if row is None:
            raise ValueError("Invoice no longer exists.")
        return dict(row)

    def for_booking(self, booking_id: int) -> dict | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM invoices WHERE booking_id = ?", (booking_id,)
            ).fetchone()
        return dict(row) if row else None

    def search(self, term: str = "") -> list[dict]:
        term = term.strip()
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT * FROM invoices
                   WHERE ? = '' OR customer_name LIKE ? ESCAPE '\\' COLLATE NOCASE
                      OR room_number LIKE ? ESCAPE '\\' COLLATE NOCASE
                   ORDER BY created_at DESC, id DESC""",
                (term, pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]
