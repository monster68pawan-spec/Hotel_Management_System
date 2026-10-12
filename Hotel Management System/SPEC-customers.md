# Spec: Hotel Management System — Customers

## Objective
Let the operator register, find, view, update, and delete customer records used by hotel bookings.

## Tech Stack
Python 3, Tkinter, SQLite (`sqlite3` standard library); no third-party runtime dependencies.

## Commands
- Run application: `python main.py`
- Run tests: `python -m unittest discover -s tests -v`
- Build: Not applicable; this is a Python desktop application.

## Project Structure
- `main.py`: application entry point and window navigation.
- `hotel/`: customer, persistence, and other application modules.
- `tests/`: standard-library `unittest` tests.
- `data/`: local SQLite database, created at runtime and excluded from source control.

## Code Style
Use standard Python naming, typed function signatures, and clear validation. Example:

```python
def validate_customer_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Customer name is required.")
    return cleaned
```

Use parameterized SQL, keep database access out of Tkinter callbacks, and present validation errors next to the action that failed.

## Testing Strategy
Use `unittest` with a temporary SQLite database to verify customer create/read/update/delete, search, and rejection of empty required fields. Manually verify the customer form and search UI.

## Boundaries
- Always: validate required customer information and show clear errors for rejected changes.
- Ask first: add new personal-data fields or external customer-data integrations.
- Never: include customer records in source control or interpolate user input into SQL.

## Success Criteria
- The operator can create, view, search, update, and delete customers through Tkinter.
- Invalid required fields are rejected with a useful message.
- Customer data is persisted in SQLite and CRUD/search behavior is covered by tests.

## Open Questions
- None for this module.
