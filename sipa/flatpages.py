# -*- coding: utf-8 -*-
import logging

from flask import abort, request
from babel.core import UnknownLocaleError, Locale
from flask.ext.flatpages import FlatPages
from yaml.scanner import ScannerError

from .babel import babel, locale_preferences
from operator import attrgetter
from os.path import dirname, basename, splitext

logger = logging.getLogger(__name__)


class Node:
    def __init__(self, parent, id):
        self.parent = parent
        self.id = id


class Article(Node):
    def __init__(self, parent, id):
        super().__init__(parent, id)
        self.localized_pages = {}
        self.default_page = None

    def add_page(self, page, locale):
        """Add a page to the pages list.

        If no `default_page` is set or the locale equals
        `babel.default_locale`, set `default_page` to the given page.
        """
        if not (self.id == 'index' or self.validate_page_meta(page)):
            return

        self.localized_pages[str(locale)] = page
        if self.default_page is None or locale == babel.default_locale:
            self.default_page = page

    @staticmethod
    def validate_page_meta(page):
        """Validate that the given page fits the constraints.

        Currently, the only constraints are having a title, and not
        failing to parse the metadata.  The latter is achieved by just
        accessing `page.meta` in any way, since it is cached and will
        start parsing on even the lightest, first touch.

        :return: True if the constraints are met, else False.

        """
        try:
            return 'title' in page.meta
        except ScannerError:
            return False

    @property
    def rank(self):
        try:
            return self.localized_page.meta['rank']
        except KeyError:
            return 100

    @property
    def html(self):
        return self.localized_page.html

    @property
    def link(self):
        try:
            raw_link = self.localized_page.meta['link']
        except KeyError:
            raise AttributeError
        else:
            if raw_link and raw_link[0] == "/":
                return dirname(request.url_root) + raw_link

        return

    def __getattr__(self, attr):
        """Return the meta attribute of the localized page"""
        try:
            return self.localized_page.meta[attr]
        except KeyError:
            raise AttributeError()
            logger.warning("Article does not contain attribute %s", attr,
                           extra={'data': {'id': self.id}})

    @property
    def localized_page(self):
        """Return a flatpage of the current locale or the default page"""
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
        """Return the basename of the file without extension.

        Example: `categ/article.en.md` → `article.en`
        """
        return splitext(basename(self.localized_page.path))[0]


class Category(Node):
    """The Category class

    * What's it used for?

    - Containing articles → should be iterable!
    """
    def __init__(self, parent, id):
        super().__init__(parent, id)
        self.categories = {}
        self._articles = {}

    @property
    def articles(self):
        """Return an iterator over the articles sorted by rank

        Only used for building the navigation bar
        """
        if not self._articles:
            return iter()
        return iter(sorted(self._articles.values(), key=attrgetter('rank')))

    def __getattr__(self, attr):
        """An attribute interface.

        - Used for: ['rank', 'index', 'id', 'name']
        """
        try:
            return getattr(self._articles['index'], attr, False)
        except KeyError:
            raise AttributeError()

    def add_child_category(self, id):
        """Create a new Category from an id, keep it and return it."""

        # if already existent, return and proceed
        if id in self.categories:
            return self.categories[id]

        child_category = Category(self, id)
        self.categories[id] = child_category
        return child_category

    @staticmethod
    def _parse_page_basename(basename):
        """Split the page basename into the article id and locale.

        `basename` is (supposed to be) of the form
        `<article_id>.<locale>`, e.g. `news.en`.

        If either there is no dot or the locale is unknown,
        `babel.default_locale` is returned.

        :return: The tuple `(article_id, locale)`.
        """
        default_locale = babel.default_locale
        components = basename.split('.')

        if len(components) == 1:
            return basename, default_locale

        article_id = '.'.join(components[:-1])
        try:
            return article_id, Locale(components[-1])
        except UnknownLocaleError:
            return basename, default_locale

    def add_article(self, basename, page):
        """Add a page to an article and create the latter if nonexistent.

        Firstly, the article_id is being extracted according to
        above scheme.  If an `Article` of this id already exists, it
        is asked to add the page accordingly.

        """
        article_id, locale = self._parse_page_basename(basename)

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
            basename = components[-1]
            parent.add_article(basename, page)

    def reload(self):
        self.flat_pages.reload()
        self._init_categories()


cf_pages = CategorizedFlatPages()
