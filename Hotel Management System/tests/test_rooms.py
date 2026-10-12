import tempfile
import unittest
from pathlib import Path

from hotel.database import Database
from hotel.rooms import RoomService


class RoomTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "hotel.sqlite3")
        self.database.initialize()
        self.rooms = RoomService(self.database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_room_crud_and_search(self) -> None:
        room = self.rooms.create(" 101 ", "Deluxe", "145.50")
        self.assertEqual(room["number"], "101")
        self.assertEqual(room["nightly_rate_cents"], 14550)
        self.assertEqual(len(self.rooms.search("del")), 1)
        updated = self.rooms.update(room["id"], "101", "Suite", "200")
        self.assertEqual(updated["room_type"], "Suite")
        self.assertEqual(updated["nightly_rate_cents"], 20000)
        self.rooms.delete(room["id"])
        self.assertEqual(self.rooms.search(), [])

    def test_room_rejects_invalid_number_type_and_rate(self) -> None:
        for number, room_type, rate in (
            (" ", "Standard", "100"),
            ("102", " ", "100"),
            ("102", "Standard", "0"),
            ("102", "Standard", "12.345"),
        ):
            with self.subTest(number=number, room_type=room_type, rate=rate):
                with self.assertRaises(ValueError):
                    self.rooms.create(number, room_type, rate)

    def test_availability_returns_only_rooms_without_date_overlap(self) -> None:
        available = self.rooms.create("101", "Standard", "100")
        occupied = self.rooms.create("102", "Deluxe", "150")
        with self.database.connect() as connection:
            customer_id = connection.execute(
                "INSERT INTO customers (name, phone) VALUES (?, ?)", ("Guest", "5550100")
            ).lastrowid
            booking_id = connection.execute(
                """INSERT INTO bookings
                   (customer_id, room_id, check_in, check_out, nightly_rate_cents, status)
                   VALUES (?, ?, ?, ?, 15000, 'reserved')""",
                (customer_id, occupied["id"], "2026-10-10", "2026-10-12"),
            ).lastrowid

        result = self.rooms.available("2026-10-12", "2026-10-14")
        self.assertEqual({room["id"] for room in result}, {available["id"], occupied["id"]})
        result = self.rooms.available("2026-10-11", "2026-10-13")
        self.assertEqual({room["id"] for room in result}, {available["id"]})
        result = self.rooms.available("2026-10-11", "2026-10-13", exclude_booking_id=booking_id)
        self.assertEqual({room["id"] for room in result}, {available["id"], occupied["id"]})


if __name__ == "__main__":
    unittest.main()
