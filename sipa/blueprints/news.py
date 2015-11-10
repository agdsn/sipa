# -*- coding: utf-8 -*-

"""
Blueprint providing features regarding the news entries.
"""
from operator import attrgetter

from flask import Blueprint, render_template, url_for, redirect, abort, request
from sipa.flatpages import cf_pages


bp_news = Blueprint('news', __name__, url_prefix='/news')


@bp_news.route("/")
def show():
    """Get all markdown files from 'content/news/', parse them and put
    them in a list for the template.
    The formatting of these files is described in the readme.
    """
    start = request.args.get('start', None, int)
    end = request.args.get('end', None, int)
    cf_pages.reload()
    news = cf_pages.get_articles_of_category('news')
    if len(news) is 0:
        return render_template("index.html", articles=None,
                               previous_range=0, next_range=0)
    news = sorted(news, key=attrgetter('date'), reverse=True)

    default_step = 10
    # calculating mod len() allows things like `end=-1` for the last
    # article(s).  this may lead to confusing behaviour because this
    # allows values out of the range (|val|≥len(latest)), but this
    # will only result in displaying articles instead of throwing an
    # error.  Apart from that, such values would just appear if edited
    # manually.
    if start is None:
        if end is None:
            start, end = 0, default_step
        else:
            end %= len(news)
            start = max(end - default_step + 1, 0)
    else:
        start %= len(news)
        if end is None:
            end = min(start + default_step - 1, len(news) - 1)
        else:
            end %= len(news)

    delta = end - start + 1
    prev_range, next_range = None, None

    if start > 0:
        prev_range = {'start': max(start - delta, 0), 'end': start - 1}
    if end < len(news) - 1:
        next_range = {'start': end + 1, 'end': min(end + delta, len(news) - 1)}

    return render_template("index.html", articles=news[start:end+1],
                           previous_range=prev_range, next_range=next_range)


@bp_news.route("/<filename>")
def show_news(filename):
    news = cf_pages.get_articles_of_category('news')

    for article in news:
        print("article: {}".format(article))
        print("article.localized_page: {}".format(article.localized_page))

        if article.file_basename == filename:
            return render_template("template.html", article=article)

    abort(404)
