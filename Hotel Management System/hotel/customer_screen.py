import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from hotel.customers import CustomerService
from hotel.widgets import make_table


class CustomerScreen(ttk.Frame):
    def __init__(self, parent, service: CustomerService) -> None:
        super().__init__(parent, padding=18)
        self.service = service
        self.selected_id: int | None = None
        self.search_text = tk.StringVar()
        self.name = tk.StringVar()
        self.phone = tk.StringVar()
        self.email = tk.StringVar()

        heading = ttk.Frame(self)
        heading.pack(fill="x", pady=(0, 14))
        ttk.Label(heading, text="Guests", style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text="Maintain guest profiles and contact details.", style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))

        form = ttk.LabelFrame(self, text="Guest details", padding=12)
        form.pack(fill="x", pady=(0, 12))
        for column, label, variable in (
            (0, "Full name *", self.name),
            (1, "Phone *", self.phone),
            (2, "Email", self.email),
        ):
            ttk.Label(form, text=label).grid(row=0, column=column, sticky="w", padx=(0, 12))
            ttk.Entry(form, textvariable=variable).grid(
                row=1, column=column, sticky="ew", padx=(0, 12), pady=(4, 10)
            )
            form.grid_columnconfigure(column, weight=1)
        actions = ttk.Frame(form)
        actions.grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Button(actions, text="Save guest", style="Accent.TButton", command=self.save).pack(side="left")
        ttk.Button(actions, text="Delete selected", command=self.delete).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear", command=self.clear_form).pack(side="left")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Guest directory", font=("TkDefaultFont", 13, "bold")).pack(side="left")
        search = ttk.Entry(toolbar, textvariable=self.search_text, width=30)
        search.pack(side="right")
        ttk.Label(toolbar, text="Search  ").pack(side="right")
        search.bind("<KeyRelease>", lambda _event: self.refresh())

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)
        self.table = make_table(
            table_frame,
            (("id", "ID", 55), ("name", "Guest name", 230), ("phone", "Phone", 160), ("email", "Email", 250)),
        )
        self.table.bind("<<TreeviewSelect>>", self.select_row)
        self.refresh()

    def refresh(self) -> None:
        self.table.delete(*self.table.get_children())
        for customer in self.service.search(self.search_text.get()):
            self.table.insert(
                "", "end",
                values=(customer["id"], customer["name"], customer["phone"], customer["email"]),
            )

    def select_row(self, _event=None) -> None:
        selected = self.table.selection()
        if not selected:
            return
        values = self.table.item(selected[0], "values")
        self.selected_id = int(values[0])
        self.name.set(values[1])
        self.phone.set(values[2])
        self.email.set(values[3])

    def save(self) -> None:
        try:
            if self.selected_id is None:
                self.service.create(self.name.get(), self.phone.get(), self.email.get())
            else:
                self.service.update(self.selected_id, self.name.get(), self.phone.get(), self.email.get())
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not save guest", str(error), parent=self)
            return
        self.clear_form()
        self.refresh()

    def delete(self) -> None:
        if self.selected_id is None:
            messagebox.showinfo("Select a guest", "Choose a guest from the directory first.", parent=self)
            return
        if not messagebox.askyesno("Delete guest", "Delete this guest record?", parent=self):
            return
        try:
            self.service.delete(self.selected_id)
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not delete guest", str(error), parent=self)
            return
        self.clear_form()
        self.refresh()

    def clear_form(self) -> None:
        self.selected_id = None
        self.name.set("")
        self.phone.set("")
        self.email.set("")
        for item in self.table.selection():
            self.table.selection_remove(item)
