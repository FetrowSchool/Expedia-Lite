"""Geoapify live-hotel search orchestration for a validated U.S. postcode."""

import math

import httpx

from config import get_geoapify_api_key
from models import LiveHotel, LiveHotelSearchResponse
from zip_controller import (
    GEOAPIFY_TIMEOUT_SECONDS,
    GeoapifyConfigurationError,
    GeoapifyProviderError,
    lookup_us_postcode,
)


GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
HOTEL_CATEGORY = "accommodation.hotel"
HOTEL_SEARCH_RADIUS_METERS = 5_000
HOTEL_RESULT_LIMIT = 20


def _valid_coordinate(value: object, minimum: float, maximum: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and minimum <= float(value) <= maximum
    )


def _optional_text(properties: dict[str, object], field: str) -> str | None:
    value = properties.get(field)
    return str(value).strip() if value is not None and str(value).strip() else None


def _hotel_from_feature(feature: object) -> LiveHotel | None:
    if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
        return None

    properties = feature["properties"]
    place_id = _optional_text(properties, "place_id")
    latitude = properties.get("lat")
    longitude = properties.get("lon")
    if (
        place_id is None
        or not _valid_coordinate(latitude, -90.0, 90.0)
        or not _valid_coordinate(longitude, -180.0, 180.0)
    ):
        return None

    return LiveHotel(
        place_id=place_id,
        name=_optional_text(properties, "name"),
        address=_optional_text(properties, "formatted"),
        latitude=float(latitude),
        longitude=float(longitude),
    )


def search_live_hotels(
    postcode: str,
    client: httpx.Client | None = None,
) -> LiveHotelSearchResponse:
    """Resolve a ZIP center and return provider-backed hotels within 5 km."""
    request_client = client or httpx.Client()
    try:
        location = lookup_us_postcode(postcode, request_client)
        api_key = get_geoapify_api_key()
        if api_key is None:
            raise GeoapifyConfigurationError(
                "The live hotel provider is not configured."
            )

        center = f"{location.longitude},{location.latitude}"
        try:
            response = request_client.get(
                GEOAPIFY_PLACES_URL,
                params={
                    "categories": HOTEL_CATEGORY,
                    "filter": (
                        f"circle:{center},{HOTEL_SEARCH_RADIUS_METERS}"
                    ),
                    "bias": f"proximity:{center}",
                    "limit": HOTEL_RESULT_LIMIT,
                    "apiKey": api_key,
                },
                timeout=GEOAPIFY_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            raise GeoapifyProviderError(
                "The live hotel provider request failed."
            ) from None
    finally:
        if client is None:
            request_client.close()

    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise GeoapifyProviderError(
            "The live hotel provider returned an invalid response."
        )

    features = payload["features"]
    hotels_by_id: dict[str, LiveHotel] = {}
    for feature in features:
        hotel = _hotel_from_feature(feature)
        if hotel is not None:
            hotels_by_id.setdefault(hotel.place_id, hotel)

    if features and not hotels_by_id:
        raise GeoapifyProviderError(
            "The live hotel provider returned no usable hotel records."
        )

    return LiveHotelSearchResponse(
        resolved_zip=location.postcode,
        resolved_city=location.locality,
        resolved_state=location.state,
        country_code=location.country_code,
        search_center_latitude=location.latitude,
        search_center_longitude=location.longitude,
        radius_meters=HOTEL_SEARCH_RADIUS_METERS,
        hotels=list(hotels_by_id.values()),
    )
