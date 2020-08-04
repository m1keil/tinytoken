import logging
import secrets
from hashlib import sha256
from base64 import urlsafe_b64encode
from functools import partial
from pprint import pformat
from urllib.parse import urlparse, parse_qs

import requests

logger = logging.getLogger(__name__)
headers = {'User-Agent': 'awscreds/v0.1'}


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
            headers=headers,
            allow_redirects=False
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error('Authorization request failed', e)
        raise

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
        logger.error(f'Code to token exchange failed unexpectedly: {e}')
        raise

    logger.debug(f'Exchange response: \n{pformat(response.content.decode("utf-8"))}')

    try:
        data = response.json()
    except ValueError:
        logger.error('Unexpected data format from token endpoint')
        raise

    return data


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
        logger.error(f'Token refresh failed unexpectedly: {e}')
        raise

    logger.debug(f'Refresh response: \n{pformat(response.content.decode("utf-8"))}')

    try:
        data = response.json()
    except ValueError:
        logger.error('Unexpected data format from token endpoint')
        raise

    return data


def discovery(url):
    """Returns authorization and token endpoint urls"""
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        logger.error('Error while attempting to discover OpenID endpoints')
        raise

    try:
        data = resp.json()
    except ValueError:
        logger.error('Unexpected data format from discovery endpoint')
        raise

    return data['authorization_endpoint'], data['token_endpoint']


def base64_without_padding(data):
    # https://tools.ietf.org/html/rfc7636#appendix-A
    return urlsafe_b64encode(data).decode("utf-8").rstrip("=")
