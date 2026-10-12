import tempfile
import unittest
from pathlib import Path

from hotel.bookings import BookingService
from hotel.customers import CustomerService
from hotel.database import Database
from hotel.rooms import RoomService


class BookingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "hotel.sqlite3")
        self.database.initialize()
        self.customers = CustomerService(self.database)
        self.rooms = RoomService(self.database)
        self.bookings = BookingService(self.database)
        self.customer = self.customers.create("Jordan Lee", "5550100")
        self.room = self.rooms.create("101", "Standard", "125.00")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_booking_snapshots_rate_and_rejects_overlapping_dates(self) -> None:
        booking = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-10", "2026-10-12"
        )
        self.assertEqual(booking["nightly_rate_cents"], 12500)
        with self.assertRaisesRegex(ValueError, "not available"):
            self.bookings.create(
                self.customer["id"], self.room["id"], "2026-10-11", "2026-10-13"
            )
        adjoining = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-12", "2026-10-14"
        )
        self.assertEqual(adjoining["status"], "reserved")

    def test_booking_search_check_in_check_out_and_cancel(self) -> None:
        booking = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-10", "2026-10-12"
        )
        self.assertEqual(len(self.bookings.search("Jordan")), 1)
        self.assertEqual(self.bookings.check_in(booking["id"])["status"], "checked_in")
        self.assertEqual(self.bookings.check_out(booking["id"])["status"], "checked_out")
        with self.assertRaisesRegex(ValueError, "cannot be checked in"):
            self.bookings.check_in(booking["id"])

        other = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-12", "2026-10-14"
        )
        self.assertEqual(self.bookings.cancel(other["id"])["status"], "cancelled")

    def test_reserved_booking_can_be_updated_but_not_into_a_conflict(self) -> None:
        booking = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-10", "2026-10-12"
        )
        other = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-12", "2026-10-14"
        )

        updated = self.bookings.update(
            booking["id"], self.customer["id"], self.room["id"], "2026-10-09", "2026-10-10"
        )
        self.assertEqual(updated["check_in"], "2026-10-09")
        self.assertEqual(updated["nightly_rate_cents"], 12500)
        with self.assertRaisesRegex(ValueError, "not available"):
            self.bookings.update(
                booking["id"], self.customer["id"], self.room["id"], "2026-10-11", "2026-10-13"
            )
        self.assertEqual(self.bookings.get(other["id"])["status"], "reserved")

    def test_only_reserved_booking_can_be_deleted(self) -> None:
        booking = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-10", "2026-10-12"
        )
        self.bookings.delete(booking["id"])
        with self.assertRaisesRegex(ValueError, "no longer exists"):
            self.bookings.get(booking["id"])

        checked_in = self.bookings.create(
            self.customer["id"], self.room["id"], "2026-10-12", "2026-10-14"
        )
        self.bookings.check_in(checked_in["id"])
        with self.assertRaisesRegex(ValueError, "reserved"):
            self.bookings.delete(checked_in["id"])

    def test_booking_rejects_invalid_dates_and_missing_customer_or_room(self) -> None:
        for customer_id, room_id, check_in, check_out in (
            (self.customer["id"], self.room["id"], "2026-10-12", "2026-10-12"),
            (999, self.room["id"], "2026-10-10", "2026-10-12"),
            (self.customer["id"], 999, "2026-10-10", "2026-10-12"),
        ):
            with self.subTest(customer_id=customer_id, room_id=room_id):
                with self.assertRaises(ValueError):
                    self.bookings.create(customer_id, room_id, check_in, check_out)


if __name__ == "__main__":
    unittest.main()
