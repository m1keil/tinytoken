import logging
import secrets
from hashlib import sha256
from functools import partial
from pprint import pformat

from .utils import base64_without_padding
from .exceptions import TinytokenException

import requests

logger = logging.getLogger(__name__)


def authorization(*, auth_endpoint, token_endpoint, client_id, redirect_uri):
    # PKCE:
    # https://tools.ietf.org/html/rfc7636#section-4.1
    # # https://tools.ietf.org/html/rfc7636#section-4.2
    code_verifier = secrets.token_urlsafe(43)
    code_challange = base64_without_padding(sha256(bytes(code_verifier, 'utf-8')).digest())

    # CSRF mitigation
    # state = secrets.token_urlsafe(32)
    payload = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid',
        'response_type': 'code',
        # 'state': state,
        'code_challenge_method': 'S256',
        'code_challenge': code_challange,
    }

    logger.debug(f'Authorization request: \n{pformat(payload)}')

    try:
        response = requests.get(
            auth_endpoint,
            params=payload,
            allow_redirects=False
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise TinytokenException(f'Authorization request failed: {e}')

    response_location = response.headers['Location']
    logger.debug(f'Authorization response: {response_location}')

    # Compare request and response state. (CSRF mitifation)
    # https://tools.ietf.org/html/rfc6749#section-10.12
    # if state_verification:
    #     # TODO: what if state isn't there (e.g wrong redirect_uri)
    #     response_state = parse_qs(urlparse(response_location).query)['state'][0]
    #     if response_state != state:
    #         logger.error(f'Expected state: {state}, got: {response_state}')
    #         raise ValueError('State mismatch between requests')

    p = partial(exchange, code_verifier=code_verifier, token_endpoint=token_endpoint, redirect_uri=redirect_uri, client_id=client_id)

    return response_location, p


def exchange(*, token_endpoint, code_verifier, redirect_uri, client_id, code):
    payload = {
        'client_id': client_id,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }

    logger.debug(f'Exchange request: \n{pformat(payload)}')

    try:
        response = requests.post(
            token_endpoint,
            params=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            allow_redirects=False
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise TinytokenException(f'Code to token exchange failed unexpectedly: {e}')

    logger.debug(f'Exchange response: \n{pformat(response.content.decode("utf-8"))}')

    return response.json()


def refresh(*, token_endpoint, client_id, refresh_token):
    payload = {
        'client_id': client_id,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    logger.debug(f'Refresh request: \n{pformat(payload)}')

    try:
        response = requests.post(
            token_endpoint,
            params=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            allow_redirects=False
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise TinytokenException(f'Token refresh failed unexpectedly: {e}')

    logger.debug(f'Refresh response: \n{pformat(response.content.decode("utf-8"))}')

    return response.json()


def discovery(url):
    """Returns authorization and token endpoint urls"""
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise TinytokenException(f'Fetching discovery info failed: {e}')

    data = resp.json()

    return data['authorization_endpoint'], data['token_endpoint']
