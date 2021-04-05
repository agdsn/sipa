import re

from flask import request
from markdown import Markdown
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
    """A postprocessor fixing absolute links in the HTML result of a markdown render.

    This needs to be a postprocessor compared to a treeprocessor, because
    the link may be in a pure HTML block.  Those blocks however are processed by means
    of the [`MarkdownInHtmlExtension`](https://python-markdown.github.io/extensions/md_in_html/),
    which replaces HTML by a tag in a preprocessing step and replaces this tag by the HTML
    in a postprocessing step.
    Therefore, the only way to catch these links is with a postprocessor and a regex.
    """
    def run(self, text):
        return re.sub(
            '(href|src)="(/[^"]*)"',
            absolute_path_replacer,
            text,
            flags=re.IGNORECASE,
        )


class AbsoluteLinkExtension(Extension):
    """ Add the absolute link patch to Markdown. """

    def extendMarkdown(self, md: Markdown):
        """ Add an instance of TableProcessor to BlockParser. """
        # see https://python-markdown.github.io/extensions/api/#registries for what's happening here
        md.postprocessors.register(
            LinkPostprocessor(md),
            'link_patch',
            # we need to run after `raw_html` (prio=30).  See `LinkPostprocessor` docstring.
            20,
        )


def makeExtension(*args, **kwargs):
    return AbsoluteLinkExtension(*args, **kwargs)
