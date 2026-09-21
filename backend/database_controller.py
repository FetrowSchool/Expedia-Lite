"""SQLite query and booking CRUD controller for Expedia Lite."""

from datetime import date, datetime, timezone
from pathlib import Path
import json
import sqlite3

from database import (
    BOOKING_SEQUENCE_KEY,
    DATABASE_PATH,
    SEARCH_HISTORY_SEQUENCE_KEY,
    USER_SEQUENCE_KEY,
    connect,
)


class UnknownUserError(ValueError):
    """Raised when a booking references a user that does not exist."""


class UnknownTripError(ValueError):
    """Raised when a booking references a trip that does not exist."""


class UnknownBookingError(ValueError):
    """Raised when a booking does not exist."""


class DuplicateUsernameError(ValueError):
    """Raised when an account username is already in use."""


def create_account(
    display_name: str,
    username: str,
    password: str,
    email: str | None = None,
    database_path: Path | None = None,
) -> dict[str, str | None]:
    """Create a local account with a durable unique user ID."""
    normalized_username = username.strip()
    with connect(database_path or DATABASE_PATH) as connection:
        connection.execute("BEGIN IMMEDIATE")
        next_number = int(
            connection.execute(
                "SELECT value FROM app_metadata WHERE key = ?",
                (USER_SEQUENCE_KEY,),
            ).fetchone()[0]
        )
        user_id = f"U{next_number:03d}"
        try:
            connection.execute(
                """
                INSERT INTO users
                    (user_id, display_name, username, password, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    display_name.strip(),
                    normalized_username,
                    password,
                    email.strip() if email and email.strip() else None,
                ),
            )
        except sqlite3.IntegrityError as error:
            if "username" in str(error).lower():
                raise DuplicateUsernameError(
                    f"Username {normalized_username} is already in use."
                ) from error
            raise

        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = ?",
            (str(next_number + 1), USER_SEQUENCE_KEY),
        )

    return {
        "user_id": user_id,
        "display_name": display_name.strip(),
        "username": normalized_username,
        "email": email.strip() if email and email.strip() else None,
    }


def authenticate_account(
    username: str,
    password: str,
    database_path: Path | None = None,
) -> dict[str, str | None] | None:
    """Return a local account when its demo credentials match."""
    with connect(database_path or DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT user_id, display_name, username, email
            FROM users
            WHERE username = ? COLLATE NOCASE AND password = ?
            """,
            (username.strip(), password),
        ).fetchone()
    return dict(row) if row is not None else None


