# Spec: Hotel Management System — Billing

## Objective
Generate and retain a bill for a checked-out booking. The first version calculates the room charge as nightly rate multiplied by booked nights, without taxes, extras, or payment processing.

## Tech Stack
Python 3, Tkinter, SQLite (`sqlite3` standard library); no third-party runtime dependencies.

## Commands
- Run application: `python main.py`
- Run tests: `python -m unittest discover -s tests -v`
- Build: Not applicable; this is a Python desktop application.

## Project Structure
- `main.py`: application entry point and window navigation.
- `hotel/`: billing, booking, persistence, and other application modules.
- `tests/`: standard-library `unittest` tests.
- `data/`: local SQLite database, created at runtime and excluded from source control.

## Code Style
Use standard Python naming and decimal-safe monetary calculations. Example:

```python
def calculate_room_charge(nightly_rate: Decimal, nights: int) -> Decimal:
    if nights < 1 or nightly_rate <= 0:
        raise ValueError("A bill requires a positive rate and at least one night.")
    return nightly_rate * nights
```

Use parameterized SQL and keep invoice calculation independent of Tkinter rendering.

## Testing Strategy
Use `unittest` with temporary SQLite storage to test charge calculations, invoice creation and retrieval, and rejection of bills for bookings that are not checked out. Manually verify the generated bill is readable in the UI.

## Boundaries
- Always: calculate the room charge as booked nightly rate times booked nights and retain the generated invoice.
- Ask first: add taxes, extras, discounts, refunds, payment handling, or accounting exports.
- Never: claim to process a payment or silently generate a bill with invalid booking data.

## Success Criteria
- Checking out a stay permits generation and retrieval of an invoice with the room, customer, stay dates, number of nights, nightly rate, and total.
- The total equals the nightly rate multiplied by booked nights.
- Invalid invoice requests show a clear error; calculation and persistence are covered by tests.

## Open Questions
- None for this module.
