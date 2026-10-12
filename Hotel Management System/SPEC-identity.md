# Spec: Hotel Management System — Identity

## Objective
Provide a local operator login for the hotel-management desktop application. On first launch, guide the operator through creating the initial administrator; on later launches, require authentication before accessing hotel records.

## Tech Stack
Python 3, Tkinter, SQLite (`sqlite3` standard library). Store passwords as salted password hashes; never store or log plaintext passwords.

## Commands
- Run application: `python main.py`
- Run tests: `python -m unittest discover -s tests -v`
- Build: Not applicable; this is a Python desktop application.

## Project Structure
- `main.py`: application entry point and window navigation.
- `hotel/`: authentication, persistence, and application modules.
- `tests/`: standard-library `unittest` tests.
- `data/`: local SQLite database, created at runtime and excluded from source control.

## Code Style
Use standard Python naming and small functions with explicit validation. Example:

```python
def verify_password(password: str, stored_hash: str) -> bool:
    return check_password_hash(password, stored_hash)
```

Use parameterized SQL, `pathlib` for local paths, and Tkinter dialogs for actionable user-facing errors.

## Testing Strategy
Use `unittest` for password hashing, first-run account creation, and valid/invalid login behavior against a temporary SQLite database. Manually verify first-run and subsequent-launch UI flows.

## Boundaries
- Always: validate credentials, hash passwords, and report authentication errors without exposing secrets.
- Ask first: add roles, remote identity providers, or multi-user authorization.
- Never: ship a default password, store plaintext passwords, or commit the live database.

## Success Criteria
- A fresh database offers a first-run administrator creation flow and then opens the authenticated application.
- A subsequent launch requires valid credentials.
- Invalid credentials do not grant access; passwords are not stored in plaintext.
- Authentication behavior is covered by automated tests.

## Open Questions
- None for this module.
