"""
Blueprint providing features regarding the news entries.
"""
import typing as t
from operator import attrgetter
from traceback import format_exception_only

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    request,
    render_template_string,
)
from flask_flatpages import Page

from sipa.flatpages import CategorizedFlatPages, Article

bp_news = Blueprint('news', __name__, url_prefix='/news')


@bp_news.route("/")
def show():
    """Get all markdown files from 'content/news/', parse them and put
    them in a list for the template.
    The formatting of these files is described in the readme.
    """
    start = request.args.get('start', None, int)
    end = request.args.get('end', None, int)
    cf_pages = current_app.cf_pages
    cf_pages.reload()
    news = sorted(
        (article for article in cf_pages.get_articles_of_category('news')
         if hasattr(article, 'date')),
        key=attrgetter('date'),
        reverse=True,
    )
    if len(news) == 0:
        return render_template(
            "news.html", articles=None, previous_range=0, next_range=0
        )

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

    return render_template(
        "news.html",
        articles=news[start : end + 1],
        previous_range=prev_range,
        next_range=next_range,
    )


@bp_news.route("/<filename>")
def show_news(filename):
    news = current_app.cf_pages.get_articles_of_category('news')

    for article in news:
        if article.file_basename == filename:
            return render_template("news.html", articles=[article])

    abort(404)


def try_get_content(cf_pages: CategorizedFlatPages, filename: str) -> str:
    """Reconstructs the content of a news article from the given filename."""
    news = cf_pages.get_articles_of_category("news")
    article = next((a for a in news if a.file_basename == filename), None)
    assert isinstance(article, Article)
    if not article:
        return ""
    p = article.localized_page
    # need to reconstruct actual content; only have access to parsed form
    return p._meta + "\n\n" + p.body


@bp_news.route("/edit")
@bp_news.route("/<filename>/edit")
def edit(filename: str | None = None):
    return render_template(
        "news_edit.html", content=try_get_content(current_app.cf_pages, filename)
    )


@bp_news.route("/preview", methods=["GET", "POST"])
def preview():
    article = request.form.get("article-content") or request.args.get("article-content")
    if article is None:
        abort(400)

    flatpages = t.cast(CategorizedFlatPages, current_app.cf_pages).flat_pages
    page = t.cast(Page, flatpages._parse(content=article, path="…", rel_path="…"))
    try:
        return render_template_string(
            '{% import "macros/article.html" as m %} {{ m.render_news(page) }}',
            page=page,
        )
    except Exception as e:
        return render_template_string(
            """
                <div class="alert alert-danger" role='alert'>
                    <h4 class="alert-heading">Error</h4>
                    <small>
                        <pre><code>{{ backtrace }}</code></pre>
                    </small>
                </div>
            """,
            backtrace=("\n".join(format_exception_only(e))),
        )
