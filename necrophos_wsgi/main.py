import logging.config
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser(description='start necrophos server')

    parser.add_argument(
        '-p', '--port',
        type=int,
        help='listen to port',
        default=8089,
    )

    parser.add_argument(
        '--app',
        required=True,
        help='app object',
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
    )

    return parser.parse_args()


def setup_logging(verbose=False):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': (
                    '[%(asctime)s %(process)d %(name)s '
                    '%(module)s:%(lineno)d %(levelname)s] %(message)s'
                )
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'propagate': True,
                'level': 'DEBUG' if verbose else 'ERROR',
            },
        },
    })


def setup_env():
    import os
    import sys

    sys.path.append(os.getcwd())


def main():
    from .server import Server
    args = parse_args()

    setup_logging(args.verbose)

    setup_env()

    server = Server(args.app)
    return server.run(port=args.port)
