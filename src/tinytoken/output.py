import json
from enum import Enum, auto

from . import profile, oauth


class OutputFormat(Enum):
    json = auto()
    shell = auto()
    config = auto()


def output(fmt: OutputFormat, tokens: oauth.Tokens, **kwargs: str) -> None:
    if fmt == OutputFormat.json:
        print(json.dumps(tokens._asdict(), indent=4))
    elif fmt == OutputFormat.shell:
        print(f"export ACCESS_TOKEN={tokens.access_token}")
        print(f"export ID_TOKEN={tokens.id_token}")
    elif fmt == OutputFormat.config:
        profile.set_credentials(profile_name=kwargs["profile"], credentials=tokens)
    else:
        raise ValueError(f"Output format {format} not implemented")
