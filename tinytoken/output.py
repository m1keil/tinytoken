import json
from enum import Enum


class OutputFormat(Enum):
    JSON = 1


def output(fmt: OutputFormat, tokens: dict) -> None:
    data = {
        'access_token': tokens['access_token'],
        'id_token': tokens['id_token']
    }

    if fmt == OutputFormat.JSON:
        return print(json.dumps(data, indent=4))

    raise ValueError(f'Output format {format} not implemented')
