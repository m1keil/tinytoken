import logging
import secrets
from hashlib import sha256
from base64 import urlsafe_b64encode
from functools import partial
from pprint import pformat
from urllib.parse import urlparse, parse_qs

import requests

# taken from: https://accounts.google.com/.well-known/openid-configuration
AUTHORIZATION_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'

logger = logging.getLogger(__name__)


def authorization(client_id, port):
    # PKCE:
    # https://tools.ietf.org/html/rfc7636#section-4.1
    # # https://tools.ietf.org/html/rfc7636#section-4.2
    code_verifier = secrets.token_urlsafe(43)
    code_challange = base64_without_padding(sha256(bytes(code_verifier, 'utf-8')).digest())

    # CSRF mitigation
    # https://tools.ietf.org/html/rfc6749#section-10.12
    state = secrets.token_urlsafe(32)
    payload = {
        'client_id': client_id,
        'redirect_uri': f'http://127.0.0.1:{port}',
        'scope': 'openid',
        'response_type': 'code',
        'state': state,
        'code_challenge_method': 'S256',
        'code_challenge': code_challange,
    }

    # TODO: dynamic version
    headers = {
        'User-Agent': 'awscreds/v0.1'
    }

    logger.debug(f'Authorization request: \n{pformat(payload)}')

    # TODO: error handle
    response = requests.get(
        AUTHORIZATION_ENDPOINT,
        params=payload,
        headers=headers,
        allow_redirects=False
    )

    response_location = response.headers['Location']
    logger.debug(f'Authorization response: {response_location}')

    # Compare request and response state
    response_state = parse_qs(urlparse(response_location).query)['state'][0]
    if response_state != state:
        raise ValueError('State mismatch between requests')

    p = partial(exchange, code_verifier=code_verifier)

    return response_location, p


def exchange(*, code_verifier, port, code, client_id):
    payload = {
        'client_id': client_id,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': f'http://127.0.0.1:{port}',
        'code_verifier': code_verifier
    }

    headers = {
        'User-Agent': 'awscreds/v0.1'
    }

    logger.debug(f'Exchange request: \n{pformat(payload)}')

    response = requests.post(
        TOKEN_ENDPOINT,
        params=payload,
        headers=headers,
        allow_redirects=False
    )

    data = response.json()

    logger.debug(f'Exchange response: \n{pformat(data)}')

    return data['id_token']


def base64_without_padding(data):
    # https://tools.ietf.org/html/rfc7636#appendix-A
    return urlsafe_b64encode(data).decode("utf-8").rstrip("=")
