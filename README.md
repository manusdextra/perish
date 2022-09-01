# Static Site Generator

[Publish or Perish](https://en.wikipedia.org/wiki/Publish_or_perish)

This will accept as source a directory on your hard drive containing some markdown files, at minimum an index.md, and publish a complete website to a location of your choice.

I made this tool as a learning exercise in various things. In the beginning, I went for a simple shell script, since that was what interested me at the time. I also thought it might be easier to have immediate access to files through I/O redirection built into the shell. When my ideas became more complex, I decided to re-write the script in Python, which also meant I could learn a lot about _pathlib_ in the process.

Another reason for going with Python is the _re_ library. When writing the shell script, I thought about using something like _sed_ or _awk_ to convert my articles from Markdown, but it seemed overkill to learn an entire new language just for this "simple" task. I previously refactored a markdown parser as part of an online programming exercise, and this made me curious about regular expressions, and I thought it would be easier to learn them within a familiar environment. I have now started to extract the parser I wrote into a separate file, and I may develop it further (or replace it with a pre-built solution if I find that it doesn't suit my needs anymore).

Finally, I had been reading about lightweight, minimalistic web design, and the idea appealed to me, so I wanted to use this opportunity to write a simple site using only barebones HTML and CSS. I figure it might also be a good testing ground for various accessibility optimizations and best practices I read about online.

## Usage

By default, this script works within the directory it is located. Here, it expects the following:

- a folder named "templates" which contains "base.html" (a Jinja2 template) and "style.css"
  (in future, I may add defaults for these)
- a folder named "pages" which contains—at a minimum—an index.md file, as well as any number (theoretically) of folders
