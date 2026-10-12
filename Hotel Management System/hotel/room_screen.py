import sqlite3
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from hotel.rooms import RoomService
from hotel.widgets import make_table, money


class RoomScreen(ttk.Frame):
    def __init__(self, parent, service: RoomService) -> None:
        super().__init__(parent, padding=18)
        self.service = service
        self.selected_id: int | None = None
        self.availability_mode = False
        self.search_text = tk.StringVar()
        self.number = tk.StringVar()
        self.room_type = tk.StringVar()
        self.rate = tk.StringVar()
        self.check_in = tk.StringVar(value=date.today().isoformat())
        self.check_out = tk.StringVar(value=(date.today() + timedelta(days=1)).isoformat())

        heading = ttk.Frame(self)
        heading.pack(fill="x", pady=(0, 14))
        ttk.Label(heading, text="Rooms", style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text="Manage inventory, nightly rates, and stay availability.", style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))

        form = ttk.LabelFrame(self, text="Room details", padding=12)
        form.pack(fill="x", pady=(0, 12))
        for column, label, variable in (
            (0, "Room number *", self.number),
            (1, "Room type *", self.room_type),
            (2, "Nightly rate *", self.rate),
        ):
            ttk.Label(form, text=label).grid(row=0, column=column, sticky="w", padx=(0, 12))
            ttk.Entry(form, textvariable=variable).grid(
                row=1, column=column, sticky="ew", padx=(0, 12), pady=(4, 10)
            )
            form.grid_columnconfigure(column, weight=1)
        actions = ttk.Frame(form)
        actions.grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Button(actions, text="Save room", style="Accent.TButton", command=self.save).pack(side="left")
        ttk.Button(actions, text="Delete selected", command=self.delete).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear", command=self.clear_form).pack(side="left")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Room directory", font=("TkDefaultFont", 13, "bold")).pack(side="left")
        ttk.Label(toolbar, text="Search").pack(side="right", padx=(8, 5))
        search = ttk.Entry(toolbar, textvariable=self.search_text, width=18)
        search.pack(side="right")
        search.bind("<KeyRelease>", lambda _event: self.refresh())

        availability = ttk.LabelFrame(self, text="Find available rooms", padding=10)
        availability.pack(fill="x", pady=(0, 10))
        ttk.Label(availability, text="Check-in (YYYY-MM-DD)").pack(side="left")
        ttk.Entry(availability, textvariable=self.check_in, width=13).pack(side="left", padx=(7, 14))
        ttk.Label(availability, text="Check-out").pack(side="left")
        ttk.Entry(availability, textvariable=self.check_out, width=13).pack(side="left", padx=(7, 10))
        ttk.Button(availability, text="Find available", command=self.find_available).pack(side="left")
        ttk.Button(availability, text="Show all rooms", command=self.show_all).pack(side="left", padx=8)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)
        self.table = make_table(
            table_frame,
            (("id", "ID", 55), ("number", "Room", 100), ("room_type", "Type", 180), ("rate", "Nightly rate", 120)),
        )
        self.table.bind("<<TreeviewSelect>>", self.select_row)
        self.refresh()

    def refresh(self) -> None:
        try:
            rooms = (
                self.service.available(self.check_in.get(), self.check_out.get())
                if self.availability_mode else self.service.search()
            )
        except ValueError as error:
            messagebox.showerror("Invalid stay dates", str(error), parent=self)
            return
        term = self.search_text.get().strip().casefold()
        self.table.delete(*self.table.get_children())
        for room in rooms:
            if term and term not in room["number"].casefold() and term not in room["room_type"].casefold():
                continue
            self.table.insert(
                "", "end",
                values=(room["id"], room["number"], room["room_type"], money(room["nightly_rate_cents"])),
            )

    def find_available(self) -> None:
        self.availability_mode = True
        self.refresh()

    def show_all(self) -> None:
        self.availability_mode = False
        self.refresh()

    def select_row(self, _event=None) -> None:
        selected = self.table.selection()
        if not selected:
            return
        values = self.table.item(selected[0], "values")
        self.selected_id = int(values[0])
        self.number.set(values[1])
        self.room_type.set(values[2])
        self.rate.set(values[3])

    def save(self) -> None:
        try:
            if self.selected_id is None:
                self.service.create(self.number.get(), self.room_type.get(), self.rate.get())
            else:
                self.service.update(self.selected_id, self.number.get(), self.room_type.get(), self.rate.get())
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not save room", str(error), parent=self)
            return
        self.clear_form()
        self.refresh()

    def delete(self) -> None:
        if self.selected_id is None:
            messagebox.showinfo("Select a room", "Choose a room from the directory first.", parent=self)
            return
        if not messagebox.askyesno("Delete room", "Delete this room record?", parent=self):
            return
        try:
            self.service.delete(self.selected_id)
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not delete room", str(error), parent=self)
            return
        self.clear_form()
        self.refresh()

    def clear_form(self) -> None:
        self.selected_id = None
        self.number.set("")
        self.room_type.set("")
        self.rate.set("")
        for item in self.table.selection():
            self.table.selection_remove(item)
