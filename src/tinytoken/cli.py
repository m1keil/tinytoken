"""
OpenID Connect client
"""

import sys
import argparse
import logging
from queue import Empty

from . import server, oauth, user_agent, cache, jwt, utils, profile, BASE
from . import __version__
from .oauth import Tokens
from .output import output, OutputFormat
from .exceptions import TinytokenException, RefreshTokenExpired

# Time to wait for callback from user-agent
TIMEOUT = 30

logging.basicConfig(level="WARNING", format="%(levelname)s: %(message)s")
logger = logging.getLogger("tinytoken")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__,
        add_help=False,  # defer help
    )
    parser.add_argument("--profile", "-p", help="Saved profile name", metavar="NAME")

    # Partially parse the arguments to get profile first
    args, rest = parser.parse_known_args()

    parser.add_argument("--client-id", "-c", metavar="ID", help="OIDC client id")
    parser.add_argument("--discovery-uri", metavar="URI", help="OIDC discovery uri")
    parser.add_argument(
        "--user-agent",
        default=user_agent.default(),
        metavar="PATH",
        help="Full path of a web browser or any other utility that is able to handle URLs",
    )
    parser.add_argument(
        "--redirect-uri",
        default="http://localhost:9999/",
        metavar="URI",
        help="User-agent redirect destination. Should be on the loopback interface",
    )
    parser.add_argument(
        "--output",
        choices=OutputFormat.__members__,
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--skip-cache", action="store_true", help="Skip reading or writing from cache"
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        help="Output verbosity level. Can be specified multiple times",
    )
    parser.add_argument(
        "--version", action="version", version=f"tinytoken {__version__}"
    )
    parser.add_argument(
        "--help", "-h", action="store_true", help="Display this message"
    )

    if args.profile:
        p = profile.get_profile(args.profile)._asdict()
        profile_config = {k: v for k, v in p.items() if v is not None}
        parser.set_defaults(**profile_config)

    # parser the rest of the arguments
    args = parser.parse_args()

    # Add help back
    if args.help:
        parser.print_help()
        parser.exit(0)

    # Manually handle required arguments
    if args.client_id is None or args.discovery_uri is None:
        raise TinytokenException(
            "The following arguments are required: --client-id/-c, --discovery-uri"
        )

    if OutputFormat[args.output] == OutputFormat.config and args.profile is None:
        raise TinytokenException(
            'A profile must be provided if output destination is set to "config"'
        )

    return args


def sign_in(
    discovery_uri: str, client_id: str, redirect_uri: str, user_agent_cmd: str
) -> Tokens:
    """Sign-in flow"""

    # OpenID Discovery
    auth_endpoint, token_endpoint = oauth.discovery(discovery_uri)

    # Start server on loopback to get redirect
    server.start(*utils.parse_uri(redirect_uri))

    # Kick off authorization flow
    url, code_verifier, request_state = oauth.authorization(
        client_id=client_id, redirect_uri=redirect_uri, auth_endpoint=auth_endpoint
    )

    # Execute user-agent to allow user to authenticate
    user_agent.execute(user_agent_cmd, url)

    try:
        code, response_state = server.queue.get(timeout=TIMEOUT)
    except Empty:
        raise TinytokenException(f"Timed out waiting for user's action ({TIMEOUT}s)")
    except KeyboardInterrupt:
        raise TinytokenException("Aborted by user")

    if not code:
        raise TinytokenException("Code was not provided in callback")

    # Exchange authorization code for id token
    return oauth.exchange(
        token_endpoint=token_endpoint,
        code_verifier=code_verifier,
        redirect_uri=redirect_uri,
        client_id=client_id,
        code=code,
        request_state=request_state,
        response_state=response_state,
    )


def refresh(discovery_uri: str, client_id: str, refresh_token: str) -> Tokens:
    """Refresh flow"""

    # OpenID Discovery
    auth_endpoint, token_endpoint = oauth.discovery(discovery_uri)

    return oauth.refresh(
        token_endpoint=token_endpoint, client_id=client_id, refresh_token=refresh_token
    )


def main():
    args = parse_args()

    # Create basedir
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)

    # Logging level
    if args.v == 1:
        logger.setLevel(logging.INFO)
    elif args.v >= 2:
        logger.setLevel(logging.DEBUG)

    # Get tokens
    if args.skip_cache:
        logger.info("Skipping cache")
        tokens = sign_in(
            discovery_uri=args.discovery_uri,
            client_id=args.client_id,
            redirect_uri=args.redirect_uri,
            user_agent_cmd=args.user_agent,
        )
    elif cache.exists(args.client_id):
        logger.info("Retrieving tokens from cache")
        tokens = cache.retrieve(args.client_id)
    else:
        logger.info("Token is not cached")
        tokens = sign_in(
            discovery_uri=args.discovery_uri,
            client_id=args.client_id,
            redirect_uri=args.redirect_uri,
            user_agent_cmd=args.user_agent,
        )

    # Check if still valid
    access_token_expired = jwt.expired(tokens.access_token)

    if access_token_expired:
        logger.info("Access token expired, attempting to refresh")
        try:
            tokens = refresh(
                discovery_uri=args.discovery_uri,
                client_id=args.client_id,
                refresh_token=tokens.refresh_token,
            )
        except RefreshTokenExpired:
            logger.info("Refresh token expired, attempting to authenticate")
            tokens = sign_in(
                discovery_uri=args.discovery_uri,
                client_id=args.client_id,
                redirect_uri=args.redirect_uri,
                user_agent_cmd=args.user_agent,
            )

    if not args.skip_cache or access_token_expired:
        logger.info("Caching tokens")
        cache.store(client_id=args.client_id, tokens=tokens)

    # Output
    output(OutputFormat[args.output], tokens, **vars(args))


def entry_point():
    try:
        return main()
    except TinytokenException as e:
        print(f"Error: {e}")
        sys.exit(1)
