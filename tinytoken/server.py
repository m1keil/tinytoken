import sys
import logging
from threading import Thread
from queue import Queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Any


queue = Queue(maxsize=1)
logger = logging.getLogger(__name__)


class HTTPCallbackHandler(BaseHTTPRequestHandler):
    state = None
    code = None

    def log_message(self, format: str, *args: Any) -> None:
        # disable default access logging
        pass

    def do_GET(self) -> None:
        code = state = None

        logger.debug(f'Incoming request: {self.requestline}')
        query = parse_qs(urlparse(self.path).query)

        if 'code' in query:
            code = query.get('code')[0]

        if 'state' in query:
            state = query.get('state')[0]

        queue.put((code, state))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes('Processed successfully. Page can be closed', 'utf-8'))

        # Handle only the first incoming request
        sys.exit()


def start(address: str, port: int) -> int:
    handler = HTTPCallbackHandler
    handler.test = 3
    httpd = HTTPServer((address, port), handler)
    logger.info(f'Starting local httpd ({httpd.server_address[0]}:{httpd.server_port})')
    t = Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    return httpd.server_port
