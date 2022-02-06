#!/usr/bin/env python

""" Static Site Generator.
Takes article in markdown, places it inside HTML template and updates index.
"""

import argparse
import sys

parser = argparse.ArgumentParser(
        description='Static Site Generator')
group = parser.add_mutually_exclusive_group()
group.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('r'),
        help='publish only this file')
group.add_argument(
        '-u', '--update',
        action='store_true',
        help='re-build pages and index')
args = parser.parse_args()


def main():
    if args.infile:
        print('publishing {}…'.format(args.infile.name))
    elif args.update:
        print('updating…')
    else:
        print('okay whatever man')


if __name__ == '__main__':
    main()
