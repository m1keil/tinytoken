import json
from urllib.parse import urlparse


def parse_uri(uri):
    uri_parts = urlparse(uri)

    hostname = uri_parts.hostname
    port = uri_parts.port
    if not hostname:
        raise ValueError('Invalid hostname')
    if not uri_parts.port:
        port = 80

    return hostname, port


def output(format, tokens):
    if format == 'json':
        return json.dumps(tokens, indent=2)
    raise ValueError(f'Output format {format} not implemented ')
