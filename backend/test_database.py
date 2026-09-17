import sqlite3
from pathlib import Path

from database import DATA_DIRECTORY, initialize_database


def _table_counts(database_path: Path) -> dict[str, int]:
    with sqlite3.connect(database_path) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("hotels", "trips", "users", "bookings")
        }


def test_initialize_database_seeds_all_starter_records(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"

    initialize_database(database_path, DATA_DIRECTORY)

    assert _table_counts(database_path) == {
        "hotels": 8,
        "trips": 12,
        "users": 6,
        "bookings": 6,
    }


def test_reinitializing_database_does_not_duplicate_records(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"

    initialize_database(database_path, DATA_DIRECTORY)
    counts_after_first_start = _table_counts(database_path)
    initialize_database(database_path, DATA_DIRECTORY)

    assert _table_counts(database_path) == counts_after_first_start


def test_seeded_booking_relationships_are_preserved(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                bookings.booking_id,
                users.user_id,
                trips.trip_id,
                hotels.hotel_id
            FROM bookings
            JOIN users ON users.user_id = bookings.user_id
            JOIN trips ON trips.trip_id = bookings.trip_id
            JOIN hotels ON hotels.hotel_id = trips.hotel_id
            WHERE bookings.booking_id = 'B001'
            """
        ).fetchone()

    assert row == ("B001", "U001", "T001", "H001")
