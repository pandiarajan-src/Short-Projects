"""JWT-style token helpers used at login and on protected API calls."""

import time

_FAKE_VALID_TOKENS = {}


def issue_token(user_id):
    token = f"tok_{user_id}_{int(time.time())}"
    _FAKE_VALID_TOKENS[token] = user_id
    return token


def verify_token(token):
    """Return the user_id for a token, or None if it's invalid/expired."""
    return _FAKE_VALID_TOKENS.get(token)
