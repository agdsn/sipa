import re

from flask import request
from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor


def absolute_path_replacer(match):
    """Correct the url in a regex match prepending the absolute path"""
    assert len(match.groups()) == 2

    prefix = request.script_root
    if prefix.endswith("/"):
        prefix = prefix[:-1]

    return "{key}=\"{path}\"".format(
        key=match.group(1),
        path=prefix + match.group(2)
    )


class LinkPostprocessor(Postprocessor):
    def run(self, text):
        return re.sub(
            '(href|src)="(/[^"]*)"',
            absolute_path_replacer,
            text,
            flags=re.IGNORECASE,
        )


class AbsoluteLinkExtension(Extension):
    """ Add the absolute link patch to Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add an instance of TableProcessor to BlockParser. """
        md.postprocessors['link_patch'] = LinkPostprocessor(md)


def makeExtension(*args, **kwargs):
    return AbsoluteLinkExtension(*args, **kwargs)
