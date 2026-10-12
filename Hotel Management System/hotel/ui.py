import sqlite3
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from hotel.auth import AuthError, AuthService
from hotel.billing import BillingService
from hotel.booking_screen import BookingScreen
from hotel.bookings import BookingService
from hotel.billing_screen import BillingScreen
from hotel.customer_screen import CustomerScreen
from hotel.customers import CustomerService
from hotel.database import Database
from hotel.room_screen import RoomScreen
from hotel.rooms import RoomService
from hotel.widgets import NAVY, PAPER, TEAL, WHITE, configure_style


class HotelApp:
    def __init__(self, root: tk.Tk, database: Database) -> None:
        self.root = root
        self.database = database
        self.auth = AuthService(database)
        self.root.title("Harbor Hotel · Front Desk")
        self.root.geometry("1180x760")
        self.root.minsize(960, 640)
        configure_style(root)
        self._show_auth()

    def _show_auth(self) -> None:
        self.auth_frame = ttk.Frame(self.root, padding=24)
        self.auth_frame.pack(fill="both", expand=True)
        self.auth_frame.columnconfigure(0, weight=1)
        self.auth_frame.rowconfigure(0, weight=1)
        card = ttk.Frame(self.auth_frame, padding=32)
        card.grid(row=0, column=0)
        ttk.Label(card, text="HARBOR  /  HOTEL OPERATIONS", foreground=TEAL).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        is_first_run = not self.auth.admin_exists()
        title = "Set up your front desk" if is_first_run else "Welcome back"
        subtitle = (
            "Create the administrator account for this hotel."
            if is_first_run else "Sign in to manage today's hotel operations."
        )
        ttk.Label(card, text=title, style="Title.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Label(card, text=subtitle, style="Subtitle.TLabel").grid(
            row=2, column=0, sticky="w", pady=(5, 20)
        )
        ttk.Label(card, text="Username").grid(row=3, column=0, sticky="w")
        self.username = tk.StringVar()
        ttk.Entry(card, textvariable=self.username, width=38).grid(
            row=4, column=0, sticky="ew", pady=(4, 12)
        )
        ttk.Label(card, text="Password").grid(row=5, column=0, sticky="w")
        self.password = tk.StringVar()
        password_entry = ttk.Entry(card, textvariable=self.password, show="*", width=38)
        password_entry.grid(row=6, column=0, sticky="ew", pady=(4, 12))
        if is_first_run:
            ttk.Label(card, text="Confirm password").grid(row=7, column=0, sticky="w")
            self.confirm_password = tk.StringVar()
            ttk.Entry(card, textvariable=self.confirm_password, show="*", width=38).grid(
                row=8, column=0, sticky="ew", pady=(4, 14)
            )
            ttk.Button(
                card, text="Create administrator", style="Accent.TButton", command=self._create_admin
            ).grid(row=9, column=0, sticky="ew")
            ttk.Label(
                card, text="Use at least 10 characters. Your password is stored as a secure hash.",
                style="Subtitle.TLabel",
            ).grid(row=10, column=0, sticky="w", pady=(12, 0))
        else:
            ttk.Button(
                card, text="Sign in", style="Accent.TButton", command=self._login
            ).grid(row=7, column=0, sticky="ew", pady=(5, 0))
            password_entry.bind("<Return>", lambda _event: self._login())
        card.grid_columnconfigure(0, weight=1)
        password_entry.focus_set()

    def _create_admin(self) -> None:
        if self.password.get() != self.confirm_password.get():
            messagebox.showerror("Passwords do not match", "Enter the same password in both fields.", parent=self.root)
            return
        try:
            self.auth.create_admin(self.username.get(), self.password.get())
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Could not create administrator", str(error), parent=self.root)
            return
        self._open_dashboard(self.username.get().strip())

    def _login(self) -> None:
        try:
            self.auth.login(self.username.get(), self.password.get())
        except AuthError as error:
            messagebox.showerror("Sign-in failed", str(error), parent=self.root)
            self.password.set("")
            return
        self._open_dashboard(self.username.get().strip())

    def _open_dashboard(self, username: str) -> None:
        self.auth_frame.destroy()
        self.dashboard = Dashboard(self.root, self.database, username, self._logout)
        self.dashboard.pack(fill="both", expand=True)

    def _logout(self) -> None:
        self.dashboard.destroy()
        self._show_auth()


