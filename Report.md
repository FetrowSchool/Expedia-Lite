# Expedia Lite — Part 1

## Repository and commit
https://github.com/FetrowSchool/Expedia-Lite
c157832e02ace5cccc8c86ede9fd2c275d41a657


## Implementation
Expedia Lite is a travel app that lets users search for hotels by city. The frontend uses Vue to provide the user with a search input and a results table. When a user submits a search, the frontend sends a request to the backend for results. The Python backend reads `hotels.csv` and `trips.csv`. The frontend then displays the results in a table with columns describing the trip, hotel, location, dates, nights, nightly rate, and stay price.


## Verification
Action: Entered the city "Boston" and clicked Search.

Expected result: The application should display the hotel stays available in that city in a clear table below.

Observed result: The matching hotel stays were displayed.

Screenshot: ![Success](Screenshots/Successful.png)

Action: Entered the city "Shell City" and clicked Search.

Expected result: The application should display a message stating there are no matching hotels.

Observed result: The application displayed the no-results message.

Screenshot: ![Unsuccessful](Screenshots/Unsuccessful.png)


## Project context and next steps

[README.md](README.md)
[AGENTS.md](AGENTS.md)
[Prompts](prompts)
[Handoffs](handoffs)
[Design notes](docs/design.md)

The app's main limitation is its small hotel dataset. The next step for Part 2 is to use SQLite to implement features such as simulated booking, booking history, and status updates. These will use the Vue frontend and FastAPI backend.
