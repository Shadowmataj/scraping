""""Custom exceptions for auth errors."""


class AuthError(Exception):
    """Base class for auth errors."""

    pass


class TokenExpiredError(AuthError):
    """It raises when the token is expired."""

    pass


class InvalidCredentials(AuthError):
    pass
