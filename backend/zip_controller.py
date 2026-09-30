"""Geoapify-backed U.S. postcode lookup controller.

The public contract returns a small ``ZipLocation`` for an exact U.S.
postcode match. ``ZipLookupNotFoundError`` means the provider responded but
did not resolve that postcode. ``GeoapifyProviderError`` means configuration,
transport, HTTP, or response parsing failed. Neither error exposes request
credentials or raw provider details.
"""

import math

import httpx

from config import get_geoapify_api_key
from models import ZipLocation


GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_TIMEOUT_SECONDS = 5.0


class ZipLookupNotFoundError(LookupError):
    """Raised when Geoapify does not resolve the requested U.S. postcode."""


class GeoapifyProviderError(RuntimeError):
    """Raised when the provider lookup cannot be completed safely."""


class GeoapifyConfigurationError(GeoapifyProviderError):
    """Raised when the provider key is not configured."""


def _valid_coordinate(value: object, minimum: float, maximum: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and minimum <= float(value) <= maximum
    )


def _location_from_result(result: object, postcode: str) -> ZipLocation | None:
    if not isinstance(result, dict):
        return None

    result_postcode = str(result.get("postcode", "")).strip()
    country_code = str(result.get("country_code", "")).strip().casefold()
    country = str(result.get("country", "")).strip().casefold()
    latitude = result.get("lat")
    longitude = result.get("lon")
    if (
        result_postcode != postcode
        or country_code != "us"
        or country not in {"united states", "united states of america"}
        or not _valid_coordinate(latitude, -90.0, 90.0)
        or not _valid_coordinate(longitude, -180.0, 180.0)
    ):
        return None

    locality = next(
        (
            str(result[field]).strip()
            for field in ("city", "town", "village", "municipality")
            if result.get(field) and str(result[field]).strip()
        ),
        None,
    )
    state = next(
        (
            str(result[field]).strip()
            for field in ("state_code", "state")
            if result.get(field) and str(result[field]).strip()
        ),
        None,
    )
    return ZipLocation(
        postcode=result_postcode,
        country_code="US",
        latitude=float(latitude),
        longitude=float(longitude),
        locality=locality,
        state=state,
    )


def lookup_us_postcode(
    postcode: str,
    client: httpx.Client | None = None,
) -> ZipLocation:
    """Resolve an exact U.S. postcode or raise a sanitized controller error."""
    requested_postcode = postcode.strip()
    if not requested_postcode:
        raise ZipLookupNotFoundError("The requested ZIP code could not be resolved.")

    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeoapifyConfigurationError(
            "The ZIP lookup provider is not configured."
        )

    request_client = client or httpx.Client()
    try:
        response = request_client.get(
            GEOAPIFY_GEOCODE_URL,
            params={
                "postcode": requested_postcode,
                "type": "postcode",
                "filter": "countrycode:us",
                "format": "json",
                "apiKey": api_key,
            },
            timeout=GEOAPIFY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError):
        raise GeoapifyProviderError(
            "The ZIP lookup provider request failed."
        ) from None
    finally:
        if client is None:
            request_client.close()

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise GeoapifyProviderError(
            "The ZIP lookup provider returned an invalid response."
        )

    for result in payload["results"]:
        location = _location_from_result(result, requested_postcode)
        if location is not None:
            return location

    raise ZipLookupNotFoundError("The requested ZIP code could not be resolved.")
