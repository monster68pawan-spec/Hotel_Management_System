# Spec: Hotel Management System — Rooms

## Objective
Let the operator maintain hotel room records and see whether rooms are available for a requested stay.

## Tech Stack
Python 3, Tkinter, SQLite (`sqlite3` standard library); no third-party runtime dependencies.

## Commands
- Run application: `python main.py`
- Run tests: `python -m unittest discover -s tests -v`
- Build: Not applicable; this is a Python desktop application.

## Project Structure
- `main.py`: application entry point and window navigation.
- `hotel/`: room, persistence, and other application modules.
- `tests/`: standard-library `unittest` tests.
- `data/`: local SQLite database, created at runtime and excluded from source control.

## Code Style
Use standard Python naming and validate before persistence. Example:

```python
def validate_nightly_rate(rate: float) -> float:
    if rate <= 0:
        raise ValueError("Nightly rate must be greater than zero.")
    return rate
```

Use parameterized SQL and keep room availability calculations in the application layer rather than UI callbacks.

## Testing Strategy
Use `unittest` with a temporary SQLite database to test room CRUD, positive rate validation, and date-range availability including conflicting and non-conflicting stays. Manually verify room management and availability UI.

## Boundaries
- Always: require a unique room number, valid room details, and a positive nightly rate.
- Ask first: add maintenance scheduling, room housekeeping workflows, or new room attributes.
- Never: report a room as available when it overlaps an active booking.

## Success Criteria
- The operator can create, view, update, and delete rooms through Tkinter.
- Room availability is queryable for a requested date interval and accounts for bookings.
- Invalid room data is rejected, and persistence and availability behavior are covered by tests.

## Open Questions
- None for this module.
