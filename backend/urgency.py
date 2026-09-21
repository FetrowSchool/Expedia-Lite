"""Daily search-count measurement for personalized pricing."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from database_controller import count_search_history, record_search_history

APPLICATION_TIME_ZONE_NAME = "America/New_York"
APPLICATION_TIME_ZONE = ZoneInfo(APPLICATION_TIME_ZONE_NAME)


def record_and_count_daily_searches(
    user_id: str,
    search_query: str,
    now: datetime | None = None,
    database_path: Path | None = None,
) -> tuple[int, str, str]:
    """Record the current search and return its same-day count, including itself."""
    current_time = now or datetime.now(APPLICATION_TIME_ZONE)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=APPLICATION_TIME_ZONE)
    else:
        current_time = current_time.astimezone(APPLICATION_TIME_ZONE)

    normalized_query = search_query.strip().casefold()
    searched_at_utc = current_time.astimezone(timezone.utc).isoformat(timespec="seconds")
    history = record_search_history(user_id, search_query, searched_at_utc, database_path)

    day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    next_day_start = day_start + timedelta(days=1)
    count = count_search_history(
        user_id,
        normalized_query,
        day_start.astimezone(timezone.utc).isoformat(timespec="seconds"),
        next_day_start.astimezone(timezone.utc).isoformat(timespec="seconds"),
        database_path,
    )
    return count, normalized_query, history["search_history_id"]
