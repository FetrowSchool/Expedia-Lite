import json
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import search_controller
from database import DATA_DIRECTORY, initialize_database
from search_controller import search_city
from urgency import record_and_count_daily_searches

NEW_YORK = ZoneInfo("America/New_York")


def test_existing_state_college_search_increases_one_hundred_dollar_price_once(
    tmp_path, monkeypatch
) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(
        search_controller,
        "current_account",
        lambda _session_id: {"user_id": "U001", "username": "traveler-u001"},
    )
    now = datetime(2026, 9, 20, 10, 0, tzinfo=NEW_YORK)

    responses = [
        search_city("demo-session", "  State College  ", now, database_path)
        for _ in range(5)
    ]

    assert [response["search_count"] for response in responses] == [1, 2, 3, 4, 5]
    assert [response["stays"][0]["nightly_rate_usd"] for response in responses] == [
        100.0,
        120.0,
        120.0,
        120.0,
        120.0,
    ]
    assert responses[4]["price_increased"] is True

    with sqlite3.connect(database_path) as connection:
        stored_price = connection.execute(
            "SELECT nightly_rate_usd FROM hotels WHERE hotel_id = 'H008'"
        ).fetchone()[0]
        history = connection.execute(
            """
            SELECT search_query, normalized_query, results_json,
                   search_count, price_multiplier
            FROM search_history
            WHERE user_id = 'U001'
            ORDER BY search_history_id
            """
        ).fetchall()
    assert stored_price == 100.0
    assert len(history) == 5
    assert history[-1][0:2] == ("State College", "state college")
    assert json.loads(history[-1][2])[0]["nightly_rate_usd"] == 120.0
    assert [row[4] for row in history] == [1.0, 1.2, 1.2, 1.2, 1.2]
    assert history[-1][3:] == (5, 1.2)


def test_counts_are_separate_by_user_query_and_calendar_day(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    day_one = datetime(2026, 9, 20, 23, 30, tzinfo=NEW_YORK)
    day_two = datetime(2026, 9, 21, 0, 30, tzinfo=NEW_YORK)

    assert record_and_count_daily_searches(
        "U001", "State College", day_one, database_path
    )[0] == 1
    assert record_and_count_daily_searches(
        "U001", " state college ", day_one, database_path
    )[0] == 2
    assert record_and_count_daily_searches(
        "U002", "STATE COLLEGE", day_one, database_path
    )[0] == 1
    assert record_and_count_daily_searches(
        "U001", "Boston", day_one, database_path
    )[0] == 1
    assert record_and_count_daily_searches(
        "U001", "State College", day_two, database_path
    )[0] == 1


def test_anonymous_city_search_returns_base_price_without_history(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)

    response = search_city(None, "State College", database_path=database_path)

    assert "search_count" not in response
    assert response["stays"][0]["nightly_rate_usd"] == 100.0
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM search_history").fetchone()[0] == 0
