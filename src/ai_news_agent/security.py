import secrets

from flask import abort, session


ACTION_TOKEN_KEY = "action_token"


def get_action_token() -> str:
    token = session.get(ACTION_TOKEN_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[ACTION_TOKEN_KEY] = token
    return token


def require_action_token(form_token: str | None) -> None:
    if not form_token or form_token != session.get(ACTION_TOKEN_KEY):
        abort(403)


def parse_int(value: str | None, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))

