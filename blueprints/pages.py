#!/usr/bin/env python
# -*- coding: utf-8 -*-



from flask import Blueprint, render_template, session, abort
from jinja2.exceptions import TemplateNotFound
from flatpages import pages as flat_pages


bp_pages = Blueprint('pages', __name__, url_prefix='/pages')


# todo create sitemap at /pages/
# @bp_pages.route('/', defaults={'page': 'index'})
@bp_pages.route('/<page>')
def show(page):
    lang = session.get('lang', 'de')
    flat_pages.reload()
    page = next((p for p in flat_pages
                if p.path.startswith(lang + u'/' + page)),
                None)
    if page is None:
        abort(404)
    else:
        return render_template('template.html', page=page)