import sqlite3
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from hotel.bookings import BookingService
from hotel.customers import CustomerService
from hotel.rooms import RoomService
from hotel.widgets import make_table, money


class BookingScreen(ttk.Frame):
    def __init__(
        self,
        parent,
        bookings: BookingService,
        customers: CustomerService,
        rooms: RoomService,
    ) -> None:
        super().__init__(parent, padding=18)
        self.bookings = bookings
        self.customers = customers
        self.rooms = rooms
        self.selected_id: int | None = None
        self.selected_is_editable = False
        self.customer_ids: dict[str, int] = {}
        self.room_ids: dict[str, int] = {}
        self.search_text = tk.StringVar()
        self.customer_choice = tk.StringVar()
        self.room_choice = tk.StringVar()
        self.check_in = tk.StringVar(value=date.today().isoformat())
        self.check_out = tk.StringVar(value=(date.today() + timedelta(days=1)).isoformat())

        heading = ttk.Frame(self)
        heading.pack(fill="x", pady=(0, 14))
        ttk.Label(heading, text="Reservations", style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text="Reserve rooms, manage arrivals, and check guests out.", style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))

        form = ttk.LabelFrame(self, text="New reservation", padding=12)
        form.pack(fill="x", pady=(0, 12))
        ttk.Label(form, text="Guest *").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.customer_box = ttk.Combobox(form, textvariable=self.customer_choice, state="readonly", width=28)
        self.customer_box.grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(4, 10))
        ttk.Label(form, text="Check-in * (YYYY-MM-DD)").grid(row=0, column=1, sticky="w", padx=(0, 10))
        ttk.Entry(form, textvariable=self.check_in, width=15).grid(
            row=1, column=1, sticky="ew", padx=(0, 12), pady=(4, 10)
        )
        ttk.Label(form, text="Check-out *").grid(row=0, column=2, sticky="w", padx=(0, 10))
        ttk.Entry(form, textvariable=self.check_out, width=15).grid(
            row=1, column=2, sticky="ew", padx=(0, 12), pady=(4, 10)
        )
        ttk.Label(form, text="Available room *").grid(row=0, column=3, sticky="w")
        self.room_box = ttk.Combobox(form, textvariable=self.room_choice, state="readonly", width=24)
        self.room_box.grid(row=1, column=3, sticky="ew", pady=(4, 10))
        for column in range(4):
            form.grid_columnconfigure(column, weight=1)
        actions = ttk.Frame(form)
        actions.grid(row=2, column=0, columnspan=4, sticky="w")
        ttk.Button(actions, text="Check availability", command=self.refresh_rooms).pack(side="left")
        ttk.Button(actions, text="Create / update reservation", style="Accent.TButton", command=self.save).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear selection", command=self.clear_form).pack(side="left")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Reservation list", font=("TkDefaultFont", 13, "bold")).pack(side="left")
        ttk.Label(toolbar, text="Search").pack(side="right", padx=(8, 5))
        search = ttk.Entry(toolbar, textvariable=self.search_text, width=20)
        search.pack(side="right")
        search.bind("<KeyRelease>", lambda _event: self.refresh())

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)
        self.table = make_table(
            table_frame,
            (
                ("id", "ID", 50), ("guest", "Guest", 170), ("room", "Room", 70),
                ("check_in", "Check-in", 105), ("check_out", "Check-out", 105),
                ("status", "Status", 120), ("rate", "Rate / night", 110),
            ),
        )
        self.table.bind("<<TreeviewSelect>>", self.select_row)
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(10, 0))
        ttk.Button(controls, text="Delete selected reservation", command=self.delete).pack(side="right")
        ttk.Button(controls, text="Check in", command=self.check_in_guest).pack(side="left")
        ttk.Button(controls, text="Check out", command=self.check_out_guest).pack(side="left", padx=8)
        ttk.Button(controls, text="Cancel reservation", command=self.cancel).pack(side="left")
        self.refresh()

    def refresh_rooms(self, show_error: bool = True) -> None:
        try:
            available = self.rooms.available(
                self.check_in.get(),
                self.check_out.get(),
                exclude_booking_id=self.selected_id if self.selected_is_editable else None,
            )
        except ValueError as error:
            self.room_ids.clear()
            self.room_box["values"] = ()
            self.room_choice.set("")
            if show_error:
                messagebox.showerror("Invalid stay dates", str(error), parent=self)
            return
        self.room_ids = {
            f'{room["number"]} · {room["room_type"]} · {money(room["nightly_rate_cents"])} / night': room["id"]
            for room in available
        }
        choices = tuple(self.room_ids)
        self.room_box["values"] = choices
        self.room_choice.set(choices[0] if choices else "")

    def refresh(self) -> None:
        customers = self.customers.search()
        self.customer_ids = {
            f'{customer["name"]} · {customer["phone"]}': customer["id"]
            for customer in customers
        }
        choices = tuple(self.customer_ids)
        self.customer_box["values"] = choices
        if self.customer_choice.get() not in self.customer_ids:
            self.customer_choice.set(choices[0] if choices else "")
        self.refresh_rooms(show_error=False)
        self.table.delete(*self.table.get_children())
        for booking in self.bookings.search(self.search_text.get()):
            self.table.insert(
                "", "end",
                values=(
                    booking["id"], booking["customer_name"], booking["room_number"],
                    booking["check_in"], booking["check_out"], booking["status"].replace("_", " "),
                    money(booking["nightly_rate_cents"]),
                ),
            )

    def save(self) -> None:
        if self.selected_id is not None and not self.selected_is_editable:
            messagebox.showerror("Reservation cannot be edited", "Only reserved stays can be edited.", parent=self)
            return
        customer_id = self.customer_ids.get(self.customer_choice.get())
        room_id = self.room_ids.get(self.room_choice.get())
        if customer_id is None:
            messagebox.showerror("Guest required", "Add or select a guest before making a reservation.", parent=self)
            return
        if room_id is None:
            messagebox.showerror("Room required", "No available room is selected for these dates.", parent=self)
            return
        try:
            if self.selected_id is None:
                self.bookings.create(customer_id, room_id, self.check_in.get(), self.check_out.get())
            else:
                self.bookings.update(
                    self.selected_id, customer_id, room_id, self.check_in.get(), self.check_out.get()
                )
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not save reservation", str(error), parent=self)
            self.refresh_rooms()
            return
        messagebox.showinfo("Reservation saved", "Reservation details have been saved.", parent=self)
        self.clear_form()
        self.refresh()

    def select_row(self, _event=None) -> None:
        selected = self.table.selection()
        if not selected:
            self.selected_id = None
            self.selected_is_editable = False
            return
        self.selected_id = int(self.table.item(selected[0], "values")[0])
        try:
            booking = self.bookings.get(self.selected_id)
        except ValueError as error:
            messagebox.showerror("Could not load reservation", str(error), parent=self)
            return
        self.selected_is_editable = booking["status"] == "reserved"
        self.customer_choice.set(next(
            (label for label, customer_id in self.customer_ids.items()
             if customer_id == booking["customer_id"]),
            "",
        ))
        self.check_in.set(booking["check_in"])
        self.check_out.set(booking["check_out"])
        self.refresh_rooms()
        self.room_choice.set(next(
            (label for label, room_id in self.room_ids.items() if room_id == booking["room_id"]),
            "",
        ))

    def delete(self) -> None:
        if self.selected_id is None:
            messagebox.showinfo("Select a reservation", "Choose a reservation from the list first.", parent=self)
            return
        if not messagebox.askyesno(
            "Delete reservation", "Delete this reserved stay? Completed and cancelled history is retained.", parent=self
        ):
            return
        try:
            self.bookings.delete(self.selected_id)
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not delete reservation", str(error), parent=self)
            return
        self.clear_form()
        self.refresh()

    def clear_form(self) -> None:
        self.selected_id = None
        self.selected_is_editable = False
        self.customer_choice.set("")
        self.room_choice.set("")
        for item in self.table.selection():
            self.table.selection_remove(item)
        self.refresh_rooms()

    def _change_status(self, action, success_message: str) -> None:
        if self.selected_id is None:
            messagebox.showinfo("Select a reservation", "Choose a reservation from the list first.", parent=self)
            return
        try:
            action(self.selected_id)
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Reservation was not updated", str(error), parent=self)
            return
        self.refresh()
        messagebox.showinfo("Reservation updated", success_message, parent=self)

    def check_in_guest(self) -> None:
        self._change_status(self.bookings.check_in, "Guest checked in.")

    def check_out_guest(self) -> None:
        self._change_status(self.bookings.check_out, "Guest checked out. You can now generate the bill.")

    def cancel(self) -> None:
        if not messagebox.askyesno("Cancel reservation", "Cancel the selected reservation?", parent=self):
            return
        self._change_status(self.bookings.cancel, "Reservation cancelled.")
