import logging
from operator import attrgetter
from os.path import basename, dirname, splitext
from typing import Any

from babel.core import Locale, UnknownLocaleError, negotiate_locale
from flask import abort, request
from flask_flatpages import FlatPages, Page
from yaml.scanner import ScannerError

from sipa.babel import get_user_locale_setting, possible_locales

logger = logging.getLogger(__name__)


class Node:
    """An abstract object with a parent and an id"""

    def __init__(self, extension, parent, node_id):
        #: The CategorizedFlatPages extension
        self.extension = extension
        #: The parent object
        self.parent = parent
        #: This object's id
        self.id = node_id


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
    def __init__(self, extension, parent, article_id):
        super().__init__(extension, parent, article_id)
        #: The dict containing the localized pages of this article
        self.localized_pages: dict[Any, Page] = {}
        #: The default page
        self.default_page: Page = None

    def add_page(self, page: Page, locale: Locale):
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
        if not (self.id == 'index' or self.validate_page_meta(page)):
            return

        self.localized_pages[str(locale)] = page
        default_locale = self.extension.app.babel_instance.default_locale
        if self.default_page is None or locale == default_locale:
            self.default_page = page

    @staticmethod
    def validate_page_meta(page: Page) -> bool:
        """Validate that the pages meta-section.

        This function is necessary because a page with incorrect
        metadata will raise some Errors when trying to access them.
        Note that this is done rather early as pages are cached.

        :param page: The page to validate

        :returns: Whether the page is valid
        """
        try:
            return 'title' in page.meta
        except ScannerError:
            return False

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
                "{!r} object has no attribute {!r}"
                .format(type(self).__name__, attr)) from e

    @property
    def localized_page(self) -> Page:
        """The current localized page

        This is the flatpage of the first available locale from
        :py:func:`~sipa.babel.locale_preferences`, or
        :py:attr:`default_page`.

        :returns: The localized page
        """
        available_locales = list(self.localized_pages.keys())

        user_locale = str(get_user_locale_setting())
        if user_locale is None:
            preferred_locales = []
        else:
            preferred_locales = [user_locale]
        preferred_locales.extend(request.accept_languages.values())

        negotiated_locale = negotiate_locale(
            preferred_locales, available_locales, sep='-')
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


class Category(Node):
    """The Category class

    * What's it used for?

    - Containing articles → should be iterable!
    """
    def __init__(self, extension, parent, category_id):
        super().__init__(extension, parent, category_id)
        self.categories = {}
        self._articles = {}

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
                "{!r} object has no attribute {!r}"
                .format(type(self).__name__, attr)) from e
        return getattr(index, attr)

    def add_child_category(self, id):
        """Create a new Category from an id, keep it and return it.

        If the category already exists, return it instead and do nothing.
        """
        category = self.categories.get(id)
        if category is not None:
            return category

        category = Category(self.extension, self, id)
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
        default_locale = self.extension.app.babel_instance.default_locale
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
            article = Article(self.extension, self, article_id)
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
        self.root_category = Category(self, None, '<root>')
        self.app = None

    def init_app(self, app):
        assert self.app is None, "Already initialized with an app"
        app.config.setdefault('FLATPAGES_LEGACY_META_PARSER', True)
        self.app = app
        app.cf_pages = self
        self.flat_pages.init_app(app)
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
