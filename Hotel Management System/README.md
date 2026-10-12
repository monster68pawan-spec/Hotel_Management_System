# Harbor Hotel Management System

A local desktop front-desk application built with Python, object-oriented service modules, Tkinter, and SQLite. It manages administrator login, guest and room records, stay availability, reservations, check-in/check-out, and stored bills.

## Run

Requires Python 3.10 or newer with Tkinter enabled. No third-party packages are required.

```bash
python main.py
```

On first launch, create an administrator username and password (at least 10 characters). Later launches require that login. Hotel records are stored in `data/hotel.sqlite3` beside the application.

While the app is open, use **Back up data** in the dashboard and save the backup to a separate, secure drive or location. This uses SQLite's backup operation so the database can be copied safely while the app is running. A backup also contains guest and administrator records, so protect it like the live database. To restore one, close the app, first make a copy of the current `data/hotel.sqlite3`, then replace it with the chosen backup.

Run the automated tests with:

```bash
python -m unittest discover -s tests -v
```

## Front-desk workflow

1. Add guests with a name and phone number; email is optional.
2. Add rooms with a unique room number, type, and nightly rate.
3. Search room availability using check-in and check-out dates, then create a reservation.
4. Select a reserved stay to edit or remove it; check the guest in and out as the stay progresses. Cancel an unstarted reservation to release the room while retaining its cancellation history.
5. After checkout, generate or retrieve the bill from Billing. The bill snapshots the reserved nightly rate and calculates `nightly rate × reserved nights`.

This is a single-computer record-keeping app, not a multi-workstation or full commercial hotel system. Rates and totals are entered and displayed as decimal amounts in the hotel's chosen local currency units; bills are internal room-charge records only, with no currency symbol, taxes, payment processing, or guarantee of legal invoice compliance. Verify local tax, invoicing, privacy, and record-retention requirements before using it for official accounting.

## Data and validation

SQLite foreign keys and parameterized queries protect record relationships and user input. Passwords are salted PBKDF2-HMAC-SHA256 hashes. Room availability treats stays as `[check-in, check-out)`, so one guest can check out on the date the next guest checks in. Rooms and guests with booking history are retained to preserve records.

## Tests

The `unittest` suite exercises database initialization, authentication, customer and room CRUD, date-overlap protection, reservation status transitions, and invoice calculations/persistence. The Tkinter interface requires a graphical desktop session.
