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

class Config:
    """ 
    check for existence of directories / files and create them if necessary
    """
    def __init__(self):
        self.rootdir = pathlib.Path.cwd() # this would need to be changed to make the script portable
        self.logfile = self.rootdir / 'logfile'
        self.templatedir = self.rootdir / 'templates'
        self.template_prepend = self.rootdir / 'templates' / 'prepend.html'
        self.template_append = self.rootdir / 'templates' / 'append.html'
        self.sourcedir = self.rootdir / 'pages'
        # this is a hacky workaround for the categories function below
        self.sourcedepth = len([ x.stem for x in self.sourcedir.parents ]) + 2
        self.destdir = self.rootdir / 'output'
        if not self.logfile.exists():
            self.logfile.touch()
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        if not self.destdir.exists():
            self.destdir.mkdir(parents=True)

class Infile():
    """
    convert markdown to HTML

    """
    def __init__(self, path):
        self.path = path
        self.filename = path.name
        with path.open() as f:
            self.contents = f.read()
        self.checksum = self.hash()
        self.published = self.logread()
        self.categories = [
                x.stem for x
                in self.path.parents[-config.sourcedepth::-1]
                ]
        for category in self.categories:
            all_categories.add(category)

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

    def parse(self, text):
        """
        TODO:
        - [ ] implement images and links
        - [ ] fix empty paragraphs (see comment at bottom)
        - [ ] em dashes, ellipses and degree symbols should be valid HTML characters
        - [ ] paragraphs vs newlines (empty lines should separate paragraphs)
        """
        narrate("parse markdown…")
        content = text
        content = re.sub(r'__([^\n]+?)__', r'<strong>\1</strong>', content)
        content = re.sub(r'_([^\n]+?)_', r'<em>\1</em>', content)
        content = re.sub(r'^- (.*?$)', r'<li>\1</li>', content, flags=re.M)
        content = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', content, flags=re.S)
        for i in range(6, 0, -1):
            content = re.sub(
                    r'^{} (.*?$)'.format('#' * i),
                    r'<h{0}>\1</h{0}>'.format(i),
                    content, flags=re.M)
        content = re.sub(r'^(?!<[hlu])(.*?$)', r'<p>\1</p>', content, flags=re.M)
        content = re.sub(r'<p></p>', r'', content) # why?
        # narrate(f'check article:\n\n\n{content}\n\n')
        return content

    def publish(self):
        narrate(f'check log for {self.filename}…')
        if self.published:
            bail(f'{self.filename} found in log, skip…')
        else:
            narrate(f'not found in log, continue…')

        if self.path.suffix == '.md':
            # is this necessary? can't I just look for the first match in the string?
            self.headings = re.findall(r'#{1,6} (.*)\n', self.contents)
            self.title = self.headings[0]
            self.html = self.parse(self.contents)
        else:
            self.html = self.contents
            self.title = self.path

        narrate(f'publish "{self.title}"…\n\t\t categories: {self.categories}')

        output = ''
        with config.template_prepend.open() as f:
            output += f.read()
        output += self.html
        with config.template_append.open() as f:
            output += f.read()
        dest_path = config.destdir.joinpath(
                *self.categories)
        if not dest_path.exists():
            dest_path.mkdir(parents=True)
        outfile = dest_path.joinpath(self.path.stem).with_suffix('.html')
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

def update():
    narrate('update…')

    narrate('check templates…')
    if not config.templatedir.exists():
        bail('no templates found', True)
    if not config.template_append.exists():
        bail('append template not found', True)
    if not config.template_prepend.exists():
        bail('prepend template not found', True)
    rebuild_needed = False

    # check if the templates have changed
    for f in config.templatedir.iterdir():
        template = Infile(f)
        if template.path.suffix == '.css' and not template.published:
            shutil.copyfile(f, (config.destdir / f.name))
            narrate('updated stylesheet.')
            template.logwrite()
        if template.path.suffix == '.html' and not template.published:
            narrate(f'updated {template.filename}')
            rebuild_needed = True
            template.logwrite()

    narrate('check articles…')
    def checkfiles(directory):
        for f in directory.iterdir():
            if f.is_dir():
                checkfiles(f)
            else:
                article = Infile(f)
                if rebuild_needed:
                    article.publish()
                elif not article.published:
                    article.publish()
    checkfiles(config.sourcedir)

    narrate('update completed.')

    """
    a problem here is that if you undo previous changes, such as changing a single value,
    that version of the file will still be in the log and prevent any changes being made.
    maybe there is a way to diff the files in src and dst?
    """

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
    """
    Since I want to implement a categories system which necessitates re-building
    the whole thing every time an article is added, I might as well dispense with
    the CLI arguments. I'll leave them in for now since they'll probs come in handy
    later.
    Also, the logging system needs to be overhauled to account for changes over time.
    """
    config = Config()
    args = getargs()
    all_categories = set()
    update()
