import json
import logging

from . import BASE
from .oauth import Tokens

logger = logging.getLogger(__name__)


def store(client_id: str, tokens: Tokens) -> None:
    cache = BASE / f"{client_id}_cache.json"

    # Store tokens
    cache.touch(0o600, exist_ok=True)
    with cache.open("w") as fh:
        json.dump(tokens._asdict(), fh)


def exists(client_id: str) -> bool:
    tokens = BASE / f"{client_id}_cache.json"
    return tokens.exists()


def retrieve(client_id: str) -> Tokens:
    cache = BASE / f"{client_id}_cache.json"

    with cache.open() as fh:
        data = json.load(fh)

    return Tokens(**data)
