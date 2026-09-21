# Expedia Lite — Part 2 Report

## Repository and commit

- GitHub repository URL: `<ADD_FINAL_GITHUB_REPOSITORY_URL>`
- Final Part 2 commit hash: `<ADD_FINAL_PART_2_COMMIT_HASH>`

## Implementation

Expedia Lite uses a Vue 3 frontend, FastAPI backend, and local SQLite database. The supplied hotel, trip, user, and booking CSV records are imported when an empty database is initialized. Their IDs are preserved, and a one-time metadata marker prevents later starts from duplicating or restoring starter records.

Pydantic models describe hotels, trips, users, bookings, city-search results, and booking history. Trips reference hotels through `hotel_id`; bookings reference users and trips through `user_id` and `trip_id`. Vue is the View, `backend/database_controller.py` performs SQLite reads and CRUD operations, and FastAPI connects the frontend to that controller.

The user searches by **city**. Vue sends `GET /api/stays?city=<city>`, and the backend joins SQLite hotel and trip records through `hotel_id`. Matching stays appear in the results table.

For simulated booking, the user selects a stay and starter traveler. Vue sends `user_id` and `trip_id` to FastAPI, which stores a confirmed booking in SQLite. A durable counter generates unique `B###` IDs beyond the seeded examples and does not reuse deleted IDs.

Booking history is read from SQLite and joins each booking to its traveler, trip, and hotel. The implemented CRUD flow is:

- Create: add a confirmed booking.
- Read: display SQLite booking history.
- Update: change a booking to `cancelled` while retaining it.
- Delete: remove a selected test booking without deleting its related user, trip, or hotel.

All operations follow Vue → FastAPI → database controller → SQLite. Saved changes persist across browser refreshes and service restarts.

## Verification

- Successful city search: Boston returned four matching stays with labeled result columns.
- No-results search: Atlantis displayed `No hotel stays were found for Atlantis.`
- Create/read: booking `B013` was created through the frontend and appeared in booking history.
- Update: `B013` was cancelled through the frontend and remained visible with `cancelled` status.
- Refresh persistence: `B013` remained cancelled after browser refresh.
- Restart persistence: `B013` remained cancelled after frontend and backend restarts.
- Delete: test booking `B014` was created and deleted through the frontend. It remained absent after refresh and frontend/backend restarts.
- Duplicate prevention: after restarts, SQLite contained 8 unique hotels, 12 unique trips, 6 unique users, and 13 unique bookings. The seed marker was still set.
- Automated checks: all 31 backend tests passed; Oxlint, ESLint, and the Vue production build passed.

## Project context and next steps

Part 2 is implemented and verified. Bookings remain simulated, travelers come from starter data, and SQLite is local to one application instance. Authentication, payments, surge pricing, and production deployment are outside the implemented scope. The next step is to add the final repository URL and Part 2 commit hash, review the submission, then commit and push when requested.

- [README](README.md)
- [Project rules](AGENTS.md)
- [Design notes](docs/design.md)
- [Selected prompts](prompts/README.md)
- [Current handoff](handoffs/current.md)
