#!/usr/bin/env python

"""
Static Site Generator.

"""

import argparse
import logging
import logging.handlers
import pathlib
import re
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

from parsec import parse

log = logging.getLogger()

class Config:
    """ 
    check for existence of directories / files and create them if necessary
    """
    def __init__(self):
        self.rootdir = pathlib.Path.cwd()
        # Jinja stuff
        env = Environment(
                loader=FileSystemLoader("templates"),
                autoescape=select_autoescape()
        )
        self.template = env.get_template("base.html")
        self.sourcedir = self.rootdir / 'pages'
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        self.destdir = pathlib.Path('/data/www')
        if not self.destdir.exists():
            self.destdir.mkdir(parents=True)
        self.stylesheet = self.rootdir / 'templates' / 'style.css'
        if self.stylesheet.exists():
            shutil.copyfile(self.stylesheet, self.destdir / 'style.css')


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

    def __init__(self, path):
        self.source = path
        self.filename = path.name
        with self.source.open() as f:
            self.contents = f.read()
        self.headings = re.findall(r'#{1,6} (.*)\n', self.contents)
        self.title = self.headings[0]

        # set up destination
        self.categories = [
                x.stem for x
                in self.source.relative_to(config.rootdir).parents[::-1]
        ]
        self.destination = config.destdir.joinpath(
                *self.categories[2::])
        if not self.destination.exists():
            self.destination.mkdir(parents=True)
        self.outfile = self.destination.joinpath(self.source.stem).with_suffix('.html')
        self.link = self.outfile.relative_to(config.destdir)

    def publish(self, index):
        if self.source.suffix == '.md':
            # is this necessary? can't I just look for the first match in the string?
            log.debug(f'publish {self.filename}…')
            self.html = parse(self.contents)
        else:
            self.html = self.contents
            self.title = self.source

        # render template
        output = config.template.render(
                content=self.html,
                title=self.title,
                index=index,
        )

        # write to file
        if not self.outfile.exists():
            self.outfile.touch()
        self.outfile.write_text(output, encoding='utf-8')


class Index():
    def __init__(self):
        self.files = set()
        self.find_all_files(config.sourcedir)
        self.linklist = self.build_index(config.sourcedir)

    def build_index(self, path):
        linklist = f'<ul>'
        for node in path.iterdir():
            if node.stem == "index":
                link = f'<li><a href="/index.html">Home</a></li>\n'
                linklist = re.sub(r'(\A<ul>)(.*)', r'\1%s\2' % link, linklist) 
            elif node.is_dir():
                linklist += f'<li><a href="/{node.stem}/{node.stem}.html">{node.stem.capitalize()}</a><li>\n'
            elif not node.is_dir():
                linklist += f'<li><a href="/{node.stem}.html">{node.stem.capitalize()}</a></li>\n'
        linklist += f'</ul>'
        return linklist

    def find_all_files(self, directory):
        for f in directory.iterdir():
            if f.is_dir():
                self.find_all_files(f)
            else:
                self.files.add(Infile(f))


if __name__ == '__main__':
    config = Config()
    args = getargs()
    setup_log(args)
    index = Index()
    for file in index.files:
        file.publish(index.linklist)
