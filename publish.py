#!/usr/bin/env python

""" Static Site Generator.
Takes article in markdown, places it inside HTML template and updates index.
"""

import argparse
from pathlib import Path

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

class Config:
    def __init__(self):
        self.rootdir = Path.cwd()
        self.sourcedir = self.rootdir / 'pages' / 'recipes'
        self.destdir = self.rootdir / 'output'
        self.logfile = self.rootdir / 'logfile'
        print('Source found') if self.sourcedir.exists() else self.sourcedir.mkdir(parents=True)
        print('Destination found') if self.destdir.exists() else self.destdir.mkdir(parents=True)
        print('Logfile found') if self.logfile.exists() else self.logfile.touch()


def main():
    if args.infile:
        print('publishing {}…'.format(args.infile.name))
    elif args.update:
        print('updating…')
    else:
        print('nothing to do. exiting…')


if __name__ == '__main__':
    config = Config()
    main()
