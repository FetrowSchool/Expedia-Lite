from fastapi.testclient import TestClient

import booking_data
from database import DATA_DIRECTORY, initialize_database
from main import app

client = TestClient(app)


def test_search_stays_returns_joined_boston_results() -> None:
    response = client.get("/api/stays", params={"city": "Boston"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["city"] == "Boston"
    assert [stay["trip_id"] for stay in payload["stays"]] == ["T001", "T002", "T009", "T010"]
    assert payload["stays"][0] == {
        "trip_id": "T001",
        "trip_name": "Boston Harbor Weekend",
        "hotel_name": "Harbor Lantern Hotel",
        "city": "Boston",
        "state": "MA",
        "check_in": "2026-09-18",
        "check_out": "2026-09-20",
        "nights": 2,
        "nightly_rate_usd": 150.0,
        "stay_price_usd": 300.0,
    }


def test_search_stays_ignores_city_capitalization() -> None:
    response = client.get("/api/stays", params={"city": "new york"})

    assert response.status_code == 200
    assert [stay["trip_id"] for stay in response.json()["stays"]] == ["T003", "T004", "T011"]


def test_search_stays_returns_an_empty_list_for_an_unknown_city() -> None:
    response = client.get("/api/stays", params={"city": "Miami"})

    assert response.status_code == 200
    assert response.json() == {"city": "Miami", "stays": []}


def test_list_users_returns_seeded_travelers(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    response = client.get("/api/users")

    assert response.status_code == 200
    assert response.json()[0] == {
        "user_id": "U001",
        "display_name": "Demo Traveler 1",
    }
    assert len(response.json()) == 6


def test_create_booking_persists_a_confirmed_booking(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    response = client.post(
        "/api/bookings",
        json={"user_id": "U006", "trip_id": "T012"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "booking_id": "B007",
        "user_id": "U006",
        "trip_id": "T012",
        "booked_on": response.json()["booked_on"],
        "status": "confirmed",
    }

    with booking_data.connect(database_path) as connection:
        stored_booking = connection.execute(
            "SELECT user_id, trip_id, status FROM bookings WHERE booking_id = 'B007'"
        ).fetchone()

    assert tuple(stored_booking) == ("U006", "T012", "confirmed")


def test_create_booking_rejects_an_unknown_user(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    response = client.post(
        "/api/bookings",
        json={"user_id": "U999", "trip_id": "T001"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User U999 was not found."}


def test_create_booking_rejects_missing_ids() -> None:
    response = client.post("/api/bookings", json={})

    assert response.status_code == 422


def test_booking_history_returns_seeded_relationships(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    response = client.get("/api/bookings")

    assert response.status_code == 200
    assert len(response.json()) == 6
    assert response.json()[0] == {
        "booking_id": "B001",
        "user_id": "U001",
        "display_name": "Demo Traveler 1",
        "trip_id": "T001",
        "trip_name": "Boston Harbor Weekend",
        "hotel_name": "Harbor Lantern Hotel",
        "city": "Boston",
        "state": "MA",
        "booked_on": "2026-09-01",
        "status": "confirmed",
    }


def test_new_booking_appears_in_booking_history(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    create_response = client.post(
        "/api/bookings",
        json={"user_id": "U006", "trip_id": "T012"},
    )
    history_response = client.get("/api/bookings")

    assert create_response.status_code == 201
    assert history_response.status_code == 200
    assert history_response.json()[-1]["booking_id"] == "B007"
    assert history_response.json()[-1]["display_name"] == "Demo Traveler 6"
    assert history_response.json()[-1]["hotel_name"] == "Capitol Grove Hotel"


def test_booking_history_can_be_empty(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    with booking_data.connect(database_path) as connection:
        connection.execute("DELETE FROM bookings")

    response = client.get("/api/bookings")

    assert response.status_code == 200
    assert response.json() == []


def test_cancel_booking_updates_status_without_deleting_row(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    response = client.patch("/api/bookings/B001/cancel")

    assert response.status_code == 200
    assert response.json()["booking_id"] == "B001"
    assert response.json()["status"] == "cancelled"

    with booking_data.connect(database_path) as connection:
        stored_booking = connection.execute(
            "SELECT status FROM bookings WHERE booking_id = 'B001'"
        ).fetchone()
        booking_count = connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]

    assert stored_booking["status"] == "cancelled"
    assert booking_count == 6


def test_cancel_booking_is_idempotent(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    first_response = client.patch("/api/bookings/B002/cancel")
    second_response = client.patch("/api/bookings/B002/cancel")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "cancelled"


def test_cancel_booking_rejects_unknown_booking_id(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    response = client.patch("/api/bookings/B999/cancel")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking B999 was not found."}


def test_create_then_delete_booking_removes_only_booking(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    create_response = client.post(
        "/api/bookings",
        json={"user_id": "U006", "trip_id": "T012"},
    )
    booking_id = create_response.json()["booking_id"]
    delete_response = client.delete(f"/api/bookings/{booking_id}")
    history_response = client.get("/api/bookings")

    assert create_response.status_code == 201
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert booking_id not in {
        booking["booking_id"] for booking in history_response.json()
    }

    with booking_data.connect(database_path) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("hotels", "trips", "users", "bookings")
        }

    assert counts == {"hotels": 8, "trips": 12, "users": 6, "bookings": 6}


def test_delete_booking_rejects_unknown_booking_id(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.db"
    initialize_database(database_path, DATA_DIRECTORY)
    monkeypatch.setattr(booking_data, "DATABASE_PATH", database_path)

    response = client.delete("/api/bookings/B999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking B999 was not found."}
