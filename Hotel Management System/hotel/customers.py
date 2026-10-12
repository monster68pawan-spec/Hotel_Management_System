import re
import sqlite3

from hotel.database import Database


PHONE_PATTERN = re.compile(r"^[0-9+(). -]{5,24}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_customer(name: str, phone: str, email: str) -> tuple[str, str, str]:
    name, phone, email = name.strip(), phone.strip(), email.strip()
    if not name or len(name) > 100:
        raise ValueError("Customer name is required and must be 100 characters or fewer.")
    if not PHONE_PATTERN.fullmatch(phone) or sum(character.isdigit() for character in phone) < 5:
        raise ValueError("Enter a valid phone number with at least five digits.")
    if email and (len(email) > 254 or not EMAIL_PATTERN.fullmatch(email)):
        raise ValueError("Enter a valid email address or leave it blank.")
    return name, phone, email


class CustomerService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, name: str, phone: str, email: str = "") -> dict:
        name, phone, email = _validate_customer(name, phone, email)
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)",
                (name, phone, email),
            )
            row = connection.execute(
                "SELECT * FROM customers WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def search(self, term: str = "") -> list[dict]:
        term = term.strip()
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT * FROM customers
                   WHERE ? = '' OR name LIKE ? ESCAPE '\\' COLLATE NOCASE
                      OR phone LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\'
                   ORDER BY name COLLATE NOCASE""",
                (term, pattern, pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def update(self, customer_id: int, name: str, phone: str, email: str = "") -> dict:
        name, phone, email = _validate_customer(name, phone, email)
        with self.database.connect() as connection:
            cursor = connection.execute(
                "UPDATE customers SET name = ?, phone = ?, email = ? WHERE id = ?",
                (name, phone, email, customer_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Customer no longer exists.")
            row = connection.execute(
                "SELECT * FROM customers WHERE id = ?", (customer_id,)
            ).fetchone()
        return dict(row)

    def delete(self, customer_id: int) -> None:
        try:
            with self.database.connect() as connection:
                cursor = connection.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
                if cursor.rowcount == 0:
                    raise ValueError("Customer no longer exists.")
        except sqlite3.IntegrityError as error:
            raise ValueError("This customer has booking history and cannot be deleted.") from error
