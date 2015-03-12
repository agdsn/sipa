#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Blueprint for the flatpages
"""

from flask import Blueprint, render_template, session, abort
from flatpages import pages


bp_pages = Blueprint('pages', __name__, url_prefix='/pages')

# todo rethink routing. Which link will redirect here?
# @bp_pages.route('/<category>')
# def show_category(category):
# pass

# todo create sitemap at /pages/
# @bp_pages.route('/', defaults={'page': 'index'})
@bp_pages.route('/<category>/<name>')
def show(category, name):
    lang = session.get('lang', 'de')
    page = pages.get_or_404(u'{}/{}.{}'.format(category, name, lang))
    if page is None:
        abort(404)
    else:
        return render_template('template.html', page=page)