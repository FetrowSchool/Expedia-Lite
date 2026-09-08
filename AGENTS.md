# Project Rules

These rules apply throughout the repository.

## General

- Keep backend and frontend concerns in their respective directories.
- Make small, focused changes and avoid unrelated refactors.
- Never commit secrets, credentials, virtual environments, dependency directories, or generated build output.
- Update `README.md` when setup steps or project structure change.

## Backend

- Use Python 3.11+ and FastAPI.
- Place application code under `backend/app/`.
- Add type hints to new Python code.
- Keep route handlers concise; move reusable business logic into separate modules as the application grows.
- Add or update tests for behavioral changes.

## Frontend

- Use Vue 3 with the Composition API and Vite.
- Place application code under `frontend/src/`.
- Keep components focused and prefer explicit props and events.
- Add or update tests for behavioral changes.

## Verification

- Run relevant backend and frontend checks before considering a change complete.
- Do not install or upgrade dependencies unless the task explicitly calls for it.
