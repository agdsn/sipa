# -*- coding: utf-8 -*-

from flask import abort, request
from babel.core import UnknownLocaleError, Locale
from flask.ext.flatpages import FlatPages

from .babel import babel, locale_preferences
from operator import attrgetter
from os.path import dirname, basename, splitext


class Node:
    def __init__(self, parent, id):
        self.parent = parent
        self.id = id


class Article(Node):
    def __init__(self, parent, id):
        super().__init__(parent, id)
        self.localized_pages = {}
        self.default_page = None

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
        self.articles = {}

    def get_articles(self):
        """Return an iterator over the articles sorted by rank"""
        return iter(sorted(self.articles.values(), key=attrgetter('rank')))

    def __getattr__(self, attr):
        """An attribute interface.

        - Used for: ['rank', 'index', 'id', 'name']
        """
        try:
            return getattr(self.articles['index'], attr, False)
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

    def add_article(self, page_name, page):
        components = page_name.split('.')
        if len(components) == 1:
            article_id = page_name
            locale = babel.default_locale
        else:
            try:
                article_id = '.'.join(components[:-1])
                locale = Locale(components[-1])
            except UnknownLocaleError:
                article_id = page_name
                locale = babel.default_locale
        article = self.articles.get(article_id)
        if article is None:
            article = Article(self, article_id)
            article.default_page = page
            self.articles[article_id] = article
        article.localized_pages[str(locale)] = page
        if locale == babel.default_locale:
            article.default_page = page


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
        return category.articles.get(article_id)

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
            for a in list(category.articles.values()):
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
            page_name = components[-1]
            parent.add_article(page_name, page)

    def reload(self):
        self.flat_pages.reload()
        self._init_categories()


cf_pages = CategorizedFlatPages()
