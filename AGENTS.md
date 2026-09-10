# Project rules

- Keep FastAPI code and CSV handling in `backend/`; keep Vue code in `frontend/`.
- Use Python 3.11+ with type hints and Vue 3's Composition API.
- Preserve the Part 1 API contract: `GET /health` and `GET /api/stays?city=<city>`.
- Treat `hotel_id` as the join key between `hotels.csv` and `trips.csv`.
- Keep Part 1 focused on city search. Do not add booking or SQLite CRUD unless a Part 2 task requests it.
- Do not commit `.venv`, `node_modules`, Vite build output, secrets, or local environment files.
- Update documentation when behavior, setup, or structure changes.
- Make focused changes and do not rewrite unrelated user work.

## Verification

- Backend: `backend/.venv/bin/python -m pytest -q backend`
- Frontend, from `frontend/`: `./node_modules/.bin/oxlint .`, `./node_modules/.bin/eslint .`, and `npm run build`
- For UI changes, verify a matching city and a no-results city through the running application.
