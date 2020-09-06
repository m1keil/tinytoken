from typing import Tuple, NamedTuple, Optional
import logging
import secrets
from hashlib import sha256
from pprint import pformat

from .utils import base64_without_padding
from .exceptions import TinytokenException, RefreshTokenExpired

import requests
from requests import Request

logger = logging.getLogger(__name__)


class Tokens(NamedTuple):
    access_token: str
    id_token: str
    refresh_token: Optional[str] = None


def authorization(*, auth_endpoint, client_id, redirect_uri) -> Tuple[str, str, str]:
    # PKCE:
    # https://tools.ietf.org/html/rfc7636#section-4.1
    # https://tools.ietf.org/html/rfc7636#section-4.2
    code_verifier = secrets.token_urlsafe(43)
    code_challange = base64_without_padding(
        sha256(bytes(code_verifier, "utf-8")).digest()
    )

    # CSRF mitigation
    state = secrets.token_urlsafe(32)

    payload = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid",
        "response_type": "code",
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": code_challange,
    }

    logger.debug(f"Authorization request: \n{pformat(payload)}")

    request = Request("GET", auth_endpoint, params=payload).prepare()
    if request.url is None:
        raise ValueError(f"Unable to get url for {auth_endpoint}")

    return request.url, code_verifier, state


def exchange(
    *,
    token_endpoint: str,
    code_verifier: str,
    redirect_uri: str,
    client_id: str,
    code: str,
    request_state: str,
    response_state: str,
) -> Tokens:
    # Compare request and response state. (CSRF mitigation)
    # https://tools.ietf.org/html/rfc6749#section-10.12
    if request_state != response_state:
        raise ValueError("CSRF check failed!")

    payload = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    logger.debug(f"Exchange request: \n{pformat(payload)}")

    try:
        response = requests.post(
            token_endpoint,
            params=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=False,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise TinytokenException(f"Code to token exchange failed unexpectedly: {e}")

    logger.debug(f'Exchange response: \n{pformat(response.content.decode("utf-8"))}')

    try:
        resp = response.json()
        access_token = resp["access_token"]
        id_token = resp["id_token"]
        refresh_token = resp["refresh_token"]
    except KeyError:
        raise TinytokenException("Unexpected response while exchanging code for tokens")
    return Tokens(
        access_token=access_token, refresh_token=refresh_token, id_token=id_token
    )


def refresh(*, token_endpoint: str, client_id: str, refresh_token: str) -> Tokens:
    payload = {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    logger.debug(f"Refresh request: \n{pformat(payload)}")

    try:
        response = requests.post(
            token_endpoint,
            params=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=False,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RefreshTokenExpired()

    logger.debug(f'Refresh response: \n{pformat(response.content.decode("utf-8"))}')

    try:
        resp = response.json()
        access_token = resp["access_token"]
        id_token = resp["id_token"]
    except KeyError:
        raise TinytokenException("Unexpected response while exchanging code for tokens")
    return Tokens(access_token=access_token, id_token=id_token)


def discovery(url: str) -> Tuple[str, str]:
    """Returns authorization and token endpoint urls"""
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise TinytokenException(f"Fetching discovery info failed: {e}")

    data = resp.json()

    return data["authorization_endpoint"], data["token_endpoint"]
