# Expedia Lite

Expedia Lite is a local Part 1 travel application that searches supplied hotel-stay data by destination city. It uses a Vue frontend and a Python/FastAPI backend.

## Technology stack

- Vue 3 and Vite for the browser interface
- Python 3.11+ and FastAPI for the HTTP API
- CSV files for the Part 1 hotel and trip data

## Project structure

```text
backend/
  data/hotels.csv     Hotel names, locations, and nightly rates
  data/trips.csv      Offered trips with hotel IDs and dates
  main.py             FastAPI routes and response models
  travel_data.py      CSV loading, joining, filtering, and price calculation
  test_*.py           Backend tests (including legacy calculator tests)
frontend/
  src/App.vue         City-search form, results table, and messages
  src/api/travel.js   Request to the stays API
  vite.config.js      Vite configuration and local API proxy
docs/                 Design and verification notes
handoffs/             Current continuation note
prompts/              Selected prompts used during Part 1 work
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

## Part 1 city search

The user enters a city and submits the Vue form. The frontend requests `GET /api/stays?city=<city>` through Vite's local proxy. FastAPI compares the city without regard to capitalization or outer whitespace, joins trip rows to hotel rows by `hotel_id`, calculates the number of nights and total stay price, and returns matching stays as JSON. Vue displays those stays in a labeled table or shows a no-results message when the returned list is empty.
