"""
Blueprint for the flatpages
"""

from logging import getLogger

from flask import Blueprint, render_template, redirect, current_app
from flask_login import current_user


logger = getLogger(__name__)

bp_pages = Blueprint('pages', __name__, url_prefix='/pages')


@bp_pages.route('/<category_id>/<article_id>')
def show(category_id, article_id):
    """Display a flatpage and parse dynamic content if available

    If available, a `<name>.<locale>.json` json_file is parsed and used to
    display A section on the webpage where users can select their
    dormitory and see _specific_ information like financial data.
    """
    article = current_app.cf_pages.get_or_404(category_id, article_id)

    try:
        restricted = article.restricted
    except AttributeError:
        restricted = False
    if restricted and not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()

    if article.link:
        return redirect(article.link)

    return render_template("template.html", article=article, dynamic=False)
