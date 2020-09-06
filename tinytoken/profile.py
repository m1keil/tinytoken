from typing import Dict, Optional, Any, NamedTuple
import logging
from configparser import ConfigParser
from pathlib import Path

from . import BASE
from .exceptions import TinytokenException
from .oauth import Tokens

logger = logging.getLogger(__name__)


class Profile(NamedTuple):
    client_id: str
    discovery_uri: str
    user_agent: Optional[str] = None
    redirect_uri: Optional[str] = None
    output: Optional[str] = None
    skip_cache: Optional[bool] = None


def _load(path: Path, section: str) -> Dict[str, Any]:
    config = ConfigParser()
    # if file not found, this will raise FileNotFound
    with path.open() as fh:
        config.read_file(fh)

    if section not in config:
        raise ValueError(f'config section "{section}" not found')

    return dict(config[section].items())


def _save(path: Path, section: str, data: Dict[str, str]) -> None:
    config = ConfigParser()

    try:
        with path.open() as fh:
            config.read_file(fh)
    except FileNotFoundError:
        path.touch(0o600)

    if section not in config:
        config[section] = data
    else:
        config[section].update(data)

    with path.open("w") as fh:
        config.write(fh)


def get_credentails(profile_name: str) -> Tokens:
    path = BASE / "credentials"
    try:
        data = _load(path, profile_name)
    except FileNotFoundError:
        raise TinytokenException(f'Profile file "{path}" not found.')
    except ValueError:
        raise TinytokenException(f'Profile "{profile_name}" not found.')

    try:
        credentials = Tokens(**data)
    except TypeError:
        raise TinytokenException(
            f'Unable to load "{profile_name}" profile from {path}. Check for typos.'
        )

    return credentials


def set_credentials(profile_name, credentials: Tokens) -> None:
    path = BASE / "credentials"
    _save(path, profile_name, credentials._asdict())


def get_profile(profile_name) -> Profile:
    path = BASE / "config"
    try:
        data = _load(path, profile_name)
    except FileNotFoundError:
        raise TinytokenException(f'Profile file "{path}" not found.')
    except ValueError:
        raise TinytokenException(f'Profile "{profile_name}" not found.')

    try:
        profile = Profile(**data)
    except TypeError:
        raise TinytokenException(
            f"Unable to load profile ({path}). Check file for typos."
        )

    return profile
