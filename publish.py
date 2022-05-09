#!/usr/bin/env python

"""
Static Site Generator.

Goals:
    - collect categories (maybe in Config class?)
    - automatically create index pages. This involves the categories collected
      and a place in the templates, potentially even some kind of jinja-like block
      system.
      (which needs to be properly documented)
    - proper logger with levels of error messages
"""

import argparse
import hashlib
import pathlib
import shutil
import time
import sys
import re
from parsec import parse


class Config:
    """ 
    check for existence of directories / files and create them if necessary
    """
    def __init__(self):
        self.rootdir = pathlib.Path.cwd() # this would need to be changed to make the script portable
        self.logfile = self.rootdir / 'logfile'
        self.templatedir = self.rootdir / 'templates'
        self.template_prefix = self.rootdir / 'templates' / 'prefix.html'
        self.template_suffix = self.rootdir / 'templates' / 'suffix.html'
        self.sourcedir = self.rootdir / 'pages'
        self.destdir = pathlib.Path('/data/www')
        if not self.logfile.exists():
            self.logfile.touch()
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        if not self.destdir.exists():
            self.destdir.mkdir(parents=True)


class Infile():

    def __init__(self, path, index=None):
        self.source = path
        self.filename = path.name
        with self.source.open() as f:
            self.contents = f.read()
        self.checksum = self.hash()
        self.published = self.logread()

        self.categories = [
                x.stem for x
                in self.source.relative_to(config.rootdir).parents[::-1]
                ]
        self.destination = config.destdir.joinpath(
                *self.categories[2::])

        for category in self.categories:
            all_categories.add(category)

        self.index = index

    def hash(self):
        """
        calculate the SHA-1 sum of incoming document
        """
        h = hashlib.sha1()
        h.update(self.contents.encode('utf-8'))
        return h.hexdigest()

    def logread(self):
        """
        check if the file has been handled before
        could use re.match to look for by filename and then see which of the
        matches also has the checksum. This way would enable rewriting history
        """
        with config.logfile.open() as logfile:
            log = logfile.read()
            if self.checksum in log:
                return True
            else:
                return False

    def logwrite(self):
        self.published = True
        entry = f'{int(time.time())} {self.checksum} {self.filename}\n'
        with config.logfile.open(mode='a') as log:
            log.write(entry)

    def publish(self):
        if self.source.suffix == '.md':
            # is this necessary? can't I just look for the first match in the string?
            self.headings = re.findall(r'#{1,6} (.*)\n', self.contents)
            self.title = self.headings[0]
            narrate(f'publish {self.title}…')
            self.html = parse(self.contents)
        else:
            self.html = self.contents
            self.title = self.source

        output = ''
        with config.template_prefix.open() as f:
            output += f.read()
        output += self.html
        if self.index:
            output += self.index
        with config.template_suffix.open() as f:
            output += f.read()

        if not self.destination.exists():
            self.destination.mkdir(parents=True)
        outfile = self.destination.joinpath(self.source.stem).with_suffix('.html')
        if not outfile.exists():
            outfile.touch()
        outfile.write_text(output, encoding='utf-8')
        self.logwrite()


def getargs():
    """ 
    process command line arguments 
    """
    parser = argparse.ArgumentParser(
        description='Static Site Generator'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        'infile',
        nargs='?',
        type=pathlib.Path,
        help='publish only this file'
    )
    group.add_argument(
        '-u', '--update',
        action='store_true',
        help='re-build pages and index'
    )
    args = parser.parse_args()
    return args


def update(directory, rebuild=False):
    for f in directory.iterdir():
        if f.is_dir():
            update(f)
        else:
            if f.name == 'index.md':
                continue
            article = Infile(f)
            if rebuild:
                article.publish()
            elif not article.published:
                article.publish()


def templates_ok():
    narrate('check if templates exist…')
    if not config.templatedir.exists():
        bail('no templates found', fatal=True)
    if not config.template_prefix.exists():
        bail('prefix template not found', fatal=True)
    if not config.template_suffix.exists():
        bail('suffix template not found', fatal=True)

    untouched = True
    narrate('check if the templates have changed…')
    for f in config.templatedir.iterdir():
        template = Infile(f)
        if template.source.suffix == '.css' and not template.published:
            shutil.copyfile(f, (config.destdir / f.name))
            narrate('updated stylesheet.')
            template.logwrite()
        if template.source.suffix == '.html' and not template.published:
            narrate(f'updated {template.filename}')
            untouched = False
            template.logwrite()
    return untouched


def build_index():
    """
    TODO:
    - [ ] check for index page for each subfolder
    - [ ] if present, suffix .html list, else make it standalone
    """
    narrate('build index…')
    linklist = '<ul>\n'
    for f in config.destdir.rglob('*.html'):
        linklist += f'\t<li><a href="{f.relative_to(config.destdir)}" />{f.stem}</a></li>\n'
    linklist += '\n</ul>'
    i = config.sourcedir.joinpath('index.md')
    index = Infile(i, index=linklist)
    index.publish()

def narrate(message):
    """
    Simple logger to console, to be fleshed out
    """
    print(f'…\t{message}')

def bail(error, fatal=False):
    """
    Print error message and exit.
    This needs fleshed out for minor and major errors. The "fatal" flag is just a
    workaround.
    """
    print(f'ERROR:\t{error}\n')
    if fatal:
        sys.exit(1)

if __name__ == '__main__':
    config = Config()
    args = getargs()
    all_categories = set()
    if templates_ok():
        update(config.sourcedir)
    else:
        update(config.sourcedir, rebuild=True)
    # build_index()
