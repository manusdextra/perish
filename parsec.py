import re


def parse(markdown):
    """
    TODO:
    - [ ] implement images and links
    - [ ] fix empty paragraphs (see comment at bottom)
    - [ ] em dashes, ellipses and degree symbols should be valid HTML characters
    - [ ] preserve umlaute
    - [ ] paragraphs vs newlines (empty lines should separate paragraphs)
    """
    content = markdown
    content = re.sub(r"--", r"&mdash;", content)
    content = re.sub(r"__([^\n]+?)__", r"<strong>\1</strong>", content)
    content = re.sub(r"_([^\n]+?)_", r"<em>\1</em>", content)
    content = re.sub(r"^[-*] (.*?$)", r"<li>\1</li>", content, flags=re.M)
    # this is a problem if there is more than one list in the source, in particular
    # one "interrupted" by headlines, which will be matched due to the S flag (ignore newlines)
    content = re.sub(r"(<li>.*</li>)(<h.>)*", r"<ul>\1</ul>", content, flags=re.S)
    for i in range(6, 0, -1):
        content = re.sub(
            r"^{} (.*?$)".format("#" * i),
            r"<h{0}>\1</h{0}>".format(i),
            content,
            flags=re.M,
        )
    content = re.sub(r"^(?!<[hlu])(.*?$)", r"<p>\1</p>", content, flags=re.M)
    content = re.sub(r"<p></p>", r"", content)  # why?
    return content


if __name__ == "__main__":
    pass
