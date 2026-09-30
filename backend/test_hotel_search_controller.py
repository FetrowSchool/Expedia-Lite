import httpx
import pytest

import hotel_search_controller
import zip_controller
from hotel_search_controller import search_live_hotels
from zip_controller import GeoapifyProviderError


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _geocode_response(postcode: str = "16802") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "postcode": postcode,
                    "country": "United States",
                    "country_code": "us",
                    "lat": 40.8032,
                    "lon": -77.8614,
                    "city": "State College",
                    "state_code": "PA",
                }
            ]
        },
    )


def test_live_hotel_search_returns_provider_backed_results(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")
    monkeypatch.setattr(
        hotel_search_controller,
        "get_geoapify_api_key",
        lambda: "demo-key",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/geocode/search":
            return _geocode_response()

        assert request.url.path == "/v2/places"
        assert request.url.params["categories"] == "accommodation.hotel"
        assert request.url.params["filter"] == "circle:-77.8614,40.8032,5000"
        assert request.url.params["bias"] == "proximity:-77.8614,40.8032"
        assert request.url.params["apiKey"] == "demo-key"
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "properties": {
                            "place_id": "hotel-1",
                            "name": "Example Hotel",
                            "formatted": "100 College Ave, State College, PA",
                            "lat": 40.802,
                            "lon": -77.86,
                        }
                    }
                ]
            },
        )

    with _client(handler) as client:
        result = search_live_hotels("16802", client)

    assert result.model_dump() == {
        "resolved_zip": "16802",
        "resolved_city": "State College",
        "resolved_state": "PA",
        "country_code": "US",
        "search_center_latitude": 40.8032,
        "search_center_longitude": -77.8614,
        "radius_meters": 5000,
        "hotels": [
            {
                "place_id": "hotel-1",
                "name": "Example Hotel",
                "address": "100 College Ave, State College, PA",
                "latitude": 40.802,
                "longitude": -77.86,
            }
        ],
    }
    assert "price" not in result.model_dump()["hotels"][0]
    assert "rating" not in result.model_dump()["hotels"][0]
    assert "availability" not in result.model_dump()["hotels"][0]


def test_live_hotel_search_returns_success_with_zero_hotels(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")
    monkeypatch.setattr(
        hotel_search_controller,
        "get_geoapify_api_key",
        lambda: "demo-key",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/geocode/search":
            return _geocode_response()
        return httpx.Response(200, json={"features": []})

    with _client(handler) as client:
        result = search_live_hotels("16802", client)

    assert result.hotels == []
    assert result.resolved_zip == "16802"


def test_live_hotel_search_sanitizes_places_failure(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")
    monkeypatch.setattr(
        hotel_search_controller,
        "get_geoapify_api_key",
        lambda: "demo-key",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/geocode/search":
            return _geocode_response()
        raise httpx.ConnectError("request included demo-key", request=request)

    with _client(handler) as client:
        with pytest.raises(GeoapifyProviderError) as error:
            search_live_hotels("16802", client)

    assert str(error.value) == "The live hotel provider request failed."
    assert "demo-key" not in str(error.value)
