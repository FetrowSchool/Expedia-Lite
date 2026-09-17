# Expedia Lite

Expedia Lite is a small local travel application for searching hotel stays and managing simulated bookings. Part 2 uses a Vue frontend, a Python/FastAPI backend, and SQLite storage seeded from supplied CSV data.

## Technology stack

- Vue 3 and Vite for the browser interface
- Python 3.11+ and FastAPI for the HTTP API
- SQLite for runtime data, seeded from the supplied CSV files

## Project structure

```text
backend/
  data/*.csv           Starter hotels, trips, users, and bookings
  database.py          SQLite schema, connection, and idempotent seeding
  main.py             FastAPI routes and response models
  travel_data.py      SQLite search, joining, and price calculation
  test_*.py           Backend tests (including legacy calculator tests)
frontend/
  src/App.vue         City search, booking form, and booking history
  src/api/travel.js   Requests to the travel and booking APIs
  vite.config.js      Vite configuration and local API proxy
docs/                 Design and verification notes
handoffs/             Current continuation note
prompts/              Selected prompts used during Parts 1 and 2
```

`backend/calculator.py` and `backend/test_calculator.py` are legacy starter exercise files. They are not used by the Expedia Lite search flow.

## Setup

Create the backend environment and install its declared packages:

```sh
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Install the locked frontend packages:

```sh
cd frontend
npm install
```

## Start the application

Run the backend from `backend/`:

```sh
./.venv/bin/uvicorn main:app --reload
```

Run the frontend in a second terminal from `frontend/`:

```sh
npm run dev
```

Open `http://127.0.0.1:5173`. FastAPI runs at `http://127.0.0.1:8000`.

## Data initialization

When the backend starts, it creates `backend/data/expedia_lite.db` if needed and seeds the supplied hotel, trip, user, and booking records. Primary keys and `INSERT OR IGNORE` prevent duplicate starter rows on later starts. The generated database is local and is not committed.

## City search

The user enters a city and submits the Vue form. The frontend requests `GET /api/stays?city=<city>` through Vite's local proxy. FastAPI queries SQLite without regard to capitalization or outer whitespace, joins trips to hotels by `hotel_id`, calculates the number of nights and total stay price, and returns matching stays as JSON. Vue displays those stays in a labeled table or shows a no-results message when the returned list is empty.

## Simulated booking

After searching, the user selects a stay, chooses one of the seeded travelers, and submits the booking form. Vue sends `POST /api/bookings` with the selected `user_id` and `trip_id`. FastAPI validates both records, generates the next `B###` booking ID, and stores a confirmed booking in SQLite. The saved booking remains in the local database after a browser refresh or backend restart.

The backend also exposes `GET /api/users` so the frontend can list the seeded travelers.

## Booking history

Vue requests `GET /api/bookings` when the page loads and after a booking is created or cancelled. FastAPI joins bookings to users, trips, and hotels in SQLite so the table can show booking, traveler, trip, hotel, location, date, and status information. History remains available after browser refreshes and backend restarts.

Confirmed bookings include a Cancel control. Vue sends `PATCH /api/bookings/<booking_id>/cancel` through FastAPI, which changes the SQLite status to `cancelled` without deleting the record. Cancelled bookings remain visible in history.

Each history row also includes a Delete control for removing test bookings. Vue sends `DELETE /api/bookings/<booking_id>` through FastAPI. The backend deletes only the selected booking; related users, trips, and hotels remain unchanged.

## Verification

Run backend tests from the project root:

```sh
backend/.venv/bin/python -m pytest -q backend
```

Run frontend checks from `frontend/`:

```sh
./node_modules/.bin/oxlint .
./node_modules/.bin/eslint .
npm run build
```

Manual browser checks cover a matching city, a no-results city, booking creation, history, cancellation, deletion, refresh persistence, and backend-restart persistence.

## Current limitations

Bookings are simulated, travelers come from starter data, and there is no authentication, payment processing, or production deployment. The SQLite database is local to one application instance.
