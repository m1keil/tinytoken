import platform
import shlex
from subprocess import run, CalledProcessError
from pathlib import Path

from .exceptions import TinytokenException


def execute(command: str, url: str) -> None:
    cmd = shlex.split(command)
    cmd.append(url)

    try:
        run(cmd, capture_output=True, check=True)
    except CalledProcessError as e:
        raise TinytokenException(
            f"Attempt to start user-agent failed with return code {e.returncode}"
        )
    except FileNotFoundError as e:
        raise TinytokenException(f"User agent not found: {e}")


def default() -> str:
    os = platform.system()

    if os == "Darwin":
        target = Path("/usr/bin/open")
    elif os == "Linux":
        target = Path("/usr/bin/xdg-open")
    else:
        raise TinytokenException(
            f"Unable to get default handler for {os}. Specify --user-agent manually."
        )

    if not target.exists():
        raise TinytokenException(
            f"{os} OS detected but {target} not found. Specify --user-agent manually."
        )

    return str(target)