class Dashboard(ttk.Frame):
    def __init__(self, parent, database: Database, username: str, on_logout) -> None:
        super().__init__(parent)
        self.database = database
        self.customer_service = CustomerService(database)
        self.room_service = RoomService(database)
        self.booking_service = BookingService(database)
        self.billing_service = BillingService(database)

        style = ttk.Style(self)
        style.configure("Header.TFrame", background=NAVY)
        style.configure("HeaderTitle.TLabel", background=NAVY, foreground=WHITE, font=("TkDefaultFont", 17, "bold"))
        style.configure("HeaderMeta.TLabel", background=NAVY, foreground="#D8E2E9")
        style.configure("Metric.TFrame", background=WHITE, padding=16)
        style.configure("MetricLabel.TLabel", background=WHITE, foreground="#647987")
        style.configure("MetricValue.TLabel", background=WHITE, foreground=NAVY, font=("TkDefaultFont", 20, "bold"))
        style.configure("Overview.TFrame", background=PAPER)

        header = ttk.Frame(self, style="Header.TFrame", padding=(22, 16))
        header.pack(fill="x")
        ttk.Label(header, text="HARBOR  /  HOTEL OPERATIONS", style="HeaderTitle.TLabel").pack(side="left")
        ttk.Button(header, text="Sign out", command=on_logout).pack(side="right")
        ttk.Button(header, text="Back up data", command=self._backup_database).pack(
            side="right", padx=8
        )
        ttk.Label(header, text=f"Front desk  ·  {username}", style="HeaderMeta.TLabel").pack(side="right", padx=14)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=14)
        overview = ttk.Frame(self.notebook, style="Overview.TFrame", padding=24)
        self.notebook.add(overview, text="Overview")
        self._build_overview(overview)
        self.customer_screen = CustomerScreen(self.notebook, self.customer_service)
        self.room_screen = RoomScreen(self.notebook, self.room_service)
        self.booking_screen = BookingScreen(
            self.notebook, self.booking_service, self.customer_service, self.room_service
        )
        self.billing_screen = BillingScreen(
            self.notebook, self.billing_service, self.booking_service
        )
        self.notebook.add(self.customer_screen, text="Guests")
        self.notebook.add(self.room_screen, text="Rooms")
        self.notebook.add(self.booking_screen, text="Reservations")
        self.notebook.add(self.billing_screen, text="Billing")
        self.notebook.bind("<<NotebookTabChanged>>", self._tab_changed)

    def _backup_database(self) -> None:
        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Back up hotel data",
            initialdir=Path.home(),
            initialfile=f"hotel-backup-{date.today().isoformat()}.sqlite3",
            defaultextension=".sqlite3",
            filetypes=(("SQLite database", "*.sqlite3"), ("All files", "*")),
        )
        if not destination:
            return
        try:
            self.database.backup(destination)
        except (OSError, sqlite3.Error, ValueError) as error:
            messagebox.showerror("Could not back up hotel data", str(error), parent=self)
            return
        messagebox.showinfo(
            "Backup complete",
            f"Hotel data was backed up to:\n{destination}\n\n"
            "Keep a copy on a separate drive or secure location.",
            parent=self,
        )

    def _build_overview(self, parent) -> None:
        ttk.Label(parent, text="Good day. Here's your front desk at a glance.", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            parent, text="Manage room inventory, guest stays, and checkout from one place.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 22))

        metrics = ttk.Frame(parent, style="Overview.TFrame")
        metrics.pack(fill="x")
        self.metric_values: dict[str, ttk.Label] = {}
        for column, (key, title) in enumerate((
            ("guests", "Registered guests"),
            ("rooms", "Rooms in inventory"),
            ("arrivals", "Arrivals today"),
            ("occupied", "Currently checked in"),
        )):
            card = ttk.Frame(metrics, style="Metric.TFrame")
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
            metrics.grid_columnconfigure(column, weight=1)
            ttk.Label(card, text=title, style="MetricLabel.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="0", style="MetricValue.TLabel")
            value.pack(anchor="w", pady=(7, 0))
            self.metric_values[key] = value
        ttk.Label(parent, text="Today's workflow", font=("TkDefaultFont", 15, "bold")).pack(
            anchor="w", pady=(28, 10)
        )
        steps = ttk.Frame(parent)
        steps.pack(fill="x")
        for title, detail in (
            ("1  Guests", "Register or find a guest and keep their contact details current."),
            ("2  Rooms", "Maintain room types and nightly rates; check availability by dates."),
            ("3  Reservations", "Reserve an available room, then record guest check-in and checkout."),
            ("4  Billing", "Generate and retrieve the stay bill after checkout."),
        ):
            row = ttk.Frame(steps, padding=(0, 7))
            row.pack(fill="x")
            ttk.Label(row, text=title, width=19, font=("TkDefaultFont", 10, "bold")).pack(side="left", anchor="n")
            ttk.Label(row, text=detail, style="Subtitle.TLabel").pack(side="left", anchor="n")
        self._refresh_metrics()

    def _refresh_metrics(self) -> None:
        today = date.today().isoformat()
        with self.database.connect() as connection:
            counts = {
                "guests": connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
                "rooms": connection.execute("SELECT COUNT(*) FROM rooms").fetchone()[0],
                "arrivals": connection.execute(
                    "SELECT COUNT(*) FROM bookings WHERE check_in = ? AND status = 'reserved'", (today,)
                ).fetchone()[0],
                "occupied": connection.execute(
                    "SELECT COUNT(*) FROM bookings WHERE status = 'checked_in'"
                ).fetchone()[0],
            }
        for key, value in counts.items():
            self.metric_values[key].configure(text=str(value))

    def _tab_changed(self, _event=None) -> None:
        selected = self.notebook.nametowidget(self.notebook.select())
        if selected is self.customer_screen:
            self.customer_screen.refresh()
            self.booking_screen.refresh()
        elif selected is self.room_screen:
            self.room_screen.refresh()
            self.booking_screen.refresh()
        elif selected is self.booking_screen:
            self.booking_screen.refresh()
        elif selected is self.billing_screen:
            self.billing_screen.refresh()
        else:
            self._refresh_metrics()
