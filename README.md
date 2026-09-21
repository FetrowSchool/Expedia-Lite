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
  models.py            Hotel, trip, user, booking, and API data models
  database_controller.py  SQLite queries and booking CRUD operations
  main.py              Thin FastAPI communication layer
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

The project follows MVC: the data structures and relationships are Models, Vue is the View, `database_controller.py` is the database Controller, and FastAPI connects the View to the controller.

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

When the backend starts with an empty database, it creates `backend/data/expedia_lite.db` and seeds the supplied hotel, trip, user, and booking records with their original IDs. SQLite records a one-time seed marker, so later starts do not reread the CSVs, duplicate starter rows, restore deleted rows, or overwrite user-created bookings. The generated database is local and is not committed.

Existing users are migrated in place with unique made-up demo usernames and passwords; their `user_id` values and booking relationships do not change. New accounts use a durable `U###` sequence. One shared `search_history` table relates city searches to users by `user_id` and uses a durable `S###` ID sequence. Account and search-history rows survive normal application restarts.

## Demo accounts

The Account view creates local classroom-demo accounts with a username, password, and optional email. Duplicate usernames are rejected case-insensitively. Login compares the submitted demo credentials with SQLite and stores an HTTP-only local session cookie; the signed-in username and user ID are then displayed. Logout removes the server-side session and cookie. These plain-text demo credentials are intentionally limited to this classroom application and must not be real personal passwords.

## City search

The top navigation provides Search stays and Bookings views, with the same destinations available from the Menu button. In Search stays, the user enters a city and submits the Vue form. The frontend requests `GET /api/stays?city=<city>` through Vite's local proxy. FastAPI queries SQLite without regard to capitalization or outer whitespace, joins trips to hotels by `hotel_id`, calculates the number of nights and total stay price, and returns matching stays as JSON. Vue displays those stays in a labeled table or shows a no-results message when the returned list is empty.

For a signed-in user, the same city search automatically records the original and normalized query, New York time-zone timestamp, daily same-user/query count, multiplier, and returned result snapshot. The first search returns the stored base price; the second and later matching searches return 120% of base without compounding. Anonymous searches remain untracked and return base prices. Hotel prices stored in SQLite are never changed.

## Simulated booking

After searching, the user selects a stay, chooses one of the seeded travelers, and submits the booking form. Vue sends `POST /api/bookings` with the selected `user_id` and `trip_id`. FastAPI validates both records, uses SQLite's durable counter to generate a unique `B###` booking ID, and stores a confirmed booking. IDs are not reused after deletion, and saved bookings retain their IDs after browser refreshes and backend restarts.

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

The final backend run passed 31 tests. Oxlint, ESLint, and the Vue production build also passed. Manual browser checks found four stays for Boston and displayed the no-results message for Atlantis. A booking was created, read in history, cancelled, and retained through browser and service restarts. A separate test booking was deleted and remained absent after refresh and frontend/backend restarts. SQLite retained unique starter IDs without duplicating starter rows.

## Current limitations

Bookings are simulated, travelers come from starter data, and there is no authentication, payment processing, or production deployment. The SQLite database is local to one application instance.
