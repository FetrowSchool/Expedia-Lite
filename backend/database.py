"""SQLite initialization and connections for Expedia Lite."""

import csv
import sqlite3
from pathlib import Path

DATA_DIRECTORY = Path(__file__).parent / "data"
DATABASE_PATH = DATA_DIRECTORY / "expedia_lite.db"


def connect(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with relationship checks enabled."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _read_csv(data_directory: Path, filename: str) -> list[dict[str, str]]:
    """Read a starter CSV while handling its UTF-8 BOM."""
    with (data_directory / filename).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def initialize_database(
    database_path: Path = DATABASE_PATH,
    data_directory: Path = DATA_DIRECTORY,
) -> None:
    """Create the database and seed each starter record exactly once."""
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS hotels (
                hotel_id TEXT PRIMARY KEY,
                hotel_name TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                nightly_rate_usd REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                hotel_id TEXT NOT NULL,
                trip_name TEXT NOT NULL,
                check_in TEXT NOT NULL,
                check_out TEXT NOT NULL,
                FOREIGN KEY (hotel_id) REFERENCES hotels (hotel_id)
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                booking_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                trip_id TEXT NOT NULL,
                booked_on TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
            );
            """
        )

        hotels = _read_csv(data_directory, "hotels.csv")
        connection.executemany(
            """
            INSERT OR IGNORE INTO hotels
                (hotel_id, hotel_name, city, state, nightly_rate_usd)
            VALUES (:hotel_id, :hotel_name, :city, :state, :nightly_rate_usd)
            """,
            hotels,
        )

        trips = _read_csv(data_directory, "trips.csv")
        connection.executemany(
            """
            INSERT OR IGNORE INTO trips
                (trip_id, hotel_id, trip_name, check_in, check_out)
            VALUES (:trip_id, :hotel_id, :trip_name, :check_in, :check_out)
            """,
            trips,
        )

        users = _read_csv(data_directory, "users.csv")
        connection.executemany(
            """
            INSERT OR IGNORE INTO users (user_id, display_name)
            VALUES (:user_id, :display_name)
            """,
            users,
        )

        bookings = _read_csv(data_directory, "bookings.csv")
        connection.executemany(
            """
            INSERT OR IGNORE INTO bookings
                (booking_id, user_id, trip_id, booked_on, status)
            VALUES (:booking_id, :user_id, :trip_id, :booked_on, :status)
            """,
            bookings,
        )
