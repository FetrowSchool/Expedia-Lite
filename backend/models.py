"""Application data models for Expedia Lite."""

from pydantic import BaseModel, field_validator


class Hotel(BaseModel):
    """A hotel stored in SQLite."""

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: float


class Trip(BaseModel):
    """An offered stay related to a hotel by hotel_id."""

    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: str
    check_out: str


class User(BaseModel):
    """A traveler who can create bookings."""

    user_id: str
    display_name: str


class AccountCreate(BaseModel):
    """The fields accepted when creating a local demo account."""

    username: str
    password: str
    email: str | None = None

    @field_validator("username", "password")
    @classmethod
    def reject_blank_account_fields(cls, value: str) -> str:
        """Trim required account fields and reject blank values."""
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("Value must not be blank.")
        return normalized_value

    @field_validator("email")
    @classmethod
    def normalize_optional_email(cls, value: str | None) -> str | None:
        """Store a missing or blank email as null."""
        if value is None:
            return None
        return value.strip() or None


class UserAccount(User):
    """A stored local account; passwords are never included in API responses."""

    username: str
    email: str | None = None


class LoginRequest(BaseModel):
    """Local demo credentials submitted for login."""

    username: str
    password: str


class SearchHistory(BaseModel):
    """One city search and returned-result snapshot associated with a user."""

    search_history_id: str
    user_id: str
    search_query: str
    normalized_query: str
    searched_at: str
    results: list[dict[str, str | int | float]]
    search_count: int
    price_multiplier: float


class BookingCreate(BaseModel):
    """The user and trip relationships required for a new booking."""

    user_id: str
    trip_id: str

    @field_validator("user_id", "trip_id")
    @classmethod
    def reject_blank_ids(cls, value: str) -> str:
        """Trim IDs and reject empty values."""
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("ID must not be blank.")
        return normalized_value


class Booking(BaseModel):
    """A stored booking related to one user and one trip."""

    booking_id: str
    user_id: str
    trip_id: str
    booked_on: str
    status: str


class Stay(BaseModel):
    """A trip joined to its hotel for city-search results."""

    trip_id: str
    trip_name: str
    hotel_name: str
    city: str
    state: str
    check_in: str
    check_out: str
    nights: int
    nightly_rate_usd: float
    stay_price_usd: float


class CitySearchResponse(BaseModel):
    """City-search results returned to the Vue view."""

    city: str
    search_count: int | None = None
    price_increased: bool | None = None
    time_zone: str | None = None
    stays: list[Stay]


class BookingHistoryItem(Booking):
    """A booking joined to its user, trip, and hotel display data."""

    display_name: str
    trip_name: str
    hotel_name: str
    city: str
    state: str
