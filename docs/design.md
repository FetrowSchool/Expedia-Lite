# Application design

## Frontend responsibilities

Vue owns the city input, Search button, loading and error state, results table, no-results message, stay selection, traveler selection, booking feedback, booking-history table, and cancellation and deletion controls. `frontend/src/api/travel.js` sends all search, user, booking-history, creation, cancellation, and deletion requests to FastAPI. Vite proxies local `/api` requests to FastAPI on port 8000; Vue never connects to SQLite directly.

## FastAPI responsibilities

FastAPI initializes SQLite from the starter CSVs when it starts. It exposes health, stay-search, user, booking-history, creation, cancellation, and deletion routes. The booking POST route validates required IDs, verifies that the user and trip exist, generates the next `B###` ID, and inserts a confirmed booking. The booking GET route joins bookings to users, trips, and hotels for display. The cancellation PATCH route updates status without deleting the row. The DELETE route removes only the selected booking and returns an error for an unknown ID.

## Data responsibilities

The four supplied CSVs provide starter hotels, trips, users, and bookings. `backend/database.py` creates `hotels`, `trips`, `users`, and `bookings` tables and seeds records with `INSERT OR IGNORE`, so restarts do not duplicate primary keys. After initialization, normal searches and booking operations use SQLite rather than reading CSV files.

## CSV connection

`trips.hotel_id` references `hotels.hotel_id`. `bookings.user_id` references `users.user_id`, and `bookings.trip_id` references `trips.trip_id`. The city-search SQL joins trips to hotels through `hotel_id`, preserving the Part 1 response fields and calculations.

## Application flows

- Search: Vue sends a city to `GET /api/stays`; FastAPI joins trips and hotels and returns matching stays.
- Booking: Vue sends a selected `user_id` and `trip_id` to `POST /api/bookings`; FastAPI inserts a confirmed booking.
- History: Vue loads `GET /api/bookings`; FastAPI returns bookings joined with traveler, trip, and hotel details.
- Update: Vue sends `PATCH /api/bookings/<booking_id>/cancel`; FastAPI keeps the row and changes its status to `cancelled`.
- Delete: Vue sends `DELETE /api/bookings/<booking_id>`; FastAPI deletes the booking without cascading to its related records.
