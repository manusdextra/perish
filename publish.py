#!/usr/bin/env python

"""
Static Site Generator.
Takes article in markdown, places it inside HTML template and updates index.
"""

import argparse
import hashlib
import time
import re
from pathlib import Path

class Config:
    """ 
    check for existence of directories / files and create them if necessary
    """
    def __init__(self):
        self.rootdir = Path.cwd() # this would need to be changed to make the script portable
        self.logfile = self.rootdir / 'logfile'
        self.templatedir = self.rootdir / 'templates'
        self.template_prepend = self.rootdir / 'templates' / 'prepend.html'
        self.template_append = self.rootdir / 'templates' / 'append.html'
        self.sourcedir = self.rootdir / 'pages' / 'recipes'
        self.destdir = self.rootdir / 'output'
        if not self.logfile.exists():
            self.logfile.touch()
        if not self.templatedir.exists():
            bail('no templates found')
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        if not self.destdir.exists():
            self.destdir.mkdir(parents=True)

class Article():
    """
    convert markdown to HTML

    TODO:
    - [x] extract section headings (maybe a list of sections?)
    - [x] convert to HTML
    - [ ] insert section tags with headings?
    - [ ] prepend/append template
    - [ ] decide whether or not to do log checking at this point
    """
    def __init__(self, file):
        markdown = file.read()
        file.close()
        self.headings = re.findall(r'#{1,6} (.*)\n', markdown)
        self.title = self.headings[0]
        self.content = self.parse(markdown)

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
        narrate(f'publish "{self.title}"…')
        pass

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
    h.update(file.name.encode('utf-8'))
    return h.hexdigest()

def logread(file):
    """
    check if the file has been handled before
    """
    pattern = hash(file)
    with config.logfile.open() as logfile:
        log = logfile.read()
        if pattern in log:
            return True
        else:
            return False

def logwrite(file):
    """
    write changes to logfile
    TODO: think about optimising this. Is it worth it setting up a class and
    having any infile create a new instance of it with hash, title etc?
    """
    entry = f'{int(time.time())} {hash(file)} {file.name}\n'
    with config.logfile.open(mode='a') as log:
        log.write(entry)

def publish(file):
    """
    TODO:
    - [x] extract title
    - [x] calculate checksum of markdown document
    - [x] check logfile for checksum
    - [x] convert markdown to html
    - [ ] prepend & append templates
    - [ ] log the file
    """
    narrate("check log for infile…")
    if not logread(file):
        post = Article(file)
        post.publish()
    else:
        narrate(f"File found in log, exit…")

def parse():
    """
    Simplified markdown parser
    """
    pass

def update():
    """
    TODO:
    - [ ] scan sourcedir for files
    - [ ] check logfile for these filenames and see
    if their checksums have changed
    - [ ] publish the new ones
    """
    narrate('update…')
    # check if the templates have changed
    narrate('check templates…')
    if not logread(config.template_prepend
    ) and not logread(config.template_append):
        narrate('templates have been updated')
        logwrite(config.template_prepend)
        logwrite(config.template_append)
        rebuild()
    else:
        narrate('templates OK')

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
    config = Config()
    args = getargs()
    if args.infile:
        publish(args.infile)
    elif args.update:
        update()
    else:
        bail('nothing to do')
