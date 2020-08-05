import json
import logging
from pathlib import Path

BASE = Path('~/.tinytoken').expanduser()

logger = logging.getLogger(__name__)


def store(client_id, access_token, id_token, refresh_token=None):
    # Create base dir if doesn't exists
    if not BASE.exists():
        logger.debug(f"{BASE} doesn't exists, creating..")
        BASE.mkdir(0o700)

    refresh = BASE / f'{client_id}_refresh.json'
    tokens = BASE / f'{client_id}_tokens.json'

    # Store tokens
    tokens.touch(0o600, exist_ok=True)
    with tokens.open('w') as fh:
        data = {
            'access_token': access_token,
            'id_token': id_token
        }
        json.dump(data, fh)

    # Store refresh token if provided
    if refresh_token:
        refresh.touch(0o600, exist_ok=True)
        with refresh.open('w', 0o600) as fh:
            data = {
                'refresh_token': refresh_token,
            }
            json.dump(data, fh)


def exists(client_id):
    tokens = BASE / f'{client_id}_tokens.json'
    return tokens.exists()


def retrieve(client_id):
    refresh = BASE / f'{client_id}_refresh.json'
    tokens = BASE / f'{client_id}_tokens.json'

    output = {}
    with tokens.open() as fh:
        data = json.load(fh)
    output.update(data)

    with refresh.open() as fh:
        data = json.load(fh)
    output.update(data)

    return output
