"""Existing city-search orchestration with automatic signed-in pricing."""

from datetime import datetime
from pathlib import Path

from account_controller import current_account
from database_controller import search_stays_by_city, update_search_history_results
from pricing import personalized_price, price_multiplier
from urgency import APPLICATION_TIME_ZONE_NAME, record_and_count_daily_searches


def search_city(
    session_id: str | None,
    city: str,
    now: datetime | None = None,
    database_path: Path | None = None,
) -> dict[str, object]:
    """Run the existing city search and personalize it for a signed-in user."""
    submitted_query = city.strip()
    base_stays = search_stays_by_city(submitted_query, database_path)
    account = current_account(session_id)

    if account is None:
        return {
            "city": submitted_query,
            "stays": base_stays,
        }

    search_count, _normalized_query, history_id = record_and_count_daily_searches(
        str(account["user_id"]), submitted_query, now, database_path
    )
    multiplier = price_multiplier(search_count)
    priced_stays = [
        {
            **stay,
            "nightly_rate_usd": personalized_price(
                float(stay["nightly_rate_usd"]), search_count
            ),
            "stay_price_usd": personalized_price(
                float(stay["stay_price_usd"]), search_count
            ),
        }
        for stay in base_stays
    ]
    update_search_history_results(
        history_id, priced_stays, search_count, multiplier, database_path
    )
    return {
        "city": submitted_query,
        "search_count": search_count,
        "price_increased": multiplier > 1.0,
        "time_zone": APPLICATION_TIME_ZONE_NAME,
        "stays": priced_stays,
    }
