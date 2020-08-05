import json
import base64
import time

CLOCK_SKEW = 5


def expired(jwt: str) -> bool:
    """Checks if JWT token has expired

    Expiration checked by inspecting the "exp" field of the JWT payload.
    If "exp" key is not found, a ValueError will be raised.

    Returns True if expired, false otherwise.
    """
    if jwt.count('.') != 2:
        raise ValueError('Not valid JWT token')

    header, payload, signature = jwt.split('.')

    # python will throw padding error if padding is missing,
    # but will be totally OK with any extra padding.
    payload = base64.urlsafe_b64decode(payload + '===')
    payload = json.loads(payload)

    if 'exp' not in payload:
        raise ValueError('Token contains no "exp" key')
    exp = int(payload['exp'])
    now = int(time.time())

    return now > exp - CLOCK_SKEW * 60
