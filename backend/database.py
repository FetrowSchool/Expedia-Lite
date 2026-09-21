"""SQLite initialization and connections for Expedia Lite."""

import csv
import sqlite3
from pathlib import Path

DATA_DIRECTORY = Path(__file__).parent / "data"
DATABASE_PATH = DATA_DIRECTORY / "expedia_lite.db"
SEED_MARKER_KEY = "starter_data_seeded"
BOOKING_SEQUENCE_KEY = "next_booking_number"
USER_SEQUENCE_KEY = "next_user_number"
SEARCH_HISTORY_SEQUENCE_KEY = "next_search_history_number"


def _initialize_booking_sequence(connection: sqlite3.Connection) -> None:
    """Create the durable booking-ID counter without lowering an existing value."""
    highest_number = connection.execute(
        """
        SELECT COALESCE(MAX(CAST(SUBSTR(booking_id, 2) AS INTEGER)), 0)
        FROM bookings
        WHERE booking_id GLOB 'B[0-9]*'
        """
    ).fetchone()[0]
    connection.execute(
        "INSERT OR IGNORE INTO app_metadata (key, value) VALUES (?, ?)",
        (BOOKING_SEQUENCE_KEY, str(highest_number + 1)),
    )


def _initialize_id_sequence(
    connection: sqlite3.Connection,
    *,
    table: str,
    id_column: str,
    prefix: str,
    metadata_key: str,
) -> None:
    """Create a durable prefixed-ID counter without lowering an existing value."""
    highest_number = connection.execute(
        f"""
        SELECT COALESCE(MAX(CAST(SUBSTR({id_column}, {len(prefix) + 1}) AS INTEGER)), 0)
        FROM {table}
        WHERE {id_column} GLOB ?
        """,
        (f"{prefix}[0-9]*",),
    ).fetchone()[0]
    connection.execute(
        "INSERT OR IGNORE INTO app_metadata (key, value) VALUES (?, ?)",
        (metadata_key, str(highest_number + 1)),
    )


def _initialize_account_sequences(connection: sqlite3.Connection) -> None:
    """Initialize durable IDs for accounts and search-history records."""
    _initialize_id_sequence(
        connection,
        table="users",
        id_column="user_id",
        prefix="U",
        metadata_key=USER_SEQUENCE_KEY,
    )
    _initialize_id_sequence(
        connection,
        table="search_history",
        id_column="search_history_id",
        prefix="S",
        metadata_key=SEARCH_HISTORY_SEQUENCE_KEY,
    )


def _migrate_users_for_accounts(connection: sqlite3.Connection) -> None:
    """Add account fields in place and retain every existing user row and ID."""
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()
    }
    if "username" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN username TEXT")
    if "password" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN password TEXT")
    if "email" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN email TEXT")

    users_without_credentials = connection.execute(
        """
        SELECT user_id
        FROM users
        WHERE username IS NULL OR TRIM(username) = ''
           OR password IS NULL OR password = ''
        ORDER BY user_id
        """
    ).fetchall()
    for user in users_without_credentials:
        user_id = user["user_id"]
        connection.execute(
            """
            UPDATE users
            SET username = COALESCE(NULLIF(TRIM(username), ''), ?),
                password = COALESCE(NULLIF(password, ''), ?)
            WHERE user_id = ?
            """,
            (f"traveler-{user_id.lower()}", f"demo-{user_id.lower()}-pass", user_id),
        )

    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS users_username_unique
        ON users (username COLLATE NOCASE)
        """
    )


def _migrate_search_history(connection: sqlite3.Connection) -> None:
    """Align existing search history with the city-search response snapshot."""
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(search_history)").fetchall()
    }
    if "hotel_query" in columns and "search_query" not in columns:
        connection.execute(
            "ALTER TABLE search_history RENAME COLUMN hotel_query TO search_query"
        )
        columns.remove("hotel_query")
        columns.add("search_query")
    if "results_json" not in columns:
        connection.execute(
            "ALTER TABLE search_history ADD COLUMN results_json TEXT NOT NULL DEFAULT '[]'"
        )
    if "search_count" not in columns:
        connection.execute(
            "ALTER TABLE search_history ADD COLUMN search_count INTEGER NOT NULL DEFAULT 1"
        )
    if "price_multiplier" not in columns:
        connection.execute(
            "ALTER TABLE search_history ADD COLUMN price_multiplier REAL NOT NULL DEFAULT 1.0"
        )


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
                display_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password TEXT NOT NULL,
                email TEXT
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

            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS search_history (
                search_history_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                search_query TEXT NOT NULL,
                normalized_query TEXT NOT NULL,
                searched_at TEXT NOT NULL,
                results_json TEXT NOT NULL DEFAULT '[]',
                search_count INTEGER NOT NULL DEFAULT 1,
                price_multiplier REAL NOT NULL DEFAULT 1.0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            """
        )

        connection.execute("BEGIN IMMEDIATE")
        _migrate_users_for_accounts(connection)
        _migrate_search_history(connection)
        seed_marker = connection.execute(
            "SELECT value FROM app_metadata WHERE key = ?",
            (SEED_MARKER_KEY,),
        ).fetchone()
        if seed_marker is not None:
            _initialize_booking_sequence(connection)
            _initialize_account_sequences(connection)
            return

        existing_record_count = sum(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("hotels", "trips", "users", "bookings")
        )
        if existing_record_count:
            connection.execute(
                "INSERT INTO app_metadata (key, value) VALUES (?, '1')",
                (SEED_MARKER_KEY,),
            )
            _initialize_booking_sequence(connection)
            _initialize_account_sequences(connection)
            return

        hotels = _read_csv(data_directory, "hotels.csv")
        connection.executemany(
            """
            INSERT INTO hotels
                (hotel_id, hotel_name, city, state, nightly_rate_usd)
            VALUES (:hotel_id, :hotel_name, :city, :state, :nightly_rate_usd)
            """,
            hotels,
        )

        trips = _read_csv(data_directory, "trips.csv")
        connection.executemany(
            """
            INSERT INTO trips
                (trip_id, hotel_id, trip_name, check_in, check_out)
            VALUES (:trip_id, :hotel_id, :trip_name, :check_in, :check_out)
            """,
            trips,
        )

        users = _read_csv(data_directory, "users.csv")
        for user in users:
            user["username"] = f"traveler-{user['user_id'].lower()}"
            user["password"] = f"demo-{user['user_id'].lower()}-pass"
            user["email"] = ""
        connection.executemany(
            """
            INSERT INTO users (user_id, display_name, username, password, email)
            VALUES (:user_id, :display_name, :username, :password, NULLIF(:email, ''))
            """,
            users,
        )

        bookings = _read_csv(data_directory, "bookings.csv")
        connection.executemany(
            """
            INSERT INTO bookings
                (booking_id, user_id, trip_id, booked_on, status)
            VALUES (:booking_id, :user_id, :trip_id, :booked_on, :status)
            """,
            bookings,
        )
        connection.execute(
            "INSERT INTO app_metadata (key, value) VALUES (?, '1')",
            (SEED_MARKER_KEY,),
        )
        _initialize_booking_sequence(connection)
        _initialize_account_sequences(connection)
