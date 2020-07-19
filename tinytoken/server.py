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
    def log_message(self, format: str, *args: Any) -> None:
        # disable default access logging
        pass

    def do_GET(self):
        logger.debug(f'Incoming request: {self.requestline}')
        query = parse_qs(urlparse(self.path).query)
        queue.put(query['code'][0])
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes('Processed successfully. Page can be closed', 'utf-8'))

        # Handle only the first incoming request
        sys.exit()


def start() -> int:
    httpd = HTTPServer(('127.0.0.1', 0), HTTPCallbackHandler)
    logger.info(f'Starting local httpd ({httpd.server_address[0]}:{httpd.server_port})')
    t = Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    return httpd.server_port
