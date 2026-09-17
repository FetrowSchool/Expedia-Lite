# Part 2 booking deletion

The user requested a Vue control for deleting a test booking through FastAPI and SQLite. A successful deletion must remove the booking from history and persist after refresh, while leaving related users, trips, and hotels unchanged. Invalid booking IDs must be handled clearly, and Vue must not access SQLite directly.
