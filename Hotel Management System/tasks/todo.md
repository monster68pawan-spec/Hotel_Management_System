# Hotel Management System — Task List

## Phase 1: Foundation
- [x] Task 1: Create the application foundation and database schema
  - Acceptance: Runnable Tkinter entry point; repeatable SQLite schema for customers, rooms, bookings, invoices; foreign keys enabled.
  - Verify: `python -m unittest tests.test_database -v`; `python -m py_compile main.py hotel/*.py`.
  - Dependencies: None.
  - Files: `main.py`, `hotel/__init__.py`, `hotel/database.py`, `tests/test_database.py`.
- [x] Task 2: Deliver first-run administrator setup and login
  - Acceptance: First-run admin setup, later login, salted password hashes, invalid credentials rejected.
  - Verify: `python -m unittest tests.test_auth -v`; manually verify UI flows where a display is available.
  - Dependencies: Task 1.
  - Files: `hotel/auth.py`, `hotel/ui.py`, `tests/test_auth.py`.

## Checkpoint: Foundation
- [x] Foundation and authentication tests pass; app presents first-run setup/login and an authenticated main window.

## Phase 2: Front Desk Records
- [x] Task 3: Deliver customer CRUD and search
  - Acceptance: Validated customer create/read/update/delete and case-insensitive search in service and UI.
  - Verify: `python -m unittest tests.test_customers -v`; manually verify UI where a display is available.
  - Dependencies: Task 2.
  - Files: `hotel/customers.py`, `hotel/ui.py`, `tests/test_customers.py`.
- [x] Task 4: Deliver room CRUD and date-aware availability
  - Acceptance: Room CRUD/search; positive-rate validation; availability excludes overlapping active stays.
  - Verify: `python -m unittest tests.test_rooms -v`; manually verify UI where a display is available.
  - Dependencies: Task 1.
  - Files: `hotel/rooms.py`, `hotel/ui.py`, `tests/test_rooms.py`.

## Checkpoint: Front Desk Records
- [x] Customer and room management work through Tkinter, with passing persistence and availability tests.

## Phase 3: Stay Lifecycle and Billing
- [x] Task 5: Deliver booking CRUD, check-in, and check-out
  - Acceptance: Validated booking create/search/edit; transactionally prevented room/date overlaps; reserved-only delete; valid status transitions with completed/cancelled history retained.
  - Verify: `python -m unittest tests.test_bookings -v`; manually verify UI where a display is available.
  - Dependencies: Tasks 3 and 4.
  - Files: `hotel/bookings.py`, `hotel/ui.py`, `tests/test_bookings.py`.
- [x] Task 6: Deliver stored invoices and end-to-end flow
  - Acceptance: Persistent invoice for checked-out booking, showing itemized stay facts and nightly-rate × nights total; run instructions documented.
  - Verify: `python -m unittest tests.test_billing -v`; `python -m unittest discover -s tests -v`; `python -m py_compile main.py hotel/*.py`.
  - Dependencies: Task 5.
  - Files: `hotel/billing.py`, `hotel/ui.py`, `tests/test_billing.py`, `README.md`.

## Checkpoint: Complete
- [x] Full test suite and compile check pass.
- [x] End-to-end operator workflow verified, including invoice retrieval after restart.
