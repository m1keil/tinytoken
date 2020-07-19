import sys
import json
import argparse
import logging
from queue import Empty
from pprint import pprint

from . import server, oauth, user_agent, sts

# Time to wait for callback from user-agent
TIMEOUT = 30

logging.basicConfig(level='WARNING', format='%(message)s')
logger = logging.getLogger('tinytoken')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.description = 'AWS CLI external credentials fetcher via OpenID Connect federation'
    parser.add_argument('-v', action='count', default=0, help='verbosity level')
    parser.add_argument('--role', '-r', required=True, help='arn of IAM role to assume')
    parser.add_argument('--client', '-c', dest='client_id', required=True, help='OAuth 2.0 client id')
    parser.add_argument('--user-agent', default='/usr/bin/open -a "Google Chrome"',
                        help='Custom user-agent execution command')

    return parser.parse_args()


def main():
    args = parse_args()
    if args.v == 1:
        logger.setLevel(logging.INFO)
    elif args.v >= 2:
        logger.setLevel(logging.DEBUG)

    # Start server on loopback to get redirect
    server_port = server.start()

    # Kick off authorization flow
    url, exchange = oauth.authorization(args.client_id, server_port)

    # Execute user-agent to allow user to authenticate
    user_agent.execute(args.user_agent, url)

    try:
        code = server.queue.get(timeout=TIMEOUT)
    except Empty:
        logger.error(f"Timed out waiting for user's action ({TIMEOUT}s)")
        sys.exit(1)

    # Exchange authorization code for id token
    id_token = exchange(port=server_port, code=code, client_id=args.client_id)

    # Call for AssumeRoleWithWebIdentity with id token
    credentials = sts.get_credentials(id_token, args.role)

    # Format message as required in:
    # https://docs.aws.amazon.com/cli/latest/topic/config-vars.html#sourcing-credentials-from-external-processes
    credentials['Version'] = 1
    print(json.dumps(credentials, indent=2))
