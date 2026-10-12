# Spec: Hotel Management System — Bookings

## Objective
Let the operator create, find, and edit reserved customer room stays; delete an unstarted reservation; cancel a reservation; and check guests in and out. A room cannot have overlapping active stays. Preserve completed and cancelled stay records.

## Tech Stack
Python 3, Tkinter, SQLite (`sqlite3` standard library); no third-party runtime dependencies.

## Commands
- Run application: `python main.py`
- Run tests: `python -m unittest discover -s tests -v`
- Build: Not applicable; this is a Python desktop application.

## Project Structure
- `main.py`: application entry point and window navigation.
- `hotel/`: booking, customer, room, persistence, and other application modules.
- `tests/`: standard-library `unittest` tests.
- `data/`: local SQLite database, created at runtime and excluded from source control.

## Code Style
Use standard Python naming, typed function signatures, and explicit date validation. Example:

```python
def validate_stay(check_in: date, check_out: date) -> None:
    if check_out <= check_in:
        raise ValueError("Check-out must be after check-in.")
```

Use parameterized SQL and perform availability checks transactionally with booking writes.

## Testing Strategy
Use `unittest` with temporary SQLite storage to test reservation creation and editing, deletion of reserved stays only, overlapping-date rejection, valid transitions through reserved/checked-in/checked-out/cancelled states, and invalid dates or references. Manually verify booking and check-in/check-out flows in Tkinter.

## Boundaries
- Always: require an existing customer and room, a valid date interval, and an available room; preserve referential integrity and historical checked-in/checked-out/cancelled records.
- Ask first: add group bookings, partial stays, deposits, or booking modification after check-in.
- Never: permit an overlapping active booking or silently swallow a failed status transition.

## Success Criteria
- The operator can create and search bookings, then check guests in and out.
- Reserved bookings can be edited or deleted; completed and cancelled history is retained.
- Overlapping stays for a room are rejected while non-overlapping stays are allowed.
- Invalid dates, references, and status transitions produce clear errors.
- Booking persistence and workflow rules are covered by automated tests.

## Open Questions
- None for this module.
