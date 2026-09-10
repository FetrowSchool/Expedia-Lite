"""CSV-backed travel search for Expedia Lite Part 1."""

import csv
from datetime import date
from pathlib import Path

DATA_DIRECTORY = Path(__file__).parent / "data"


def _read_csv(filename: str) -> list[dict[str, str]]:
    """Read a supplied CSV while handling its UTF-8 BOM and CRLF line endings."""
    with (DATA_DIRECTORY / filename).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def search_stays_by_city(city: str) -> list[dict[str, str | int | float]]:
    """Return offered hotel stays whose hotel city matches the supplied city."""
    normalized_city = city.strip().casefold()
    if not normalized_city:
        return []

    hotels_by_id = {hotel["hotel_id"]: hotel for hotel in _read_csv("hotels.csv")}
    stays = []

    for trip in _read_csv("trips.csv"):
        hotel = hotels_by_id[trip["hotel_id"]]
        if hotel["city"].casefold() != normalized_city:
            continue

        check_in = date.fromisoformat(trip["check_in"])
        check_out = date.fromisoformat(trip["check_out"])
        nightly_rate = float(hotel["nightly_rate_usd"])
        nights = (check_out - check_in).days

        stays.append(
            {
                "trip_id": trip["trip_id"],
                "trip_name": trip["trip_name"],
                "hotel_name": hotel["hotel_name"],
                "city": hotel["city"],
                "state": hotel["state"],
                "check_in": trip["check_in"],
                "check_out": trip["check_out"],
                "nights": nights,
                "nightly_rate_usd": nightly_rate,
                "stay_price_usd": nightly_rate * nights,
            }
        )

    return stays
