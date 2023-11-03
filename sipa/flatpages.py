from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from operator import attrgetter
from os.path import basename, dirname, splitext

from babel.core import Locale, UnknownLocaleError, negotiate_locale
from flask import abort, request
from flask_babel import get_babel
from flask_flatpages import FlatPages, Page
from yaml.scanner import ScannerError

from sipa.babel import possible_locales, preferred_locales

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def cached_negotiate_locale(
    preferred_locales: tuple[str], available_locales: tuple[str]
) -> str | None:
    return negotiate_locale(
        preferred_locales,
        available_locales,
        sep="-",
    )


# NB: Node is meant to be a union `Article | Category`.
@dataclass
class Node:
    """An abstract object with a parent and an id"""

    parent: Category | None
    id: str

    #: Only used for initialization.
    #: determines the default page of an article.
    default_locale: Locale


@dataclass
class Article(Node):
    """The Article class

    An article provides the possibility to access multiple versions of
    a Page.  In this case, :py:attr:`localized_pages` is a dict where
    a locale string points to a :py:obj:`Page`.  The latter represents
    the actual markdown file located in the repository.

    After the initialization, which consists of adding pages with
    :py:meth:`add_page`, internal methods access only the page with
    the correct locale, which is proxied by :py:attr:`localized_page`.

    Besides that, :py:meth:`__getattr__` comfortably passes queries to
    the :py:obj:`localized_page.meta` dict.
    """

    #: The dict containing the localized pages of this article
    localized_pages: dict[str, Page] = field(init=False, default_factory=dict)
    #: The default page
    default_page: Page | None = field(init=False, default=None)

    def add_page(self, page: Page, locale: Locale) -> None:
        """Add a page to the pages list.

        If the name is not ``index`` and the validation via
        :py:meth:`validate_page_meta` fails, skip this.

        If no :py:attr:`default_page` is set or the locale equals
        :py:obj:`babel.default_locale`, set :py:attr:`default_page` to
        the given page.

        Update the :py:attr:`localized_pages` dict at the
        ``str(locale)`` key to ``page``.

        :param page: The page to add
        :param locale: The locale of this page
        """
        if not (self.id == "index" or validate_page_meta(page)):
            return

        self.localized_pages[str(locale)] = page
        if self.default_page is None or locale == self.default_locale:
            self.default_page = page

    @property
    def rank(self) -> int:
        """The rank of the :py:attr:`localized_page`

        This is what is given in the page's ``rank`` meta-attribute if
        available else ``100``.

        :returns: The :py:attr:`localized_page` s rank
        """
        return self.localized_page.meta.get('rank', 100)

    @property
    def html(self) -> str:
        """The :py:attr:`localized_page` as html

        :returns: The :py:attr:`localized_page` converted to html
        """
        return self.localized_page.html

    @property
    def link(self) -> str | None:
        """A valid link to this article

        :returns: The URL or ``None`` if the link starts with ``"/"``

        :raises: :py:obj:`AttributeError` if :py:attr:`localized_page`
                 doesn't have a link in the meta section.
        """
        raw_link = self.localized_page.meta.get('link', None)
        if raw_link and raw_link[0] == "/":
            return dirname(request.url_root) + raw_link

        return None

    @property
    def hidden(self) -> bool:
        """The hidden state of the :py:attr:`localized_page`

        This controls whether the page should be displayed in listings.

        :returns: The :py:attr:`localized_page` s hidden state
        """
        return self.localized_page.meta.get('hidden', False)

    @property
    def icon(self) -> str:
        return self.localized_page.meta.get("icon") or self.localized_page.meta.get(
            "glyphicon"
        )

    def __getattr__(self, attr: str) -> str:
        """Return the meta attribute of the localized page

        :param attr: The meta attribute to access

        :returns: The meta attribute of :py:attr:`localized_page`

        :raises: :py:obj:`AttributeError` if :py:obj:`attr` doesn't
                 exist in the page's meta
        """
        try:
            return self.localized_page.meta[attr]
        except KeyError as e:
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {attr!r}"
            ) from e

    @cached_property
    def available_locales(self) -> tuple[str]:
        return tuple(self.localized_pages.keys())

    @property
    def localized_page(self) -> Page:
        """The current localized page

        This is the flatpage of the first available locale from
        :py:func:`~sipa.babel.locale_preferences`, or
        :py:attr:`default_page`.

        :returns: The localized page
        """
        negotiated_locale = cached_negotiate_locale(
            tuple(preferred_locales()),
            self.available_locales,
        )
        if negotiated_locale is not None:
            return self.localized_pages[negotiated_locale]
        return self.default_page

    @property
    def file_basename(self) -> str:
        """The basename of the localized page without extension.

        Example: `categ/article.en.md` → `article.en`

        :returns: The basename of the :py:attr:`localized_page`
        """
        return splitext(basename(self.localized_page.path))[0]


