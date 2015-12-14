import re
import os
import os.path

from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor


prefix = os.getenv('SIPA_UWSGI_PREFIX', '/sipa_debug')


def absolute_path_replacer(match):
    return "{key}=\"{path}\"".format(
        key=match.group(1),
        path=os.path.join(prefix, match.group(2)[1:]),
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
