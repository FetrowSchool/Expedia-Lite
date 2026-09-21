from fastapi import Cookie, FastAPI, HTTPException, Response

from account_controller import (
    SESSION_COOKIE_NAME,
    InvalidCredentialsError,
    current_account,
    login,
    logout,
    register_account,
)

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
from models import (
    Booking,
    BookingCreate,
    BookingHistoryItem,
    AccountCreate,
    CitySearchResponse,
    LoginRequest,
    User,
    UserAccount,
)
from search_controller import search_city

initialize_database()

app = FastAPI(title="Expedia Lite API")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API is available."""
    return {"status": "ok"}


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
