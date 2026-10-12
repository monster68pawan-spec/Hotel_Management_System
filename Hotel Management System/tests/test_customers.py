import tempfile
import unittest
from pathlib import Path

from hotel.customers import CustomerService
from hotel.database import Database


class CustomerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "hotel.sqlite3")
        self.database.initialize()
        self.customers = CustomerService(self.database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_customer_crud_and_search(self) -> None:
        customer = self.customers.create("  Jordan Lee ", "+1 555 0100", "jordan@example.com")
        self.assertEqual(customer["name"], "Jordan Lee")
        self.assertEqual(len(self.customers.search("jordan")), 1)
        self.assertEqual(len(self.customers.search("missing")), 0)

        updated = self.customers.update(customer["id"], "Jordan Park", "+1 555 0101", "")
        self.assertEqual(updated["name"], "Jordan Park")
        self.customers.delete(customer["id"])
        self.assertEqual(self.customers.search(), [])

    def test_customer_rejects_missing_name_invalid_phone_and_email(self) -> None:
        for name, phone, email in (
            (" ", "+1 555 0100", ""),
            ("Jordan Lee", "x", ""),
            ("Jordan Lee", "+1 555 0100", "not-an-email"),
        ):
            with self.subTest(name=name, phone=phone, email=email):
                with self.assertRaises(ValueError):
                    self.customers.create(name, phone, email)


if __name__ == "__main__":
    unittest.main()
