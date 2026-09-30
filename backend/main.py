from fastapi import Cookie, FastAPI, HTTPException, Response

from account_controller import (
    SESSION_COOKIE_NAME,
    InvalidCredentialsError,
    current_account,
    login,
    logout,
    register_account,
)
from config import is_geoapify_key_configured

from database_controller import (
    UnknownTripError,
    UnknownUserError,
    UnknownBookingError,
    DuplicateUsernameError,
    cancel_booking,
    create_booking,
    delete_booking,
    list_booking_history,
    list_users,
)
from database import initialize_database
from hotel_search_controller import search_live_hotels
from models import (
    Booking,
    BookingCreate,
    BookingHistoryItem,
    AccountCreate,
    CitySearchResponse,
    LoginRequest,
    LiveHotelSearchResponse,
    User,
    UserAccount,
    ZipLocation,
)
from search_controller import search_city
from zip_controller import (
    GeoapifyConfigurationError,
    GeoapifyProviderError,
    ZipLookupNotFoundError,
    lookup_us_postcode,
)

initialize_database()

app = FastAPI(title="Expedia Lite API")


@app.get("/api/health")
@app.get("/health")
def health_check() -> dict[str, str]:
    """Report API availability and safe configuration status."""
    key_status = (
        "key is configured"
        if is_geoapify_key_configured()
        else "key is not configured"
    )
    return {"status": "ok", "geoapify_api_key": key_status}


def _validate_postcode(postcode: str) -> None:
    if (
        len(postcode) != 5
        or not postcode.isascii()
        or not postcode.isdigit()
    ):
        raise HTTPException(
            status_code=400,
            detail="Enter a ZIP code using exactly 5 numeric digits.",
        )


@app.get(
    "/api/demo/zip-location",
    response_model=ZipLocation,
    response_model_exclude_none=True,
)
def get_demo_zip_location(postcode: str = "") -> ZipLocation:
    """Resolve a five-digit U.S. ZIP without exposing provider credentials."""
    _validate_postcode(postcode)

    try:
        return lookup_us_postcode(postcode)
    except GeoapifyConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail="The ZIP location provider is not configured.",
        ) from error
    except ZipLookupNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=f"ZIP code {postcode} could not be resolved.",
        ) from error
    except GeoapifyProviderError as error:
        raise HTTPException(
            status_code=502,
            detail="The ZIP location provider request failed.",
        ) from error


@app.get(
    "/api/live-hotels",
    response_model=LiveHotelSearchResponse,
    response_model_exclude_none=True,
)
def get_live_hotels(postcode: str = "") -> LiveHotelSearchResponse:
    """Return Geoapify hotels within 5 km of an exact U.S. ZIP center."""
    _validate_postcode(postcode)

    try:
        return search_live_hotels(postcode)
    except GeoapifyConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail="The live hotel provider is not configured.",
        ) from error
    except ZipLookupNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=f"ZIP code {postcode} could not be resolved.",
        ) from error
    except GeoapifyProviderError as error:
        raise HTTPException(
            status_code=502,
            detail="The live hotel provider request failed.",
        ) from error


@app.post("/api/accounts", response_model=UserAccount, status_code=201)
def post_account(account: AccountCreate) -> UserAccount:
    """Create a local classroom-demo account."""
    try:
        return UserAccount(
            **register_account(account.username, account.password, account.email)
        )
    except DuplicateUsernameError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/session/login", response_model=UserAccount)
def post_login(credentials: LoginRequest, response: Response) -> UserAccount:
    """Authenticate demo credentials and begin a local browser session."""
    try:
        session_id, account = login(credentials.username, credentials.password)
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="lax",
    )
    return UserAccount(**account)


@app.get("/api/session", response_model=UserAccount | None)
def get_session(
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> UserAccount | None:
    """Return the account currently signed in for this browser session."""
    account = current_account(session_id)
    return UserAccount(**account) if account is not None else None


@app.post("/api/session/logout", status_code=204)
def post_logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Response:
    """End the current local browser session."""
    logout(session_id)
    response.delete_cookie(SESSION_COOKIE_NAME)
    response.status_code = 204
    return response


@app.get("/api/stays", response_model=CitySearchResponse, response_model_exclude_none=True)
def search_stays(
    city: str,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> CitySearchResponse:
    """Run the existing city search with automatic signed-in pricing."""
    return CitySearchResponse(**search_city(session_id, city))


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
