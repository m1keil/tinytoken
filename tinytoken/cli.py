"""
OpenID Connect client
"""

import sys
import argparse
import logging
from queue import Empty


from . import server, oauth, user_agent, cache, jwt, utils
from .output import output, OutputFormat
from .exceptions import TinytokenException

# Time to wait for callback from user-agent
TIMEOUT = 30

logging.basicConfig(level='WARNING', format='%(message)s')
logger = logging.getLogger('tinytoken')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('--client-id', '-c', required=True, metavar='ID', help='OIDC client id')
    parser.add_argument('--discovery-uri', required=True, metavar='URI', help='OIDC discovery uri')
    parser.add_argument('--user-agent', default=user_agent.default(),
                        help='Path to web browser or any other utility that is able to determine how to open URLs')
    parser.add_argument('--redirect-uri', default='http://localhost:9999/', metavar='URI',
                        help='User-agent redirect destination. Should be on the loopback interface')
    # Temporary until I figure out how Cognito generates its state
    # parser.add_argument('--no-csrf', action='store_true', help='Disable state verification')
    parser.add_argument('--output', choices=OutputFormat.__members__, default='JSON', help='Output format')
    parser.add_argument('--skip-cache', action='store_true', help='Disable caching to disk')
    parser.add_argument('-v', action='count', default=0, help='Verbosity level. Can be specified multiple times')

    return parser.parse_args()


def sign_in(discovery_uri, client_id, redirect_uri, user_agent_cmd):
    # OpenID Discovery
    auth_endpoint, token_endpoint = oauth.discovery(discovery_uri)

    # Start server on loopback to get redirect
    server.start(*utils.parse_uri(redirect_uri))

    # Kick off authorization flow
    url, exchange = oauth.authorization(
        client_id=client_id,
        redirect_uri=redirect_uri,
        auth_endpoint=auth_endpoint,
        token_endpoint=token_endpoint,
    )

    # Execute user-agent to allow user to authenticate
    user_agent.execute(user_agent_cmd, url)

    try:
        code = server.queue.get(timeout=TIMEOUT)
    except Empty:
        raise TinytokenException(f"Timed out waiting for user's action ({TIMEOUT}s)")

    # Exchange authorization code for id token
    return exchange(code=code)


def refresh(discovery_uri, client_id, refresh_token):
    # OpenID Discovery
    auth_endpoint, token_endpoint = oauth.discovery(discovery_uri)

    tokens = oauth.refresh(
        token_endpoint=token_endpoint,
        client_id=client_id,
        refresh_token=refresh_token
    )

    return tokens


def main():
    args = parse_args()
    # Logging level
    if args.v == 1:
        logger.setLevel(logging.INFO)
    elif args.v >= 2:
        logger.setLevel(logging.DEBUG)

    if args.skip_cache:
        logger.info('Skipping cache')
        tokens = sign_in(
            discovery_uri=args.discovery_uri,
            client_id=args.client_id,
            redirect_uri=args.redirect_uri,
            user_agent_cmd=args.user_agent
        )
    elif cache.exists(args.client_id):
        logger.info('Retrieving tokens from cache')
        tokens = cache.retrieve(args.client_id)
    else:
        logger.info('Token is not cached')
        tokens = sign_in(
            discovery_uri=args.discovery_uri,
            client_id=args.client_id,
            redirect_uri=args.redirect_uri,
            user_agent_cmd=args.user_agent
        )

    expired = jwt.expired(tokens['access_token'])

    if expired:
        logger.info('Access token expired, attempting to refresh')
        try:
            tokens = refresh(
                discovery_uri=args.discovery_uri,
                client_id=args.client_id,
                refresh_token=tokens['refresh_token']
            )
        except TinytokenException:
            logger.info('Refresh token expired, attempting to authenticate')
            tokens = sign_in(
                discovery_uri=args.discovery_uri,
                client_id=args.client_id,
                redirect_uri=args.redirect_uri,
                user_agent_cmd=args.user_agent
            )

    if not args.skip_cache or expired:
        logger.info('Caching tokens')
        cache.store(
            client_id=args.client_id,
            access_token=tokens['access_token'],
            id_token=tokens['id_token'],
            refresh_token=tokens.get('refresh_token')
        )

    # Output
    output(OutputFormat[args.output], tokens)


def entry_point():
    try:
        return main()
    except TinytokenException as e:
        print(f'Error: {e}')
        sys.exit(1)
