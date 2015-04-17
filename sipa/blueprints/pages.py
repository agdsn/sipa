#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Blueprint for the flatpages
"""

from flask import Blueprint, render_template

from sipa.flatpages import cf_pages


bp_pages = Blueprint('pages', __name__, url_prefix='/pages')

# todo rethink routing. Which link will redirect here?
# @bp_pages.route('/<category>')
# def show_category(category):
# pass


# todo create sitemap at /pages/
# @bp_pages.route('/', defaults={'page': 'index'})
@bp_pages.route('/<category_id>/<article_id>')
def show(category_id, article_id):
    # todo think of a more elegant way to reload
    cf_pages.reload()
    article = cf_pages.get_or_404(category_id, article_id)
    return render_template('template.html', article=article)
