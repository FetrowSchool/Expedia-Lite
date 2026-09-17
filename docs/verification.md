# Verification

Use the project-local Python environment for backend checks:

```sh
backend/.venv/bin/python -m pytest -q backend
```

Run frontend checks from `frontend/`. Use non-fixing linters during verification so source files remain unchanged:

```sh
./node_modules/.bin/oxlint .
./node_modules/.bin/eslint . --cache --cache-location /private/tmp/hello-agent-eslint-smoke-cache
npm run build
```

The development backend listens on `127.0.0.1:8000` and Vite on `127.0.0.1:5173`. Vite proxies `/api` to the backend. Verify `GET /api/stays?city=Boston` returns four stays, and `GET /api/stays?city=Miami` returns HTTP 200 with an empty `stays` array.

For the booking flow, search for Boston, select a stay, choose a traveler, and click **Book stay**. Confirm the page reports a unique `B###` booking ID, the FastAPI request returns HTTP 201, and the new row remains in SQLite after refreshing the browser.

For booking history, confirm the seeded rows appear on initial page load. Create a booking, confirm its joined traveler/trip/hotel details appear immediately, then refresh and confirm the same booking remains visible.

For cancellation, click **Cancel** on a confirmed booking. Confirm the status changes to `cancelled`, the row remains in history, the API returns HTTP 200, and the status remains cancelled after a browser refresh.

For deletion, create a test booking and click its **Delete** control. Confirm the API returns HTTP 204, the row disappears from history, related user/trip/hotel records remain, and the deletion persists after browser refresh and backend restart.
