"""SQLite-backed travel search for Expedia Lite."""

from database import connect


def search_stays_by_city(city: str) -> list[dict[str, str | int | float]]:
    """Return SQLite-backed hotel stays whose city matches the supplied city."""
    normalized_city = city.strip()
    if not normalized_city:
        return []

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                trips.trip_id,
                trips.trip_name,
                hotels.hotel_name,
                hotels.city,
                hotels.state,
                trips.check_in,
                trips.check_out,
                CAST(julianday(trips.check_out) - julianday(trips.check_in) AS INTEGER)
                    AS nights,
                hotels.nightly_rate_usd,
                hotels.nightly_rate_usd
                    * CAST(julianday(trips.check_out) - julianday(trips.check_in) AS INTEGER)
                    AS stay_price_usd
            FROM trips
            JOIN hotels ON hotels.hotel_id = trips.hotel_id
            WHERE hotels.city = ? COLLATE NOCASE
            ORDER BY trips.trip_id
            """,
            (normalized_city,),
        ).fetchall()

    return [dict(row) for row in rows]
