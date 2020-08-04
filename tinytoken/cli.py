import sys
import argparse
import logging
from queue import Empty


from . import server, oauth, user_agent, utils

# Time to wait for callback from user-agent
TIMEOUT = 30

logging.basicConfig(level='WARNING', format='%(message)s')
logger = logging.getLogger('tinytoken')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.description = 'OpenID Connect client'
    parser.add_argument('-v', action='count', default=0, help='verbosity level')
    parser.add_argument('--client', '-c', dest='client_id', required=True, help='OAuth 2.0 client id')
    parser.add_argument('--user-agent', default='/usr/bin/open -a "Google Chrome"',
                        help='Custom user-agent execution command')
    parser.add_argument('--discovery', required=True, help='OpenID discovery url')
    parser.add_argument('--redirect-uri', default='http://localhost:9999/', help='Local endpoint to listen on')
    # Temporary until I figure out how Cognito generates its state
    # parser.add_argument('--no-csrf', action='store_true', help='Disable state verification')
    parser.add_argument('--output', choices=['json'], default='json', help='Output format')

    return parser.parse_args()


def main():
    args = parse_args()
    # Logging level
    if args.v == 1:
        logger.setLevel(logging.INFO)
    elif args.v >= 2:
        logger.setLevel(logging.DEBUG)

    # OpenID Discovery
    auth_endpoint, token_endpoint = oauth.discovery(args.discovery)

    # Start server on loopback to get redirect
    server.start(*utils.parse_uri(args.redirect_uri))

    # Kick off authorization flow
    url, exchange = oauth.authorization(
        client_id=args.client_id,
        redirect_uri=args.redirect_uri,
        auth_endpoint=auth_endpoint,
        token_endpoint=token_endpoint,
    )

    # Execute user-agent to allow user to authenticate
    user_agent.execute(args.user_agent, url)

    try:
        code = server.queue.get(timeout=TIMEOUT)
    except Empty:
        logger.error(f"Timed out waiting for user's action ({TIMEOUT}s)")
        sys.exit(1)

    # Exchange authorization code for id token
    tokens = exchange(code=code)

    # Output
    print(utils.output(args.output, tokens))
