import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from hotel.database import Database
from hotel.ui import HotelApp


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    database = Database(project_dir / "data" / "hotel.sqlite3")
    root = tk.Tk()
    try:
        database.initialize()
    except sqlite3.Error as error:
        messagebox.showerror("Could not open hotel database", str(error), parent=root)
        root.destroy()
        return
    HotelApp(root, database)
    root.mainloop()


if __name__ == "__main__":
    main()
