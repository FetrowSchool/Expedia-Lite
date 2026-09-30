import httpx
import pytest

import zip_controller
from zip_controller import (
    GeoapifyProviderError,
    ZipLookupNotFoundError,
    lookup_us_postcode,
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_lookup_us_postcode_returns_exact_us_match(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["postcode"] == "16802"
        assert request.url.params["type"] == "postcode"
        assert request.url.params["filter"] == "countrycode:us"
        assert request.url.params["format"] == "json"
        assert request.url.params["apiKey"] == "demo-key"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "postcode": "16802",
                        "country": "United States",
                        "country_code": "us",
                        "lat": 40.7982,
                        "lon": -77.8599,
                        "city": "University Park",
                        "state_code": "PA",
                    }
                ]
            },
        )

    with _client(handler) as client:
        location = lookup_us_postcode("16802", client)

    assert location.model_dump() == {
        "postcode": "16802",
        "country_code": "US",
        "latitude": 40.7982,
        "longitude": -77.8599,
        "locality": "University Park",
        "state": "PA",
    }


def test_lookup_us_postcode_preserves_leading_zero(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["postcode"] == "02108"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "postcode": "02108",
                        "country": "United States",
                        "country_code": "us",
                        "lat": 42.357,
                        "lon": -71.0637,
                        "city": "Boston",
                        "state_code": "MA",
                    }
                ]
            },
        )

    with _client(handler) as client:
        location = lookup_us_postcode("02108", client)

    assert location.postcode == "02108"


def test_lookup_us_postcode_rejects_empty_results(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    with _client(handler) as client:
        with pytest.raises(ZipLookupNotFoundError):
            lookup_us_postcode("16802", client)


def test_lookup_us_postcode_rejects_mismatched_location(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "postcode": "16801",
                        "country": "United States",
                        "country_code": "us",
                        "lat": 40.7934,
                        "lon": -77.86,
                    }
                ]
            },
        )

    with _client(handler) as client:
        with pytest.raises(ZipLookupNotFoundError) as error:
            lookup_us_postcode("16802", client)

    assert str(error.value) == "The requested ZIP code could not be resolved."


def test_lookup_us_postcode_rejects_non_us_country(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "postcode": "16802",
                        "country": "Canada",
                        "country_code": "ca",
                        "lat": 40.8032,
                        "lon": -77.8614,
                    }
                ]
            },
        )

    with _client(handler) as client:
        with pytest.raises(ZipLookupNotFoundError):
            lookup_us_postcode("16802", client)


def test_lookup_us_postcode_sanitizes_provider_failure(monkeypatch) -> None:
    monkeypatch.setattr(zip_controller, "get_geoapify_api_key", lambda: "demo-key")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("request contained demo-key", request=request)

    with _client(handler) as client:
        with pytest.raises(GeoapifyProviderError) as error:
            lookup_us_postcode("16802", client)

    assert str(error.value) == "The ZIP lookup provider request failed."
    assert "demo-key" not in str(error.value)
