import sys
import logging
from threading import Thread
from queue import Queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Any


RESPONSE = (
    "Callback processed successfully. Page can be closed. Check terminal for results."
)

queue: Queue = Queue(maxsize=1)
logger = logging.getLogger(__name__)


class HTTPCallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # disable default access logging
        pass

    def do_GET(self) -> None:
        logger.debug(f"Incoming request: {self.requestline}")
        query = parse_qs(urlparse(self.path).query)

        code = query.get("code", [""])[0]
        state = query.get("state", [""])[0]

        queue.put((code, state))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(RESPONSE, "utf-8"))

        # Handle only the first incoming request
        sys.exit()


def start(address: str, port: int) -> int:
    httpd = HTTPServer((address, port), HTTPCallbackHandler)
    logger.info(f"Starting local httpd ({httpd.server_address[0]}:{httpd.server_port})")
    t = Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    return httpd.server_port
