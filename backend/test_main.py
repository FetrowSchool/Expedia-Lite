from fastapi.testclient import TestClient

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
