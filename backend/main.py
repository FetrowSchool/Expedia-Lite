from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, field_validator

from booking_data import (
    UnknownTripError,
    UnknownUserError,
    UnknownBookingError,
    cancel_booking,
    create_booking,
    delete_booking,
    list_booking_history,
    list_users,
)
from database import initialize_database
from travel_data import search_stays_by_city

initialize_database()

app = FastAPI(title="Expedia Lite API")


class Stay(BaseModel):
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
    city: str
    stays: list[Stay]


class User(BaseModel):
    user_id: str
    display_name: str


class BookingCreate(BaseModel):
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
    booking_id: str
    user_id: str
    trip_id: str
    booked_on: str
    status: str


class BookingHistoryItem(Booking):
    display_name: str
    trip_name: str
    hotel_name: str
    city: str
    state: str


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API is available."""
    return {"status": "ok"}


@app.get("/api/stays", response_model=CitySearchResponse)
def search_stays(city: str) -> CitySearchResponse:
    """Find offered hotel stays by city, ignoring capitalization and outer whitespace."""
    return CitySearchResponse(city=city.strip(), stays=search_stays_by_city(city))


@app.get("/api/users", response_model=list[User])
def get_users() -> list[User]:
    """List the seeded travelers available for simulated bookings."""
    return [User(**user) for user in list_users()]


@app.post("/api/bookings", response_model=Booking, status_code=201)
def post_booking(booking: BookingCreate) -> Booking:
    """Create a confirmed booking for an existing user and trip."""
    try:
        return Booking(**create_booking(booking.user_id, booking.trip_id))
    except (UnknownUserError, UnknownTripError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/bookings", response_model=list[BookingHistoryItem])
def get_booking_history() -> list[BookingHistoryItem]:
    """List bookings with related traveler, trip, and hotel information."""
    return [BookingHistoryItem(**booking) for booking in list_booking_history()]


@app.patch("/api/bookings/{booking_id}/cancel", response_model=Booking)
def patch_booking_cancel(booking_id: str) -> Booking:
    """Mark an existing booking as cancelled without deleting it."""
    normalized_booking_id = booking_id.strip()
    if not normalized_booking_id:
        raise HTTPException(status_code=400, detail="Booking ID must not be blank.")

    try:
        return Booking(**cancel_booking(normalized_booking_id))
    except UnknownBookingError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.delete("/api/bookings/{booking_id}", status_code=204)
def remove_booking(booking_id: str) -> Response:
    """Delete an existing booking without deleting related records."""
    normalized_booking_id = booking_id.strip()
    if not normalized_booking_id:
        raise HTTPException(status_code=400, detail="Booking ID must not be blank.")

    try:
        delete_booking(normalized_booking_id)
    except UnknownBookingError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return Response(status_code=204)
