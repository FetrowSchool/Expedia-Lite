import sqlite3
from pathlib import Path

from database import (
    BOOKING_SEQUENCE_KEY,
    DATA_DIRECTORY,
    SEARCH_HISTORY_SEQUENCE_KEY,
    SEED_MARKER_KEY,
    USER_SEQUENCE_KEY,
    initialize_database,
)
from database_controller import (
    DuplicateUsernameError,
    create_account,
    create_booking,
    delete_booking,
    record_search_history,
)


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


def test_restart_preserves_a_user_created_booking(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    booking = create_booking("U006", "T012", database_path)
    counts_before_restart = _table_counts(database_path)

    initialize_database(database_path, DATA_DIRECTORY)

    assert _table_counts(database_path) == counts_before_restart
    with sqlite3.connect(database_path) as connection:
        stored_booking = connection.execute(
            """
            SELECT user_id, trip_id, status
            FROM bookings
            WHERE booking_id = ?
            """,
            (booking["booking_id"],),
        ).fetchone()

    assert stored_booking == ("U006", "T012", "confirmed")


def test_new_booking_ids_are_unique_even_after_deletion(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)

    first = create_booking("U001", "T001", database_path)
    second = create_booking("U002", "T003", database_path)
    delete_booking(second["booking_id"], database_path)
    third = create_booking("U003", "T007", database_path)

    assert first["booking_id"] == "B007"
    assert second["booking_id"] == "B008"
    assert third["booking_id"] == "B009"
    assert len({first["booking_id"], second["booking_id"], third["booking_id"]}) == 3

    with sqlite3.connect(database_path) as connection:
        next_number = connection.execute(
            "SELECT value FROM app_metadata WHERE key = ?",
            (BOOKING_SEQUENCE_KEY,),
        ).fetchone()[0]

    assert next_number == "10"


def test_restart_does_not_restore_a_deleted_starter_booking(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)

    with sqlite3.connect(database_path) as connection:
        connection.execute("DELETE FROM bookings WHERE booking_id = 'B001'")

    initialize_database(database_path, DATA_DIRECTORY)

    with sqlite3.connect(database_path) as connection:
        restored_booking = connection.execute(
            "SELECT 1 FROM bookings WHERE booking_id = 'B001'"
        ).fetchone()

    assert restored_booking is None
    assert _table_counts(database_path)["bookings"] == 5


def test_existing_database_is_marked_without_reloading_csv_data(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)

    with sqlite3.connect(database_path) as connection:
        connection.execute("DELETE FROM bookings WHERE booking_id = 'B001'")
        connection.execute(
            "DELETE FROM app_metadata WHERE key = ?",
            (SEED_MARKER_KEY,),
        )

    initialize_database(database_path, DATA_DIRECTORY)

    with sqlite3.connect(database_path) as connection:
        restored_booking = connection.execute(
            "SELECT 1 FROM bookings WHERE booking_id = 'B001'"
        ).fetchone()
        marker = connection.execute(
            "SELECT value FROM app_metadata WHERE key = ?",
            (SEED_MARKER_KEY,),
        ).fetchone()

    assert restored_booking is None
    assert marker == ("1",)


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


def test_existing_users_receive_unique_demo_credentials_without_changing_ids(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)

    with sqlite3.connect(database_path) as connection:
        users = connection.execute(
            "SELECT user_id, username, password FROM users ORDER BY user_id"
        ).fetchall()
        booking_relationships = connection.execute(
            """
            SELECT COUNT(*)
            FROM bookings
            JOIN users ON users.user_id = bookings.user_id
            """
        ).fetchone()[0]

    assert [user[0] for user in users] == [f"U{number:03d}" for number in range(1, 7)]
    assert len({user[1].casefold() for user in users}) == 6
    assert all(user[1] and user[2] for user in users)
    assert booking_relationships == 6


def test_new_accounts_receive_durable_unique_user_ids(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)

    first = create_account("Demo Seven", "demo-seven", "password-7", None, database_path)
    second = create_account(
        "Demo Eight", "demo-eight", "password-8", "eight@example.test", database_path
    )
    initialize_database(database_path, DATA_DIRECTORY)

    assert first["user_id"] == "U007"
    assert second["user_id"] == "U008"
    with sqlite3.connect(database_path) as connection:
        stored_ids = connection.execute(
            "SELECT user_id FROM users WHERE user_id IN ('U007', 'U008') ORDER BY user_id"
        ).fetchall()
        next_number = connection.execute(
            "SELECT value FROM app_metadata WHERE key = ?", (USER_SEQUENCE_KEY,)
        ).fetchone()[0]
    assert stored_ids == [("U007",), ("U008",)]
    assert next_number == "9"


def test_duplicate_usernames_are_rejected_case_insensitively(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    create_account("Demo Seven", "demo-seven", "password-7", None, database_path)

    try:
        create_account("Duplicate", "DEMO-SEVEN", "another-password", None, database_path)
    except DuplicateUsernameError as error:
        assert "already in use" in str(error)
    else:
        raise AssertionError("Expected a duplicate username to be rejected")


def test_shared_search_history_preserves_relationships_and_survives_restart(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    first = record_search_history(
        "U001", "  Harbor Lantern Hotel  ", "2026-09-20T10:00:00-04:00", database_path
    )
    second = record_search_history(
        "U002", "HARBOR LANTERN HOTEL", "2026-09-20T11:00:00-04:00", database_path
    )
    initialize_database(database_path, DATA_DIRECTORY)

    assert first["search_history_id"] == "S001"
    assert second["search_history_id"] == "S002"
    assert first["search_query"] == "Harbor Lantern Hotel"
    assert first["normalized_query"] == second["normalized_query"]

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT search_history_id, search_history.user_id
            FROM search_history
            JOIN users ON users.user_id = search_history.user_id
            ORDER BY search_history_id
            """
        ).fetchall()
        next_number = connection.execute(
            "SELECT value FROM app_metadata WHERE key = ?",
            (SEARCH_HISTORY_SEQUENCE_KEY,),
        ).fetchone()[0]
    assert rows == [("S001", "U001"), ("S002", "U002")]
    assert next_number == "3"


def test_account_and_search_history_changes_do_not_modify_hotel_base_prices(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    with sqlite3.connect(database_path) as connection:
        prices_before = connection.execute(
            "SELECT hotel_id, nightly_rate_usd FROM hotels ORDER BY hotel_id"
        ).fetchall()

    create_account("Demo Seven", "demo-seven", "password-7", None, database_path)
    record_search_history("U007", "Maple Square Inn", None, database_path)

    with sqlite3.connect(database_path) as connection:
        prices_after = connection.execute(
            "SELECT hotel_id, nightly_rate_usd FROM hotels ORDER BY hotel_id"
        ).fetchall()
    assert prices_after == prices_before
