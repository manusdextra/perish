#!/usr/bin/env python

""" Static Site Generator.
Takes article in markdown, places it inside HTML template and updates index.
"""

import argparse
import sys

parser = argparse.ArgumentParser(
        description='Static Site Generator')
group = parser.add_mutually_exclusive_group()
group.add_argument('--update', action='store_true')
group.add_argument('--publish', action='store_true')
parser.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin)
args = parser.parse_args()


def main():
    if args.update:
        print('updating…')
    elif args.publish:
        print('publishing {}…'.format(args.infile))
    else:
        print('okay whatever man')


if __name__ == '__main__':
    main()
