# Application design

## Model responsibilities

`backend/models.py` defines hotel, trip, user account, search-history, booking, city-search, and booking-history structures using the stored fields. A trip references a hotel by `hotel_id`; a booking and each search-history row reference a user by `user_id`; a booking references a trip by `trip_id`. Supplied IDs are preserved.

## View responsibilities

Vue owns the Expedia Lite top navigation, Search stays and Bookings views, city input, Search button, loading and error state, results table, no-results message, stay selection, traveler selection, booking feedback, booking-history table, and cancellation and deletion controls. `frontend/src/api/travel.js` sends all search, user, booking-history, creation, cancellation, and deletion requests to FastAPI. Vite proxies local `/api` requests to FastAPI on port 8000; Vue never connects to SQLite directly.

## Controller responsibilities

`backend/database_controller.py` contains SQLite reads, account persistence, shared city-search-history persistence, and booking CRUD operations. Durable SQLite counters keep new `U###`, `S###`, and `B###` IDs unique across deletions and restarts. `backend/account_controller.py` coordinates account creation, credential checks, and server-side session tracking. `backend/search_controller.py` runs the existing city search for the current user, `backend/urgency.py` records and counts same-day searches in `America/New_York`, and `backend/pricing.py` calculates the non-compounding returned price. FastAPI uses an HTTP-only cookie to identify the browser session. Route handlers do not contain SQL.

## FastAPI responsibilities

`backend/main.py` is the communication layer between Vue and the backend. It initializes SQLite, defines the health, search, user, and booking routes, validates API input and output with the models, calls the database controller, and translates controller errors into HTTP responses.

## Data responsibilities

The supplied CSVs provide starter hotels, trips, users, and bookings. `backend/database.py` creates those SQLite tables plus shared `search_history` and `app_metadata` tables. Existing users are extended in place with unique demo account fields without changing their IDs. It imports the CSV records only for an empty database and records a one-time seed marker. Existing databases without that marker are marked initialized without reloading CSV rows. Normal reads and writes use SQLite after initialization.

## CSV connection

`trips.hotel_id` references `hotels.hotel_id`. `bookings.user_id` references `users.user_id`, and `bookings.trip_id` references `trips.trip_id`. The city-search SQL joins trips to hotels through `hotel_id`, preserving the Part 1 response fields and calculations.

## Application flows

- Search: Vue sends a city to `GET /api/stays`; FastAPI joins trips and hotels and returns matching stays.
- Signed-in pricing: the city-search controller records the search and result snapshot, counts the same normalized query for that user and New York calendar day, and returns base price for search 1 or 120% of base from search 2 onward. SQLite base prices are unchanged.
- Booking: Vue sends a selected `user_id` and `trip_id` to `POST /api/bookings`; FastAPI inserts a confirmed booking.
- History: Vue loads `GET /api/bookings`; FastAPI returns bookings joined with traveler, trip, and hotel details.
- Update: Vue sends `PATCH /api/bookings/<booking_id>/cancel`; FastAPI keeps the row and changes its status to `cancelled`.
- Delete: Vue sends `DELETE /api/bookings/<booking_id>`; FastAPI deletes the booking without cascading to its related records.
