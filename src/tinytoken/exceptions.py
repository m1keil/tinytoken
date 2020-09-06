class TinytokenException(Exception):
    """Base exception for this module"""


class RefreshTokenExpired(TinytokenException):
    """Refresh token expired exception"""
