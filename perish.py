#!/usr/bin/env python

"""
Static Site Generator.

"""

import os
import argparse
import logging
import logging.handlers
import pathlib
import re
import shutil
from typing import Namespace

from jinja2 import Environment, FileSystemLoader, select_autoescape

from parsec import parse

log = logging.getLogger()


def setup_log(options: Namespace) -> None:
    """
    Configure log
    """
    root = logging.getLogger("")
    root.setLevel(logging.WARNING)
    log.setLevel(options.debug and logging.DEBUG or logging.INFO)
    if not options.silent:
        custom_handler = logging.StreamHandler()
        custom_handler.setFormatter(
            logging.Formatter("%(levelname)s\t[%(name)s]\t%(message)s")
        )
        root.addHandler(custom_handler)


def getargs() -> Namespace:
    """
    process command line arguments
    """
    parser = argparse.ArgumentParser(description="Static Site Generator")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "infile", nargs="?", type=pathlib.Path, help="publish only this file"
    )
    group.add_argument(
        "-p",
        "--publish",
        action="store_true",
        help="push staging directory to public server",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-d", "--debug", action="store_true", default=False, help="enable debugging"
    )
    group.add_argument(
        "-s", "--silent", action="store_true", default=False, help="don't log anything"
    )
    args = parser.parse_args()
    return args


class Config:
    """
    check for existence of directories / files and create them if necessary
    """

    def __init__(self) -> None:
        self.rootdir = pathlib.Path.cwd()
        # Jinja stuff
        env = Environment(
            loader=FileSystemLoader("templates"), autoescape=select_autoescape()
        )
        self.template = env.get_template("base.html")
        self.sourcedir = self.rootdir / "pages"
        if not self.sourcedir.exists():
            self.sourcedir.mkdir(parents=True)
        self.staging = pathlib.Path("/data/www")
        if not self.staging.exists():
            self.staging.mkdir(parents=True)
        self.stylesheet = self.rootdir / "templates" / "style.css"
        if self.stylesheet.exists():
            log.debug("publish stylesheet…")
            shutil.copyfile(self.stylesheet, self.staging / "style.css")


class Infile:
    def __init__(self, path: pathlib.Path) -> None:
        self.source = path
        self.filename = path.name
        with self.source.open() as f:
            self.title = re.sub(r"(#.?)(.*)\n", r"\2", f.readline())
            self.contents = f.read()

        # set up destination
        self.destination = config.staging.joinpath(
            self.source.relative_to(config.sourcedir)
        ).parent
        if not self.destination.exists():
            self.destination.mkdir(parents=True)
        self.outfile = self.destination.joinpath(self.source.stem).with_suffix(".html")
        self.link = self.outfile.relative_to(config.staging)

    def publish(self, index):
        if self.source.suffix == ".md":
            # is this necessary? can't I just look for the first match in the string?
            log.debug(f"publish {self.title}…")
            self.html = parse(self.contents)
        else:
            self.html = self.contents
            self.title = self.source

        branches = None
        if self.source.parent.stem == self.source.stem:
            log.debug(f"\t{self.filename} is an index page")
            # check if there are pages/folders beneath this page
            parent = self.source.parent.stem
            if index.categories.get(parent):
                branches = index.categories[self.source.stem]

        # render template
        output: str = config.template.render(
            content=self.html,
            title=self.title,
            nav=index.navigation,
            branches=branches,
        )

        # write to file
        if not self.outfile.exists():
            self.outfile.touch()
        self.outfile.write_text(output, encoding="utf-8")


class Index:
    def __init__(self) -> None:
        self.files: set[Infile] = set()
        self.find_all_files(config.sourcedir)
        self.navigation = self.build_nav()
        self.categories = {
            f"{path.stem}": f"{self.build_index(path)}"
            for path in config.sourcedir.iterdir()
            if path.is_dir()
        }

    def find_all_files(self, path) -> None:
        for f in path.iterdir():
            if f.is_dir():
                self.find_all_files(f)
            else:
                self.files.add(Infile(f))

    def build_nav(self) -> list[dict[str, str]]:
        """This collects all files and directories in the top level of the source directory"""
        links: list[dict[str, str]] = []
        links.append({"href": "/index.html", "caption": "Home"})
        links.extend(
            [
                {
                    "href": f"/{file.outfile.relative_to(config.staging)}",
                    "caption": f"{file.source.stem.capitalize()}",
                }
                for file in self.files
                if file.source.parent == config.sourcedir
                and not file.source.stem == "index"
            ]
        )
        links.extend(
            [
                {
                    "href": f"/{file.stem}/{file.stem}.html",
                    "caption": file.stem.capitalize(),
                }
                for file in config.sourcedir.iterdir()
                if file.is_dir()
            ]
        )
        return links

    def build_index(self, path, level=2) -> str:
        """
        this goes through the whole tree and collects all files.
        ideally, I'd like to use this for any folder that should have
        an index page.
        """
        linklist = f"<h{level}>{path.stem.capitalize()}</h{level}>\n<ul>\n"
        for node in path.iterdir():
            if node.stem == "index":
                link = f'\t<li><a href="/index.html">Home</a></li>\n'
                linklist = re.sub(r"(\A<ul>\n)(.*)", r"\1%s\2" % link, linklist)
            elif node.is_dir():
                linklist += self.build_index(node, level=level + 1)
            elif not node.is_dir():
                links = [
                    f"""\t<li><a href="/{file.outfile.relative_to(config.staging)}">
                    {file.title}</a></li>\n"""
                    for file in self.files
                    if file.source.stem == node.stem
                    and not file.source.stem == file.source.parent.stem
                ]
                for link in links:
                    linklist += link
        linklist += f"</ul>\n"
        return linklist


if __name__ == "__main__":
    args = getargs()
    setup_log(args)
    config = Config()
    index = Index()
    for file in index.files:
        file.publish(index)
    if args.publish:
        print("Handing off to publishing script…")
        os.system("./publish")