def validate_page_meta(page: Page) -> bool:
    """Validate that the pages meta-section.

    This function is necessary because a page with incorrect
    metadata will raise some Errors when trying to access them.
    Note that this is done rather early as pages are cached.

    :param page: The page to validate

    :returns: Whether the page is valid
    """
    try:
        return "title" in page.meta
    except ScannerError:
        return False


@dataclass
class Category(Node):
    """The Category class

    * What's it used for?

    - Containing articles → should be iterable!
    """

    categories: dict = field(init=False, default_factory=dict)
    _articles: dict = field(init=False, default_factory=dict)

    @property
    def articles(self):
        """Return an iterator over the articles sorted by rank

        Only used for building the navigation bar
        """
        return iter(sorted(self._articles.values(), key=attrgetter('rank')))

    def __getattr__(self, attr):
        """An attribute interface.

        - Used for: ['rank', 'index', 'id', 'name']
        """
        try:
            index = self._articles['index']
        except KeyError as e:
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {attr!r}"
            ) from e
        return getattr(index, attr)

    def add_child_category(self, id):
        """Create a new Category from an id, keep it and return it.

        If the category already exists, return it instead and do nothing.
        """
        category = self.categories.get(id)
        if category is not None:
            return category

        category = Category(
            parent=self,
            id=id,
            default_locale=self.default_locale,
        )
        self.categories[id] = category
        return category

    def _parse_page_basename(self, basename):
        """Split the page basename into the article id and locale.

        `basename` is (supposed to be) of the form
        `<article_id>.<locale>`, e.g. `news.en`.

        If either there is no dot or the locale is unknown,
        the `default_locale` of babel is used.

        :return: The tuple `(article_id, locale)`.
        """
        default_locale = self.default_locale
        article_id, sep, locale_identifier = basename.rpartition('.')

        if sep == '':
            return basename, default_locale

        try:
            locale = Locale(locale_identifier)
        except UnknownLocaleError:
            logger.error("Unknown locale %s of arcticle %s",
                         locale_identifier, basename)
            return basename, default_locale
        if locale not in possible_locales():
            logger.warning("Locale %s of article is not a possible locale",
                           locale_identifier, basename)
            return basename, default_locale
        return article_id, locale

    def add_article(self, prefix, page):
        """Add a page to an article and create the latter if nonexistent.

        Firstly, the article_id is being extracted according to
        above scheme.  If an `Article` of this id already exists, it
        is asked to add the page accordingly.

        """
        article_id, locale = self._parse_page_basename(prefix)

        article = self._articles.get(article_id)
        if article is None:
            article = Article(
                parent=self,
                id=article_id,
                default_locale=self.default_locale,
            )
            self._articles[article_id] = article

        article.add_page(page, locale)


class CategorizedFlatPages:
    """The main interface to gather pages and categories

    * What is it used for?

    - Looping: E.g. In the navbar
    - get news → get_articles_of_category('news')
    - get static page → get_or_404()
    """
    def __init__(self):
        self.flat_pages = FlatPages()
        self.root_category = None
        self.app = None

    def init_app(self, app):
        assert self.app is None, "Already initialized with an app"
        app.config.setdefault('FLATPAGES_LEGACY_META_PARSER', True)
        self.app = app
        app.cf_pages = self
        self.flat_pages.init_app(app)
        babel = get_babel(app)
        self.root_category = Category(
            parent=None,
            id="<root>",
            default_locale=babel.default_locale,
        )
        self._init_categories()

    @property
    def categories(self):
        """Yield all categories as an iterable
        """
        return sorted(self.root_category.categories.values(),
                      key=attrgetter('rank'))

    def get(self, category_id, article_id):
        category = self.root_category.categories.get(category_id)
        if category is None:
            return None
        return category._articles.get(article_id)

    def get_category(self, category_id):
        """Return the `Category` object from a given name (id)
        """
        return self.root_category.categories.get(category_id)

    def get_articles_of_category(self, category_id):
        """Get the articles of a category

        - ONLY used for fetching news
        """
        category = self.get_category(category_id)
        if category is None:
            return []
        return [article for article in category._articles.values()
                if article.id != 'index']

    def get_or_404(self, category_id, article_id):
        """Fetch a static page"""
        page = self.get(category_id, article_id)
        if page is None:
            abort(404)
        return page

    def _init_categories(self):
        # TODO: Store categories, not articles
        for page in self.flat_pages:
            # get category + page name
            # plus, assert that there is nothing more to that.
            components = page.path.split('/')
            parent = self.root_category
            for category_id in components[:-1]:
                parent = parent.add_child_category(category_id)
            prefix = components[-1]
            parent.add_article(prefix, page)

    def reload(self):
        self.flat_pages.reload()
        self._init_categories()
