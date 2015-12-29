# -*- coding: utf-8 -*-
from operator import attrgetter
from os.path import basename, dirname, splitext

from babel.core import Locale, UnknownLocaleError
from yaml.scanner import ScannerError

from flask import abort, current_app, request
from flask_flatpages import FlatPages

from .babel import locale_preferences


class Node:
    """An abstract object with a parent and an id"""

    def __init__(self, parent, node_id):
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
    def __init__(self, parent, article_id):
        super().__init__(parent, article_id)
        #: The dict containing the localized pages of this article
        self.localized_pages = {}
        #: The default page
        self.default_page = None

    def add_page(self, page, locale):
        """Add a page to the pages list.

        If the name is not ``index`` and the validation via
        :py:meth:`validate_page_meta` fails, skip this.

        If no :py:attr:`default_page` is set or the locale equals
        :py:obj:`babel.default_locale`, set :py:attr:`default_page` to
        the given page.

        Update the :py:attr:`localized_pages` dict at the
        ``str(locale)`` key to ``page``.

        :param Page page: The page to add
        :param Locale locale: The locale of this page
        """
        if not (self.id == 'index' or self.validate_page_meta(page)):
            return

        self.localized_pages[str(locale)] = page
        if self.default_page is None or locale == babel.default_locale:
            self.default_page = page

    @staticmethod
    def validate_page_meta(page):
        """Validate that the pages meta-section.

        This function is necessary because a page with incorrect
        metadata will raise some Errors when trying to access them.
        Note that this is done rather early as pages are cached.

        :param page: The page to validate

        :returns: Whether the page is valid

        :rtype: bool
        """
        try:
            return 'title' in page.meta
        except ScannerError:
            return False

    @property
    def rank(self):
        """The rank of the :py:attr:`localized_page`

        This is what is given in the page's ``rank`` meta-attribute if
        available else ``100``.

        :returns: The :py:attr:`localized_page` s rank

        :rtype: int
        """
        return self.localized_page.meta.get('rank', 100)

    @property
    def html(self):
        """The :py:attr:`localized_page` as html

        :returns: The :py:attr:`localized_page` converted to html
        :rtype: str
        """
        return self.localized_page.html

    @property
    def link(self):
        """A valid link to this article

        :returns: The URL or ``None`` if the link starts with ``"/"``

        :rtype: str

        :raises: :py:obj:`AttributeError` if :py:attr:`localized_page`
                 doesn't have a link in the meta section.
        """
        try:
            raw_link = self.localized_page.meta['link']
        except KeyError:
            raise AttributeError()
        else:
            if raw_link and raw_link[0] == "/":
                return dirname(request.url_root) + raw_link

        return

    def __getattr__(self, attr):
        """Return the meta attribute of the localized page

        :param str attr: The meta attribute to access

        :returns: The meta attribute of :py:attr:`localized_page`

        :rtype: str

        :raises: :py:obj:`AttributeError` if :py:obj:`attr` doesn't
                 exist in the page's meta
        """
        try:
            return self.localized_page.meta[attr]
        except KeyError:
            raise AttributeError()

    @property
    def localized_page(self):
        """The current localized page

        This is the flatpage of the first available locale from
        :py:func:`~sipa.babel.locale_preferences`, or
        :py:attr:`default_page`.

        :returns: The localized page
        :rtype: Whatever has been added, hopefully :py:class:`Page`
        """
        available_locales = list(self.localized_pages.keys())
        for locale in locale_preferences():
            # Locale is unfortunately not hashable
            # so locale in self.localized_pages does not work
            for available_locale in available_locales:
                if available_locale == locale.language:
                    localized_page = self.localized_pages.get(available_locale)
                    return localized_page
        return self.default_page

    @property
    def file_basename(self):
        """The basename of the localized page without extension.

        Example: `categ/article.en.md` → `article.en`

        :returns: The basename of the :py:attr:`localized_page`

        :rtype: str
        """
        return splitext(basename(self.localized_page.path))[0]


class Category(Node):
    """The Category class

    * What's it used for?

    - Containing articles → should be iterable!
    """
    def __init__(self, parent, category_id):
        super().__init__(parent, category_id)
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
        except KeyError:
            raise AttributeError()
        return getattr(index, attr)

    def add_child_category(self, id):
        """Create a new Category from an id, keep it and return it.

        If the category already exists, return it instead and do nothing.
        """
        category = self.categories.get(id)
        if category is not None:
            return category

        category = Category(self, id)
        self.categories[id] = category
        return category

    @staticmethod
    def _parse_page_basename(basename):
        """Split the page basename into the article id and locale.

        `basename` is (supposed to be) of the form
        `<article_id>.<locale>`, e.g. `news.en`.

        If either there is no dot or the locale is unknown,
        the `default_locale` of babel is used.

        :return: The tuple `(article_id, locale)`.
        """
        default_locale = current_app.babel_instance.default_locale
        components = basename.split('.')

        if len(components) == 1:
            return basename, default_locale

        article_id = '.'.join(components[:-1])
        try:
            return article_id, Locale(components[-1])
        except UnknownLocaleError:
            return basename, default_locale

    def add_article(self, prefix, page):
        """Add a page to an article and create the latter if nonexistent.

        Firstly, the article_id is being extracted according to
        above scheme.  If an `Article` of this id already exists, it
        is asked to add the page accordingly.

        """
        article_id, locale = self._parse_page_basename(prefix)

        article = self._articles.get(article_id)
        if article is None:
            article = Article(self, article_id)
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
        self.root_category = Category(None, '<root>')

    def init_app(self, app):
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
        articles = []
        category = self.get_category(category_id)
        if category:
            for a in category._articles.values():
                if a.id != 'index':
                    articles.append(a)
        return articles

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


cf_pages = CategorizedFlatPages()
