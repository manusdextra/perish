#!/usr/bin/env python

""" Static Site Generator.
Takes article in markdown, places it inside HTML template and updates index.
"""

import argparse
from pathlib import Path

class Config:
    def __init__(self):
        self.rootdir = Path.cwd()
        self.sourcedir = self.rootdir / 'pages' / 'recipes'
        self.destdir = self.rootdir / 'output'
        self.logfile = self.rootdir / 'logfile'
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        if not self.destdir.exists():
            self.destdir.mkdir(parents=True)
        if not self.logfile.exists():
            self.logfile.touch()

def getargs():
    parser = argparse.ArgumentParser(
        description='Static Site Generator'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('r'),
        help='publish only this file'
    )
    group.add_argument(
        '-u', '--update',
        action='store_true',
        help='re-build pages and index'
    )
    args = parser.parse_args()
    return args


def main():
    if args.infile:
        print('publishing {}…'.format(args.infile.name))
    elif args.update:
        print('updating…')
    else:
        print('nothing to do. exiting…')


if __name__ == '__main__':
    config = Config()
    args = getargs()
    main()
