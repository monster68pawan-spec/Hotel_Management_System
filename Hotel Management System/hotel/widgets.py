from decimal import Decimal
from tkinter import ttk


NAVY = "#183348"
TEAL = "#087E8B"
INK = "#233746"
MUTED = "#647987"
PAPER = "#F5F7F8"
WHITE = "#FFFFFF"


def configure_style(root) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=PAPER)
    style.configure(".", font=("TkDefaultFont", 10), foreground=INK)
    style.configure("TFrame", background=PAPER)
    style.configure("TLabel", background=PAPER, foreground=INK)
    style.configure("Title.TLabel", font=("TkDefaultFont", 22, "bold"), foreground=NAVY)
    style.configure("Subtitle.TLabel", foreground=MUTED)
    style.configure("TButton", padding=(11, 7))
    style.configure("Accent.TButton", background=TEAL, foreground=WHITE, padding=(12, 8))
    style.map("Accent.TButton", background=[("active", "#06646E")])
    style.configure("Treeview", rowheight=30, background=WHITE, fieldbackground=WHITE)
    style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"), padding=(8, 7))
    style.configure("TNotebook", background=PAPER, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(16, 9))


def make_table(parent, columns: tuple[tuple[str, str, int], ...]):
    identifiers = tuple(column[0] for column in columns)
    tree = ttk.Treeview(parent, columns=identifiers, show="headings", selectmode="browse")
    for identifier, heading, width in columns:
        tree.heading(identifier, text=heading)
        tree.column(identifier, width=width, minwidth=60, anchor="w")
    vertical = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    horizontal = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)
    return tree


def money(cents: int) -> str:
    return f"{Decimal(cents) / 100:.2f}"