def get_account_by_id(
    user_id: str,
    database_path: Path | None = None,
) -> dict[str, str | None] | None:
    """Retrieve one account without exposing its stored password."""
    with connect(database_path or DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT user_id, display_name, username, email
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row is not None else None


def record_search_history(
    user_id: str,
    search_query: str,
    searched_at: str | None = None,
    database_path: Path | None = None,
) -> dict[str, str]:
    """Record one nonempty city query for an existing user."""
    submitted_query = search_query.strip()
    if not submitted_query:
        raise ValueError("City search query must not be blank.")

    with connect(database_path or DATABASE_PATH) as connection:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
        ).fetchone() is None:
            raise UnknownUserError(f"User {user_id} was not found.")

        next_number = int(
            connection.execute(
                "SELECT value FROM app_metadata WHERE key = ?",
                (SEARCH_HISTORY_SEQUENCE_KEY,),
            ).fetchone()[0]
        )
        search_history_id = f"S{next_number:03d}"
        normalized_query = submitted_query.casefold()
        timestamp = searched_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        connection.execute(
            """
            INSERT INTO search_history
                (search_history_id, user_id, search_query, normalized_query, searched_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                search_history_id,
                user_id,
                submitted_query,
                normalized_query,
                timestamp,
            ),
        )
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = ?",
            (str(next_number + 1), SEARCH_HISTORY_SEQUENCE_KEY),
        )

    return {
        "search_history_id": search_history_id,
        "user_id": user_id,
        "search_query": submitted_query,
        "normalized_query": normalized_query,
        "searched_at": timestamp,
    }


def update_search_history_results(
    search_history_id: str,
    results: list[dict[str, str | int | float]],
    search_count: int,
    price_multiplier: float,
    database_path: Path | None = None,
) -> None:
    """Store the priced result snapshot returned for one recorded search."""
    with connect(database_path or DATABASE_PATH) as connection:
        connection.execute(
            """
            UPDATE search_history
            SET results_json = ?, search_count = ?, price_multiplier = ?
            WHERE search_history_id = ?
            """,
            (json.dumps(results), search_count, price_multiplier, search_history_id),
        )


def list_search_history(
    user_id: str | None = None,
    database_path: Path | None = None,
) -> list[dict[str, str]]:
    """Retrieve shared search history, optionally limited to one user."""
    query = """
        SELECT search_history_id, user_id, search_query, normalized_query, searched_at,
               results_json, search_count, price_multiplier
        FROM search_history
    """
    parameters: tuple[str, ...] = ()
    if user_id is not None:
        query += " WHERE user_id = ?"
        parameters = (user_id,)
    query += " ORDER BY search_history_id"

    with connect(database_path or DATABASE_PATH) as connection:
        rows = connection.execute(query, parameters).fetchall()
    history = []
    for row in rows:
        item = dict(row)
        item["results"] = json.loads(item.pop("results_json"))
        history.append(item)
    return history


def count_search_history(
    user_id: str,
    normalized_query: str,
    day_start_utc: str,
    next_day_start_utc: str,
    database_path: Path | None = None,
) -> int:
    """Count one user's normalized searches within an application-day window."""
    with connect(database_path or DATABASE_PATH) as connection:
        return connection.execute(
            """
            SELECT COUNT(*)
            FROM search_history
            WHERE user_id = ?
              AND normalized_query = ?
              AND searched_at >= ?
              AND searched_at < ?
            """,
            (user_id, normalized_query, day_start_utc, next_day_start_utc),
        ).fetchone()[0]


def search_stays_by_city(
    city: str,
    database_path: Path | None = None,
) -> list[dict[str, str | int | float]]:
    """Retrieve offered stays whose hotel city matches the supplied city."""
    normalized_city = city.strip()
    if not normalized_city:
        return []

    with connect(database_path or DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT
                trips.trip_id,
                trips.trip_name,
                hotels.hotel_name,
                hotels.city,
                hotels.state,
                trips.check_in,
                trips.check_out,
                CAST(julianday(trips.check_out) - julianday(trips.check_in) AS INTEGER)
                    AS nights,
                hotels.nightly_rate_usd,
                hotels.nightly_rate_usd
                    * CAST(julianday(trips.check_out) - julianday(trips.check_in) AS INTEGER)
                    AS stay_price_usd
            FROM trips
            JOIN hotels ON hotels.hotel_id = trips.hotel_id
            WHERE hotels.city = ? COLLATE NOCASE
            ORDER BY trips.trip_id
            """,
            (normalized_city,),
        ).fetchall()

    return [dict(row) for row in rows]


def list_users(database_path: Path | None = None) -> list[dict[str, str]]:
    """Retrieve users in stable ID order."""
    with connect(database_path or DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT user_id, display_name FROM users ORDER BY user_id"
        ).fetchall()

    return [dict(row) for row in rows]


def list_booking_history(database_path: Path | None = None) -> list[dict[str, str]]:
    """Retrieve bookings with related user, trip, and hotel details."""
    with connect(database_path or DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT
                bookings.booking_id,
                bookings.user_id,
                users.display_name,
                bookings.trip_id,
                trips.trip_name,
                hotels.hotel_name,
                hotels.city,
                hotels.state,
                bookings.booked_on,
                bookings.status
            FROM bookings
            JOIN users ON users.user_id = bookings.user_id
            JOIN trips ON trips.trip_id = bookings.trip_id
            JOIN hotels ON hotels.hotel_id = trips.hotel_id
            ORDER BY bookings.booking_id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def create_booking(
    user_id: str,
    trip_id: str,
    database_path: Path | None = None,
) -> dict[str, str]:
    """Create and return a confirmed booking for an existing user and trip."""
    with connect(database_path or DATABASE_PATH) as connection:
        connection.execute("BEGIN IMMEDIATE")

        if connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
        ).fetchone() is None:
            raise UnknownUserError(f"User {user_id} was not found.")

        if connection.execute(
            "SELECT 1 FROM trips WHERE trip_id = ?", (trip_id,)
        ).fetchone() is None:
            raise UnknownTripError(f"Trip {trip_id} was not found.")

        next_number = int(
            connection.execute(
                "SELECT value FROM app_metadata WHERE key = ?",
                (BOOKING_SEQUENCE_KEY,),
            ).fetchone()[0]
        )
        booking_id = f"B{next_number:03d}"
        booked_on = date.today().isoformat()

        connection.execute(
            """
            INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
            VALUES (?, ?, ?, ?, 'confirmed')
            """,
            (booking_id, user_id, trip_id, booked_on),
        )
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = ?",
            (str(next_number + 1), BOOKING_SEQUENCE_KEY),
        )

    return {
        "booking_id": booking_id,
        "user_id": user_id,
        "trip_id": trip_id,
        "booked_on": booked_on,
        "status": "confirmed",
    }


def cancel_booking(
    booking_id: str,
    database_path: Path | None = None,
) -> dict[str, str]:
    """Update an existing booking to cancelled without deleting it."""
    with connect(database_path or DATABASE_PATH) as connection:
        booking = connection.execute(
            """
            SELECT booking_id, user_id, trip_id, booked_on, status
            FROM bookings
            WHERE booking_id = ?
            """,
            (booking_id,),
        ).fetchone()

        if booking is None:
            raise UnknownBookingError(f"Booking {booking_id} was not found.")

        connection.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?",
            (booking_id,),
        )

    return {
        "booking_id": booking["booking_id"],
        "user_id": booking["user_id"],
        "trip_id": booking["trip_id"],
        "booked_on": booking["booked_on"],
        "status": "cancelled",
    }


def delete_booking(booking_id: str, database_path: Path | None = None) -> None:
    """Delete one booking while leaving its related records untouched."""
    with connect(database_path or DATABASE_PATH) as connection:
        result = connection.execute(
            "DELETE FROM bookings WHERE booking_id = ?",
            (booking_id,),
        )

        if result.rowcount == 0:
            raise UnknownBookingError(f"Booking {booking_id} was not found.")
