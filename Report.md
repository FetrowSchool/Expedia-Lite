# Expedia Lite — Parts 1 and 2

## Repository

https://github.com/FetrowSchool/Expedia-Lite

## Implementation

Expedia Lite is a local travel application with a Vue 3 frontend, a Python/FastAPI backend, and a SQLite database. Users can search available hotel stays by city, select a stay and seeded traveler, create a simulated booking, view booking history, cancel a booking without deleting it, and delete a test booking.

FastAPI initializes SQLite from the supplied hotel, trip, user, and booking CSV files. Normal application reads and writes use SQLite. Trips reference hotels through `hotel_id`; bookings reference users and trips through `user_id` and `trip_id`. Vue performs every database operation through FastAPI and never accesses SQLite directly.

## Verification

- Searching for Boston returned four matching stays in a table with clear labels.
- Searching for Atlantis displayed `No hotel stays were found for Atlantis.`
- The search, booking, history, cancellation, and deletion requests went through FastAPI.
- A created booking remained available after browser refresh and backend restart.
- Cancelled booking `B009` remained in history with status `cancelled`.
- Deleted test booking `B010` remained absent after browser refresh and backend restart.
- Restarting the backend did not duplicate starter records.
- SQLite foreign-key verification reported no violations.
- The backend suite passed 26 tests. Oxlint, ESLint, and the Vue production build passed.
- The final browser check reported no console warnings or errors after both development servers were running.

## Limitations

Bookings are simulated. Travelers come from starter data, and the application does not include authentication, payments, or production deployment. SQLite is local to one application instance, and cancellation is the only supported booking-status update.

## Project documentation

- [README](README.md)
- [Project rules](AGENTS.md)
- [Design notes](docs/design.md)
- [Verification instructions](docs/verification.md)
- [Selected prompts](prompts/README.md)
- [Current handoff](handoffs/current.md)

Parts 1 and 2 are implemented and verified. The remaining step is assignment submission.
