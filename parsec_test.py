import unittest

from parsec import parse


class TestMarkdownParser(unittest.TestCase):
    maxDiff = None

    def test_emdash(self):
        self.assertEqual(
            parse("I don't know--but I can guess"),
            "<p>I don't know&mdash;but I can guess</p>",
        )

    def test_links(self):
        self.assertEqual(
            parse("[https://google.com](Google)"),
            "<p><a href=\"https://google.com\">Google</a></p>"
        )
    def test_umlaut(self):
        self.assertEqual(parse("Deine Mütter stinken"), "<p>Deine Mütter stinken</p>")

    def test_lists(self):
        self.assertEqual(
            parse(
                "# Nut Roast\n\n## Ingredients\n\n* 1 tbsp olive oil\n* 15g butter\n* 1 large onion, finely chopped\n* 2 sticks celery, finely chopped\n* 400ml passata\n\n## Method"
            ),
            "<h1>Nut Roast</h1>\n\n<h2>Ingredients</h2>\n\n<ul><li>1 tbsp olive oil</li>\n<li>15g butter</li>\n<li>1 large onion, finely chopped</li>\n<li>2 sticks celery, finely chopped</li>\n<li>400ml passata</li></ul>\n\n<h2>Method</h2>",
        )
