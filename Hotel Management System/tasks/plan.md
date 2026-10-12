# Implementation Plan: Hotel Management System

## Overview
Build a runnable, single-operator hotel management desktop application using Python, object-oriented modules, Tkinter, and SQLite. Deliver authenticated startup, customer and room management, date-aware reservations with check-in/check-out, and stored bills. Keep the application dependency-free beyond Python's standard library.

## Architecture Decisions
- Use a small `hotel/` package with domain/persistence services separated from Tkinter screens so validation and business rules are testable without a display.
- Use SQLite transactions, parameterized queries, foreign keys, and a local runtime database under `data/`; tests use temporary databases.
- Hash the first-run administrator's password using the standard library's PBKDF2-HMAC support.
- Calculate and store invoice amounts in integer cents to avoid floating-point currency errors; bill the saved nightly rate times the reserved nights.
- Provide a single Tkinter main window with clearly labeled navigation and tables/forms for the daily front-desk workflow.
- Use only standard-library `unittest`; no package install or build step is required.

## Task List

### Phase 1: Foundation
- [x] Task 1: Create the application foundation and database schema.
- [x] Task 2: Deliver first-run administrator setup and login.

### Checkpoint: Foundation
- [x] Tests pass for schema, password handling, setup, and login.
- [x] Application opens a clear, usable authenticated main window.

### Phase 2: Front Desk Records
- [x] Task 3: Deliver customer CRUD and search.
- [x] Task 4: Deliver room CRUD and date-aware availability.

### Checkpoint: Front Desk Records
- [x] Customer and room records persist and can be managed through the UI.
- [x] Automated tests prove availability against overlapping and non-overlapping stays.

### Phase 3: Stay Lifecycle and Billing
- [x] Task 5: Deliver booking CRUD, search, check-in, and check-out.
- [x] Task 6: Deliver stored invoices and the end-to-end front-desk flow.

### Checkpoint: Complete
- [x] All automated tests pass and all modules compile.
- [x] A user can set up an admin, log in, create a customer and room, book an available stay, check the guest in/out, and generate/retrieve a bill.
- [x] Run instructions and database behavior are documented.

## Task Details

### Task 1: Create the application foundation and database schema
**Description:** Add the package and application entry point, initialize the local SQLite database, and define related customer, room, booking, and invoice tables with foreign keys and constraints. Provide temporary-database support for tests.

**Acceptance criteria:**
- [x] `python main.py` launches the Tkinter application without a missing dependency.
- [x] Database initialization is repeatable and creates the required relational schema.
- [x] SQLite foreign-key enforcement is enabled on application connections.

