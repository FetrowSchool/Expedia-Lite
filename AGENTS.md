# Project rules

- Keep FastAPI, SQLite, and starter-data handling in `backend/`; keep Vue code in `frontend/`.
- Use Python 3.11+ with type hints and Vue 3's Composition API.
- Preserve `GET /health`, `GET /api/stays?city=<city>`, `GET /api/users`, `GET`/`POST /api/bookings`, `PATCH /api/bookings/<booking_id>/cancel`, and `DELETE /api/bookings/<booking_id>`.
- Treat `hotel_id` as the join key between `hotels.csv` and `trips.csv`.
- Preserve the SQLite relationships for `hotel_id`, `user_id`, and `trip_id`.
- Keep models in `backend/models.py`, SQLite CRUD in `backend/database_controller.py`, and HTTP concerns in `backend/main.py`.
- Seed supplied CSV records only when initializing an empty database; never restore deleted rows or overwrite saved bookings on restart.
- Preserve supplied IDs and use the durable SQLite booking sequence for new unique `B###` IDs.
- Keep demo-account session logic in `backend/account_controller.py`; never expose stored passwords in API responses.
- Treat account passwords as made-up classroom credentials only. Do not add OAuth, password recovery, or personal credentials.
- Keep all database access behind FastAPI; the Vue frontend must never access SQLite directly.
- Keep personalized pricing inside the existing city search. Do not add a separate hotel-name search or expose pricing decisions in Vue.
- Use `America/New_York` for daily search counts; calculate each returned price from the immutable SQLite base price.
- Cancellation updates status and must never delete the booking row.
- Deletion removes only the selected booking; it must not delete related users, trips, or hotels.
- Do not add unrelated booking status changes or features.
- Do not commit `.venv`, `node_modules`, Vite build output, secrets, or local environment files.
- Update documentation when behavior, setup, or structure changes.
- Make focused changes and do not rewrite unrelated user work.

## Verification

- Backend: `backend/.venv/bin/python -m pytest -q backend`
- Frontend, from `frontend/`: `./node_modules/.bin/oxlint .`, `./node_modules/.bin/eslint .`, and `npm run build`
- Through the running application, verify a matching city and a no-results city. When affected, also verify booking creation, history, cancellation, deletion, and persistence across refresh and service restart.
