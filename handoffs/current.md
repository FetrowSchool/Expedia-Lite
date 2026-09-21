# Current handoff

## What works

- Vue provides branded top navigation for Search stays and Bookings. It searches hotel stays by city through FastAPI and displays results or a clear no-results message.
- FastAPI reads runtime data from SQLite and joins trips to hotels by `hotel_id`.
- Signed-in city searches are automatically recorded in shared search history and priced by same-user/query/day frequency. Search 1 uses base price; search 2 and later use a single 20% increase. The frontend uses the returned price without a separate pricing search UI.
- An empty database is seeded once from the supplied hotel, trip, user, and booking CSV files while preserving their IDs.
- Users can create simulated bookings, read booking history, cancel bookings without deleting them, and delete test bookings.
- Users can create local demo accounts, receive unique user IDs, log in with made-up credentials, see the signed-in username, and log out. Duplicate usernames are rejected.
- New bookings receive durable unique `B###` IDs. Refreshing or restarting the services does not restore deleted bookings, overwrite saved changes, or duplicate starter rows.
- The structure follows MVC: Pydantic models describe data, Vue is the View, the database controller owns SQLite CRUD, and FastAPI is the API layer.

## Final verification

- Backend: 31 tests passed.
- Frontend: Oxlint, ESLint, and the Vite production build passed.
- Browser: Boston returned four stays; Atlantis displayed the no-results message.
- Persistence: `B013` remained cancelled after browser refresh and frontend/backend restarts. Test booking `B014` remained deleted after refresh and both service restarts.
- Final SQLite counts were 8 unique hotels, 12 unique trips, 6 unique users, and 13 unique bookings. The seed marker remained set and the next booking number was 15.

## Limitations

- Bookings are simulated; there is no authentication, payment processing, surge pricing, or production deployment.
- Travelers are selected from starter users, and cancellation is the only status update.
- SQLite is local to one application instance.
- Legacy calculator files are not part of Expedia Lite.

## Next step

Part 2 implementation and verification are complete. Review the submission files, then commit and push only when requested.
