#!/usr/bin/env python

"""
Static Site Generator.

Goals:
    - tags
    - index
"""

import argparse
import hashlib
import time
import re
import pathlib
import shutil

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
        # this is a hacky workaround for the tags function below
        self.sourcedepth = len([ x.stem for x in self.sourcedir.parents ]) + 2
        self.destdir = self.rootdir / 'output'
        if not self.logfile.exists():
            self.logfile.touch()
        if not self.templatedir.exists():
            bail('no templates found')
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        if not self.destdir.exists():
            self.destdir.mkdir(parents=True)

class Infile():
    """
    convert markdown to HTML

    """
    def __init__(self, file):
        self.path = file
        self.filename = file.name
        with file.open() as f:
            self.contents = f.read()
        self.checksum = self.hash()
        self.published = self.logread()
        self.tags = [
                x.stem for x
                in self.path.parents[-config.sourcedepth::-1]
                ]

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
        - [ ] paragraphs vs newlines (empty lines should separate paragraphs)
        """
        narrate("parse infile…")
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
        """
        TODO:
        - [ ] when pre/appending templates, use regex to insert tags?
        """
        if self.path.suffix == '.md':
            self.headings = re.findall(r'#{1,6} (.*)\n', self.contents)
            self.title = self.headings[0]
            self.html = self.parse(self.contents)
        else:
            self.html = self.contents
            self.title = self.path

        narrate("check log for infile…")
        if not self.published:
            narrate(f'publish "{self.title}"…')
            narrate(f'\t tags: {self.tags}')
            output = ''
            with config.template_prepend.open() as f:
                output += f.read()
            output += self.html
            with config.template_append.open() as f:
                output += f.read()
            outfile = (config.destdir / self.path.stem).with_suffix('.html')
            outfile.write_text(output, encoding='utf-8')
            self.logwrite()
        else:
            bail(f"File found in log, exit…")

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
    """
    TODO:
    """
    narrate('update…')
    # check if the templates have changed
    narrate('check templates…')
    for f in config.templatedir.iterdir():
        template = Infile(f)
        if template.path.suffix == '.css' and not template.published:
            shutil.copyfile(f, (config.destdir / f.name))
            narrate('updated stylesheet')
            template.logwrite()
        if template.path.suffix == '.html' and not template.published:
            # rebuild()
            narrate(f'updated {template.filename}')
            template.logwrite()

    narrate('check articles…')
    def checkfiles(directory):
        for f in directory.iterdir():
            if f.is_dir():
                checkfiles(f)
            else:
                article = Infile(f)
                if not article.published:
                    article.publish()
    checkfiles(config.sourcedir)
    narrate('update completed.')

    """
    a problem here is that if you undo previous changes, such as changing a single value,
    that version of the file will still be in the log and prevent any changes being made.
    maybe there is a way to diff the files in src and dst?
    """

def rebuild():
    """
    - re-do every single file
    - potentially delete logfile and create new one
    - make this undoable (how?)
    """
    pass

def narrate(message):
    """
    Simple logger to console, to be fleshed out
    """
    print(f'…\t{message}')

def bail(error):
    """
    Print error message and exit
    """
    print(f'ERROR:\t{error}\n')

if __name__ == '__main__':
    """
    Since I want to implement a tags system which necessitates re-building
    the whole thing every time an article is added, I might as well dispense with
    the CLI arguments. I'll leave them in for now since they'll probs come in handy
    later.
    Also, the logging system needs to be overhauled to account for changes over time.
    """
    config = Config()
    args = getargs()
    update()
