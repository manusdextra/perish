#!/usr/bin/env python

"""
Static Site Generator.

"""

import argparse
import datetime
import logging
import pathlib
import re
import shutil
import subprocess
import sys

from jinja2 import (Environment, FileSystemLoader, TemplateNotFound,
                    select_autoescape)

from parsec import parse

log = logging.getLogger()


def setup_log(options) -> None:
    """
    Configure log
    """
    root = logging.getLogger("")
    root.setLevel(logging.WARNING)
    log.setLevel(options.verbose and logging.DEBUG or logging.INFO)
    if not options.silent:
        custom_handler = logging.StreamHandler()
        custom_handler.setFormatter(
            logging.Formatter("%(levelname)s\t[%(name)s]\t%(message)s")
        )
        root.addHandler(custom_handler)


def getargs():
    """
    process command line arguments
    """
    parser = argparse.ArgumentParser(description="Static Site Generator")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "directory",
        nargs="?",
        type=pathlib.Path,
        help="the directory to be published",
        default=pathlib.Path.cwd(),
    )
    group.add_argument(
        "-p",
        "--publish",
        action="store_true",
        help="push staging directory to public server",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-v", "--verbose", action="store_true", default=False, help="enable logging"
    )
    group.add_argument(
        "-s", "--silent", action="store_true", default=False, help="don't log anything"
    )
    arguments = parser.parse_args()
    return arguments


class Config:
    """
    check for existence of directories / files and create them if necessary
    """

    def __init__(self, args) -> None:
        self.rootdir = args.directory.absolute()

        # source directory
        self.sourcedir = self.rootdir / "pages"
        if not self.sourcedir.exists():
            log.fatal(f"no 'pages' folder found in {self.rootdir}, aborting")
            sys.exit(1)
        log.debug(f"use {self.sourcedir} as source directory")

        # staging directory and git repository
        self.staging = self.rootdir / "output"
        if not self.staging.exists():
            self.staging.mkdir(parents=True)
        log.debug(f"use {self.staging} as staging directory")

        # stylesheet
        self.stylesheet = self.rootdir / "templates" / "style.css"
        if self.stylesheet.exists():
            log.debug("publish stylesheet…")
            shutil.copyfile(self.stylesheet, self.staging / "style.css")
        else:
            log.critical(f"no stylesheet found in {self.stylesheet}")

        # Jinja stuff
        env = Environment(
            loader=FileSystemLoader(self.rootdir / "templates"),
            autoescape=select_autoescape(),
        )
        try:
            self.template = env.get_template("template.html")
        except TemplateNotFound:
            log.critical(f"No template found in {self.sourcedir}")
            sys.exit(1)


class Infile:
    """
    read markdown (or HTML) file and convert it if necessary,
    insert into template and write to file
    """

    def __init__(self, path: pathlib.Path) -> None:
        self.source = path
        self.filename = path.name
        with self.source.open() as file:
            try:
                self.title = re.sub(r"(#.?)(.*)\n", r"\2", file.readline())
            except Exception as e:
                log.critical(f"Problem with {file}: {e}")
            self.contents = file.read()
        self.html = parse(self.contents)

        # set up destination
        self.destination = config.staging.joinpath(
            self.source.relative_to(config.sourcedir)
        ).parent
        if not self.destination.exists():
            self.destination.mkdir(parents=True)
        self.outfile = self.destination.joinpath(self.source.stem).with_suffix(".html")
        self.link = self.outfile.relative_to(config.staging)

    def publish(self, linklist):
        """
        collate contents and index, insert into template and write to file
        """
        log.debug("publish %s…", self.title)

        branches = None
        if self.source.parent.stem == self.source.stem:
            log.debug("\tadd index to %s", self.filename)
            # check if there are pages/folders beneath this page
            parent = self.source.parent.stem
            if linklist.categories.get(parent):
                branches = linklist.categories[self.source.stem]

        # render template
        output: str = config.template.render(
            content=self.html,
            title=self.title,
            nav=linklist.navigation,
            branches=branches,
        )

        # write to file
        if not self.outfile.exists():
            self.outfile.touch()
        self.outfile.write_text(output, encoding="utf-8")


class Index:
    """
    traverse input directory to find folders representing categories
    and build a list of links to be used as the index
    """

    def __init__(self, config) -> None:
        self.files: set[Infile] = set()
        self.find_all_files(config.sourcedir)
        self.navigation = self.build_nav()
        self.categories = {
            f"{path.stem}": f"{self.build_index(path)}"
            for path in config.sourcedir.iterdir()
            if path.is_dir()
        }

    def is_valid_node(self, path) -> None:
        invalid_patterns = [
            "template.html",
            "style.css",
            ".git",
        ]
        return path not in invalid_patterns

    def find_all_files(self, path) -> None:
        """take all files and create articles from them"""
        for node in path.iterdir():
            if not self.is_valid_node(node.name):
                continue
            if node.is_dir():
                self.find_all_files(node)
            else:
                self.files.add(Infile(node))

    def build_nav(self) -> list[dict[str, str]]:
        """This collects all files and directories in the top level of the source directory
        TODO: document the why of using links.extend()"""
        links: list[dict[str, str]] = []
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
                if file.is_dir() and self.is_valid_node(file.name)
            ]
        )
        links = sorted(links, key=lambda x: x["caption"])
        return links

    def make_title(self, string) -> str:
        """
        Replaces hyphens with spaces and capitalises
        """
        string = string.split("-")
        string = [string[0].upper() + string[1::] + " " for string in string]
        string = "".join(string)
        return string

    def build_index(self, path, level=2) -> str:
        """
        this goes through the whole tree and collects all files.
        ideally, I'd like to use this for any folder that should have
        an index page.
        """
        heading = f"<h{level}>{self.make_title(path.stem)}</h{level}>\n<ul>\n"
        linklist = heading

        for node in path.iterdir():
            if node.stem == "index":
                link = '\t<li><a href="/index.html">Home</a></li>\n'
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

        # If nothing has been added, foobar.md is the only file in foobar
        # and the linklist isn't necessary
        if linklist == heading:
            return ""

        linklist += "</ul>\n"
        return linklist


if __name__ == "__main__":
    args = getargs()
    setup_log(args)
    config = Config(args)
    index = Index(config)
    for article in index.files:
        article.publish(index)
    if args.publish:
        log.debug(f"push staging directory {config.staging} to remote…")
        subprocess.run(
            [
                "rsync",
                "-av",
                ".",
                "henning@manusdextra.com:/usr/share/nginx/html",
                "--exclude=.git",
                "--delete",
            ],
            cwd=config.staging,
        )
