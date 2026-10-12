import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from hotel.billing import BillingService
from hotel.bookings import BookingService
from hotel.widgets import make_table, money


class BillingScreen(ttk.Frame):
    def __init__(
        self,
        parent,
        billing: BillingService,
        bookings: BookingService,
    ) -> None:
        super().__init__(parent, padding=18)
        self.billing = billing
        self.bookings = bookings
        self.booking_ids: dict[str, int] = {}
        self.search_text = tk.StringVar()
        self.booking_choice = tk.StringVar()
        self.invoice_detail = tk.StringVar(value="Select an invoice to view its stay and charge details.")

        heading = ttk.Frame(self)
        heading.pack(fill="x", pady=(0, 14))
        ttk.Label(heading, text="Billing", style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text="Generate and retrieve bills for completed stays.", style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))

        action = ttk.LabelFrame(self, text="Generate a bill", padding=12)
        action.pack(fill="x", pady=(0, 14))
        ttk.Label(action, text="Checked-out reservation").pack(side="left")
        self.booking_box = ttk.Combobox(
            action, textvariable=self.booking_choice, state="readonly", width=52
        )
        self.booking_box.pack(side="left", padx=10)
        ttk.Button(action, text="Generate / view bill", style="Accent.TButton", command=self.generate).pack(side="left")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Invoices", font=("TkDefaultFont", 13, "bold")).pack(side="left")
        ttk.Label(toolbar, text="Search").pack(side="right", padx=(8, 5))
        search = ttk.Entry(toolbar, textvariable=self.search_text, width=22)
        search.pack(side="right")
        search.bind("<KeyRelease>", lambda _event: self.refresh())
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)
        self.table = make_table(
            table_frame,
            (
                ("id", "Bill #", 70), ("guest", "Guest", 190), ("room", "Room", 80),
                ("check_in", "Check-in", 110), ("check_out", "Check-out", 110),
                ("nights", "Nights", 70), ("rate", "Rate / night", 120), ("total", "Total", 120),
            ),
        )
        self.table.bind("<<TreeviewSelect>>", self.select_row)
        details = ttk.LabelFrame(self, text="Bill details", padding=12)
        details.pack(fill="x", pady=(10, 0))
        ttk.Label(details, textvariable=self.invoice_detail, justify="left").pack(anchor="w")
        self.refresh()

    def refresh(self) -> None:
        checked_out = [
            booking for booking in self.bookings.search()
            if booking["status"] == "checked_out"
        ]
        self.booking_ids = {
            f'#{booking["id"]} · {booking["customer_name"]} · room {booking["room_number"]} '
            f'· {booking["check_in"]} to {booking["check_out"]}': booking["id"]
            for booking in checked_out
        }
        self.booking_box["values"] = tuple(self.booking_ids)
        if self.booking_choice.get() not in self.booking_ids:
            self.booking_choice.set(next(iter(self.booking_ids), ""))
        self.table.delete(*self.table.get_children())
        for invoice in self.billing.search(self.search_text.get()):
            self.table.insert(
                "", "end",
                values=(
                    invoice["id"], invoice["customer_name"], invoice["room_number"],
                    invoice["check_in"], invoice["check_out"], invoice["nights"],
                    money(invoice["nightly_rate_cents"]), money(invoice["total_cents"]),
                ),
            )

    def generate(self) -> None:
        booking_id = self.booking_ids.get(self.booking_choice.get())
        if booking_id is None:
            messagebox.showinfo(
                "No completed stay",
                "Bills can be generated after a guest has checked out.",
                parent=self,
            )
            return
        try:
            invoice = self.billing.generate(booking_id)
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not generate bill", str(error), parent=self)
            return
        self.refresh()
        self.invoice_detail.set(self._format_invoice(invoice))
        messagebox.showinfo(
            "Bill ready",
            f"Bill #{invoice['id']} total: {money(invoice['total_cents'])}",
            parent=self,
        )

    def select_row(self, _event=None) -> None:
        selected = self.table.selection()
        if not selected:
            return
        invoice_id = int(self.table.item(selected[0], "values")[0])
        try:
            self.invoice_detail.set(self._format_invoice(self.billing.get(invoice_id)))
        except ValueError as error:
            messagebox.showerror("Could not load bill", str(error), parent=self)

    @staticmethod
    def _format_invoice(invoice: dict) -> str:
        return (
            f'Bill #{invoice["id"]}  |  {invoice["customer_name"]}  |  Room {invoice["room_number"]}\n'
            f'{invoice["check_in"]} to {invoice["check_out"]}  ·  {invoice["nights"]} nights\n'
            f'Nightly rate: {money(invoice["nightly_rate_cents"])}  ×  {invoice["nights"]} nights'
            f'  =  Total: {money(invoice["total_cents"])}'
        )
