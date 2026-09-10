# Part 1 design

## Frontend responsibilities

Vue owns the city input, Search button, loading and error state, results table, and no-results message. `frontend/src/api/travel.js` sends the city to the backend and reports unsuccessful responses to the interface. Vite proxies local `/api` requests to FastAPI on port 8000.

## FastAPI responsibilities

FastAPI exposes `GET /health` and `GET /api/stays?city=<city>`. The stays route trims the submitted city, calls the travel-data search, validates the response shape with Pydantic models, and returns JSON.

## Data responsibilities

`backend/data/hotels.csv` stores each hotel's ID, name, city, state, and nightly rate. `backend/data/trips.csv` stores each offered trip's ID, hotel ID, name, check-in date, and check-out date. `backend/travel_data.py` reads both files, performs case-insensitive city matching, calculates nights, and multiplies nights by the nightly rate for the stay price.

## CSV connection

Each trip row contains a `hotel_id`. The backend indexes hotel rows by that same field, then uses `trip["hotel_id"]` to attach the matching hotel's location, name, and rate to a trip. Part 1 reads the CSV files on each search and does not modify them.
