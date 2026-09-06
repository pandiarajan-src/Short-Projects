"""Login / auth entry points for the API."""

from token_utils import issue_token, verify_token


def login(user_id, password):
    if not password:
        raise ValueError("password required")
    return issue_token(user_id)


def require_auth(token):
    user_id = verify_token(token)
    if user_id is None:
        raise PermissionError("invalid or expired token")
    return user_id
