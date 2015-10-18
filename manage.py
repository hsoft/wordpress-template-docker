import argparse
import logging

from cmds import start, stop, make

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Make output more verbose",
    )
    subparsers = parser.add_subparsers(dest='cmd')
    subparser = subparsers.add_parser(
        'make',
        help="Build docker images"
    )
    subparser.add_argument(
        'target',
        nargs='?',
        choices=['wordpress'],
        help="Build the specified image (default is to build all)",
    )
    subparser.add_argument(
        '--no-cache',
        action='store_true',
        help="Don't use cache when building",
    )
    subparser = subparsers.add_parser(
        'start',
        help="Spawn containers that run the website"
    )
    subparser.add_argument(
        '--port',
        default='80',
        help="Port to serve the site onto",
    )
    subparser = subparsers.add_parser(
        'stop',
        help="Kill containers that run the website"
    )
    subparser.add_argument(
        '--clean',
        action='store_true',
        help="Remove data containers as well"
    )
    return parser

def main(argv=None):
    parser = get_parser()
    args = parser.parse_args(argv)
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.cmd == 'make':
        make(target=args.target, nocache=bool(args.no_cache))
    elif args.cmd == 'start':
        start(args.port)
    elif args.cmd == 'stop':
        stop(clean=args.clean)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