**Verification:**
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python -m py_compile main.py hotel/*.py`.
- [ ] Verify a fresh temporary database initializes twice without error.

**Dependencies:** None

**Files likely touched:**
- `main.py`
- `hotel/__init__.py`
- `hotel/database.py`
- `tests/test_database.py`

**Estimated scope:** Medium

### Task 2: Deliver first-run administrator setup and login
**Description:** Add password hashing and authentication services, then gate the main window on one-time administrator creation or successful login.

**Acceptance criteria:**
- [x] A fresh database opens an administrator setup form; later launches show login.
- [x] Passwords are salted and hashed, and invalid credentials never authenticate.
- [x] Login and setup failures are shown clearly without leaking password data.

**Verification:**
- [ ] Run `python -m unittest tests.test_auth -v`.
- [ ] Manually verify the fresh-install and subsequent-login flows where a display is available.

**Dependencies:** Task 1

**Files likely touched:**
- `hotel/auth.py`
- `hotel/ui.py`
- `tests/test_auth.py`

**Estimated scope:** Medium

### Task 3: Deliver customer CRUD and search
**Description:** Add validated customer persistence and a Tkinter customer screen to create, list, find, update, and delete customer records.

**Acceptance criteria:**
- [x] Required customer name and contact details are validated before save.
- [x] Customer create, read, update, delete, and case-insensitive search work against SQLite.
- [x] The UI reloads after changes and shows clear validation/database errors.

**Verification:**
- [ ] Run `python -m unittest tests.test_customers -v`.
- [ ] Manually verify customer create/search/edit/delete through Tkinter where a display is available.

**Dependencies:** Task 2

**Files likely touched:**
- `hotel/customers.py`
- `hotel/ui.py`
- `tests/test_customers.py`

**Estimated scope:** Medium

### Task 4: Deliver room CRUD and date-aware availability
**Description:** Add room management with unique room numbers, valid room types, positive nightly rates, and availability searches using the same date-overlap rules as bookings.

**Acceptance criteria:**
- [x] Room create, read, update, delete, and search are available in the application.
- [x] Availability excludes rooms with overlapping non-cancelled stays in the requested interval.
- [x] Invalid dates and non-positive rates are rejected with clear errors.

**Verification:**
- [ ] Run `python -m unittest tests.test_rooms -v`.
- [ ] Manually verify room management and an availability search through Tkinter where a display is available.

**Dependencies:** Task 1

**Files likely touched:**
- `hotel/rooms.py`
- `hotel/ui.py`
- `tests/test_rooms.py`

**Estimated scope:** Medium

### Task 5: Deliver booking creation, search, check-in, and check-out
**Description:** Add reservations connecting existing customers and rooms, prevent date conflicts transactionally, and implement reserved-booking edits/deletes plus valid booking status transitions in a front-desk screen.

**Acceptance criteria:**
- [x] Bookings require an existing customer, room, and check-out date after check-in.
- [x] Overlapping active stays are rejected, including when attempted concurrently through separate service calls.
- [x] Reserved bookings can be edited or deleted; reservation search and valid reserved-to-checked-in-to-checked-out transitions work; cancellation releases availability.

**Verification:**
- [ ] Run `python -m unittest tests.test_bookings -v`.
- [ ] Manually verify reservation, check-in, and check-out screens where a display is available.

**Dependencies:** Tasks 3 and 4

**Files likely touched:**
- `hotel/bookings.py`
- `hotel/ui.py`
- `tests/test_bookings.py`

**Estimated scope:** Medium

### Task 6: Deliver stored invoices and the end-to-end front-desk flow
**Description:** Generate an invoice for a checked-out booking using its saved nightly rate and number of nights; show and retain the invoice in the application. Add concise run and data-file guidance.

**Acceptance criteria:**
- [x] Only eligible checked-out bookings can be invoiced, and invoice generation is idempotent.
- [x] Invoice details show customer, room, stay dates, nights, nightly rate, and total; total is rate times nights.
- [x] The generated invoice can be retrieved after application restart.
- [x] Documentation explains first launch, run command, and local database location.

**Verification:**
- [ ] Run `python -m unittest tests.test_billing -v`.
- [ ] Run full suite: `python -m unittest discover -s tests -v`.
- [ ] Run `python -m py_compile main.py hotel/*.py`.
- [ ] Manually verify administrator setup through invoice generation where a display is available.

**Dependencies:** Task 5

**Files likely touched:**
- `hotel/billing.py`
- `hotel/ui.py`
- `tests/test_billing.py`
- `README.md`

**Estimated scope:** Medium

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Tkinter cannot be opened in a headless environment | UI launch cannot be manually tested in this environment | Keep domain logic independent; run unit tests and compile checks, and attempt UI launch only when a display is available. |
| Two reservation attempts race for one room | Double booking | Check availability and insert reservation within one SQLite write transaction. |
| UI callbacks accumulate business logic | Untestable validation and inconsistent behavior | Put validation and persistence in services; keep callbacks focused on inputs, service calls, and display refresh. |
| Existing runtime database schema changes later | Local data could become incompatible | Keep initial schema creation idempotent and do not delete or overwrite existing user data. |

## Open Questions
- None. Scope and billing behavior were approved in the capability map and module specs.
