#!/usr/bin/env python

""" Static Site Generator.
Takes article in markdown, places it inside HTML template and updates index.
"""

import argparse
import hashlib
import time
from pathlib import Path

class Config:
    """ check for existence of directories / files and create them if necessary """
    def __init__(self):
        """
        TODO:
        check for existence (and integrity) of templates
        """
        self.rootdir = Path.cwd()
        self.sourcedir = self.rootdir / 'pages' / 'recipes'
        self.destdir = self.rootdir / 'output'
        self.templatedir = self.rootdir / 'templates'
        self.logfile = self.rootdir / 'logfile'
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        if not self.destdir.exists():
            self.destdir.mkdir(parents=True)
        if not self.templatedir.exists():
            self.templatedir.mkdir(parents=True)
        if not self.logfile.exists():
            self.logfile.touch()

def getargs():
    """ process command line arguments """
    parser = argparse.ArgumentParser(
        description='Static Site Generator'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('r', encoding='UTF-8'),
        help='publish only this file'
    )
    group.add_argument(
        '-u', '--update',
        action='store_true',
        help='re-build pages and index'
    )
    args = parser.parse_args()
    return args


def hash(file):
    """
    calculate the SHA-1 sum of incoming document
    """
    h = hashlib.sha1()
    h.update(file.read().encode('utf-8'))
    return h.hexdigest()

def logread(pattern):
    with config.logfile.open() as log:
        if pattern in log:
            return True
    return False

def logwrite(file):
    entry = f'{int(time.time())} {hash(file)} {file.name}\n'
    with config.logfile.open(mode='a') as log:
        log.write(entry)

def publish():
    """
    TODO:
    - extract title
    - calculate checksum of markdown document
    - check logfile for checksum
    - convert markdown to html
    - prepend & append templates
    - log the file
    """
    print('publishing {}…'.format(args.infile.name))

def update():
    """
    TODO:
    - scan sourcedir for files
    - check logfile for these filenames and see
    if their checksums have changed
    - publish the new ones
    """
    print('updating…')


if __name__ == '__main__':
    config = Config()
    args = getargs()
    if args.infile:
        logwrite(args.infile)
    elif args.update:
        update()
    else:
        print('nothing to do. exiting…')
