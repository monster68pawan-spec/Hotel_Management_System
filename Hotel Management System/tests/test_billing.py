import tempfile
import unittest
from pathlib import Path

from hotel.billing import BillingService
from hotel.bookings import BookingService
from hotel.customers import CustomerService
from hotel.database import Database
from hotel.rooms import RoomService


class BillingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "hotel.sqlite3")
        self.database.initialize()
        customer = CustomerService(self.database).create("Jordan Lee", "5550100")
        room = RoomService(self.database).create("101", "Deluxe", "145.50")
        self.bookings = BookingService(self.database)
        self.booking = self.bookings.create(
            customer["id"], room["id"], "2026-10-10", "2026-10-13"
        )
        self.billing = BillingService(self.database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_invoice_is_generated_once_for_checked_out_booking_and_can_be_retrieved(self) -> None:
        with self.assertRaisesRegex(ValueError, "checked out"):
            self.billing.generate(self.booking["id"])

        self.bookings.check_in(self.booking["id"])
        self.bookings.check_out(self.booking["id"])
        invoice = self.billing.generate(self.booking["id"])
        self.assertEqual(invoice["nights"], 3)
        self.assertEqual(invoice["nightly_rate_cents"], 14550)
        self.assertEqual(invoice["total_cents"], 43650)
        self.assertEqual(self.billing.generate(self.booking["id"])["id"], invoice["id"])
        self.assertEqual(self.billing.get(invoice["id"])["total_cents"], 43650)
        self.assertEqual(self.billing.search("Jordan")[0]["id"], invoice["id"])


if __name__ == "__main__":
    unittest.main()
