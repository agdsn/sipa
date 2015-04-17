#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Blueprint providing features regarding the news entries.
"""

from flask import Blueprint, render_template
from sipa.flatpages import cf_pages

bp_news = Blueprint('news', __name__, url_prefix='/news')


@bp_news.route("/")
def display():
    """Get all markdown files from 'content/news/', parse them and put
    them in a list for the template.
    The formatting of these files is described in the readme.
    """
    cf_pages.reload()
    latest = cf_pages.get_articles_of_category('news')
    latest = sorted(latest, key=lambda a: a.date, reverse=True)
    latest = latest[0:10]
    return render_template("index.html", articles=latest)

