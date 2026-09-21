"""Demo account creation, authentication, and local session tracking."""

from secrets import token_urlsafe

from database_controller import (
    DuplicateUsernameError,
    authenticate_account,
    create_account,
    get_account_by_id,
)

SESSION_COOKIE_NAME = "expedia_lite_session"

_sessions: dict[str, str] = {}


class InvalidCredentialsError(ValueError):
    """Raised when a demo username and password do not match."""


def register_account(
    username: str,
    password: str,
    email: str | None = None,
) -> dict[str, str | None]:
    """Create an account through the database controller."""
    return create_account(username, username, password, email)


def login(username: str, password: str) -> tuple[str, dict[str, str | None]]:
    """Authenticate demo credentials and create a browser session."""
    account = authenticate_account(username, password)
    if account is None:
        raise InvalidCredentialsError("Username or password is incorrect.")

    session_id = token_urlsafe(32)
    _sessions[session_id] = str(account["user_id"])
    return session_id, account


def current_account(session_id: str | None) -> dict[str, str | None] | None:
    """Return the account associated with a local session cookie."""
    if not session_id:
        return None
    user_id = _sessions.get(session_id)
    if user_id is None:
        return None
    return get_account_by_id(user_id)


def logout(session_id: str | None) -> None:
    """Remove a local session if it exists."""
    if session_id:
        _sessions.pop(session_id, None)
