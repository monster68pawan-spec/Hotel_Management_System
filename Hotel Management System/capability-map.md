# Capability Map: Hotel Management System

| Module id | Responsibility | Depends on |
|---|---|---|
| identity | Login and authentication | — |
| customers | Customer registration and customer records | — |
| rooms | Room inventory and availability | — |
| bookings | Reservations, check-in, and check-out | customers, rooms |
| billing | Bill generation for stays | bookings |

Build order: identity, customers, rooms → bookings → billing

## Approved scope assumptions

- Single-operator desktop application built with Tkinter.
- SQLite stored locally in a project data file.
- The first launch guides the operator through creating an administrator account.
- Billing generates invoices; it does not process payments.
- The base bill is the room's nightly rate multiplied by the booked nights, with no taxes or add-ons.
