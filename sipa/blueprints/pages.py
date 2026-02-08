"""
Blueprint for the flatpages
"""
from flask_flatpages.page import Page
from logging import getLogger

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from flask import Blueprint, current_app, redirect, render_template
from flask_login import current_user

from sipa.flatpages import Article, Category
from ..deps import Templates

logger = getLogger(__name__)

bp_pages = Blueprint('pages', __name__, url_prefix='/pages')
router_pages = APIRouter(prefix="/pages", default_response_class=HTMLResponse)


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

    return render_template("page.html", article=article)


@router_pages.get("/{category_id}/{article_id}", name="pages.show")
def show_(templates: Templates, category_id: str, article_id: str) -> HTMLResponse:
    category = Category(parent=None, id=category_id, default_locale="en")
    article = Article(parent=category, id=article_id, default_locale="en")
    article.add_page(locale="en", page=Page(
        path=f"__STUB_PAGES__/{category_id}/{article_id}.en.md",
        meta={},
        body="TEST!",
        html_renderer=lambda self: "TEST!",
        folder=category_id,
    ))
    return templates.TemplateResponse("page.html", dict(article=article))
