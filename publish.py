#!/usr/bin/env python

"""
Static Site Generator.

Goals:
    - automatically create index pages. This involves the categories collected
      and a place in the templates, potentially even some kind of jinja-like block
      system.
      (which needs to be properly documented)
"""

import argparse
import hashlib
import logging
import logging.handlers
import pathlib
import re
import shutil
import sys
import time

from parsec import parse

log = logging.getLogger()

class Config:
    """ 
    check for existence of directories / files and create them if necessary
    """
    def __init__(self):
        self.rootdir = pathlib.Path.cwd()
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


def setup_log(options):
    """
    Configure log
    """
    root = logging.getLogger("")
    root.setLevel(logging.WARNING)
    log.setLevel(options.debug and logging.DEBUG or logging.INFO)
    if not options.silent:
        custom_handler = logging.StreamHandler()
        custom_handler.setFormatter(logging.Formatter(
            "%(levelname)s\t[%(name)s]\t%(message)s"))
        root.addHandler(custom_handler)

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
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
            "-d", "--debug", action="store_true",
            default=False,
            help="enable debugging"
    )
    group.add_argument(
            "-s", "--silent", action="store_true",
            default=False,
            help="don't log anything"
    )
    args = parser.parse_args()
    return args


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
            log.debug(f'publish {self.filename}…')
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

        link = outfile.relative_to(config.destdir)
        all_links.add(
                f'\t<li><a href="/{link}">{self.title}</a></li>\n'
        )


def update(directory, rebuild=False):
    if rebuild:
        log.debug(f'rebuild directory "{directory.stem}"')
    for f in directory.iterdir():
        if f.is_dir():
            update(f, rebuild)
        else:
            article = Infile(f)
            if rebuild:
                article.publish()
            elif not article.published:
                article.publish()


def templates_ok():
    log.debug('check if templates exist…')
    if not config.templatedir.exists():
        log.fatal('no templates found')
        sys.exit(1)
    if not config.template_prefix.exists():
        log.fatal('prefix template not found')
        sys.exit(1)
    if not config.template_suffix.exists():
        log.fatal('suffix template not found')
        sys.exit(1)

    untouched = True
    log.debug('check if the templates have changed…')
    for f in config.templatedir.iterdir():
        template = Infile(f)
        if template.source.suffix == '.css' and not template.published:
            shutil.copyfile(f, (config.destdir / f.name))
            log.debug('update stylesheet.')
            template.logwrite()
        if template.source.suffix == '.html' and not template.published:
            log.debug(f'update {template.filename}')
            untouched = False
            template.logwrite()
    return untouched


def build_index(directory):
    """
    TODO:
    - [ ] check for index page for each subfolder
    - [ ] if present, suffix .html list, else make it standalone
    """
    category = f'{directory.stem}'
    log.debug(f'build index for {category}…')
    path = config.sourcedir / directory.stem / f'{category}.md'
    linklist = f'<h2>{category.capitalize()}</h2>\n<ul>\n'
    for link in all_links:
        # this condition keeps the directoy's index page out of the index
        if len(re.findall(category, link)) == 1:
            linklist += link
    linklist += '</ul>'
    index = Infile(path, index=linklist)
    index.publish()


if __name__ == '__main__':
    """
    TODO:
    - [ ] if "rebuild" is set to false, the index is built without links.
          these links are only generated when articles are published, so if
          they're not updated, the list is empty.
    """
    config = Config()
    args = getargs()
    setup_log(args)
    all_categories = set()
    all_links = set()
    if input(f"\nReady to publish {config.rootdir} to {config.destdir}.\nPress Enter to continue."):
        exit()
    if templates_ok():
        update(config.sourcedir)
    if args.update:
        update(config.sourcedir, rebuild=True)
    else:
        update(config.sourcedir, rebuild=True)
    for d in config.destdir.iterdir():
        if d.is_dir():
            build_index(d)
