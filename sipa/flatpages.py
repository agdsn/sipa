from __future__ import absolute_import
from flask import abort
from babel.core import UnknownLocaleError, Locale
from flask.ext.flatpages import FlatPages

from .babel import babel, locale_preferences


def compare(x, y):
    if x.rank is None:
        return -1
    if y.rank is None:
        return 1
    if x.rank < y.rank:
        return -1
    else:
        return 1


class Node(object):
    def __init__(self, parent, id):
        self.parent = parent
        self.id = id


class Article(Node):
    def __init__(self, parent, id):
        super(Article, self).__init__(parent, id)
        self.localized_pages = {}
        self.default_page = None

    @property
    def rank(self):
        try:
            return self.localized_page.meta['rank']
        except KeyError:
            return 100

    def __getattr__(self, attr):
        try:
            if attr is 'html':
                return self.localized_page.html
            else:
                return self.localized_page.meta[attr]
        except KeyError:
            raise AttributeError()

    @property
    def localized_page(self):
        available_locales = self.localized_pages.keys()
        for locale in locale_preferences():
            # Locale is unfortunately not hashable
            # so locale in self.localized_pages does not work
            for available_locale in available_locales:
                if available_locale == locale:
                    localized_page = self.localized_pages.get(available_locale)
                    return localized_page
        return self.default_page


class Category(Node):
    def __init__(self, parent, id):
        super(Category, self).__init__(parent, id)
        self.categories = {}
        self.articles = {}

    def articles_itterator(self):
        return iter(sorted(self.articles.values(), cmp=compare))

    def __getattr__(self, attr):
        try:
            return getattr(self.articles['index'], attr, False)
        except KeyError:
            raise AttributeError()

    def add_category(self, id):
        category = self.categories.get(id)
        if category is not None:
            return category
        category = Category(self, id)
        self.categories[id] = category
        return category

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
        article.localized_pages[locale] = page
        if locale == babel.default_locale:
            article.default_page = page


class CategorizedFlatPages(object):
    def __init__(self):
        self.flat_pages = FlatPages()
        self.root_category = Category(None, '<root>')

    def init_app(self, app):
        self.flat_pages.init_app(app)
        self._set_categories()

    def __iter__(self):
        return iter(sorted(self.root_category.categories.values(),
                    cmp=compare))

    def get(self, category_id, article_id):
        category = self.root_category.categories.get(category_id)
        if category is None:
            return None
        return category.articles.get(article_id)

    def get_articles_of_category(self, category_id):
        barticles = []
        category = self.root_category.categories.get(
            category_id)
        if category:
            for a in category.articles.values():
                if a.id != 'index':
                    barticles.append(a)
        return barticles

    def get_or_404(self, category_id, article_id):
        page = self.get(category_id, article_id)
        if page is None:
            abort(404)
        return page

    def _set_categories(self):
        for page in self.flat_pages:
            components = page.path.split('/')
            parent = self.root_category
            for category_id in components[:-1]:
                parent = parent.add_category(category_id)
            page_name = components[-1]
            parent.add_article(page_name, page)

    def reload(self):
        self.flat_pages.reload()
        self._set_categories()


cf_pages = CategorizedFlatPages()
