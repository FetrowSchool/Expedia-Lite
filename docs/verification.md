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
