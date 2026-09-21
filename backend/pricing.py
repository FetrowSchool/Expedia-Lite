"""Non-compounding personalized price calculation."""

PRICE_INCREASE_MULTIPLIER = 1.20
PRICE_INCREASE_SEARCH_NUMBER = 2


def personalized_price(base_price: float, search_count: int) -> float:
    """Return base price for search 1 and 120% of base thereafter."""
    multiplier = (
        PRICE_INCREASE_MULTIPLIER
        if search_count >= PRICE_INCREASE_SEARCH_NUMBER
        else 1.0
    )
    return round(base_price * multiplier, 2)


def price_multiplier(search_count: int) -> float:
    """Return the one-time multiplier for a daily same-query search count."""
    return (
        PRICE_INCREASE_MULTIPLIER
        if search_count >= PRICE_INCREASE_SEARCH_NUMBER
        else 1.0
    )
