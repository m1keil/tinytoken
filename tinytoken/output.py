import json
from enum import Enum, auto


class OutputFormat(Enum):
    json = auto()
    shell = auto()


def output(fmt: OutputFormat, tokens: dict) -> None:
    data = {
        'access_token': tokens['access_token'],
        'id_token': tokens['id_token']
    }

    if fmt == OutputFormat.json:
        print(json.dumps(data, indent=4))
    elif fmt == OutputFormat.shell:
        print(f"export ACCESS_TOKEN={tokens['access_token']}")
        print(f"export ID_TOKEN={tokens['id_token']}")
    else:
        raise ValueError(f'Output format {format} not implemented')
