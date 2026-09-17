# Part 2 booking cancellation

The user requested a Vue cancellation control that sends updates through FastAPI. Cancellation must update the SQLite status rather than delete the record, retain the booking in history, show errors clearly, and persist after browser refresh. Direct Vue access to SQLite is prohibited.
