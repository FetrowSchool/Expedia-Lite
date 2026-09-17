"""SQLite-backed user and booking operations for Expedia Lite."""

from datetime import date
from pathlib import Path

from database import DATABASE_PATH, connect


class UnknownUserError(ValueError):
    """Raised when a booking references a user that does not exist."""


class UnknownTripError(ValueError):
    """Raised when a booking references a trip that does not exist."""


class UnknownBookingError(ValueError):
    """Raised when a booking does not exist."""


def list_users(database_path: Path | None = None) -> list[dict[str, str]]:
    """Return users in stable ID order."""
    with connect(database_path or DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT user_id, display_name FROM users ORDER BY user_id"
        ).fetchall()

    return [dict(row) for row in rows]


def list_booking_history(database_path: Path | None = None) -> list[dict[str, str]]:
    """Return bookings with their related user, trip, and hotel details."""
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

        highest_number = connection.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTR(booking_id, 2) AS INTEGER)), 0)
            FROM bookings
            WHERE booking_id GLOB 'B[0-9]*'
            """
        ).fetchone()[0]
        booking_id = f"B{highest_number + 1:03d}"
        booked_on = date.today().isoformat()

        connection.execute(
            """
            INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
            VALUES (?, ?, ?, ?, 'confirmed')
            """,
            (booking_id, user_id, trip_id, booked_on),
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
    """Mark an existing booking as cancelled without deleting it."""
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
