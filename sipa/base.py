#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from babel import Locale
from flask import request, session
from flask.ext.babel import get_locale
from flask.ext.login import LoginManager, AnonymousUserMixin
from werkzeug.routing import IntegerConverter as BaseIntegerConverter

from model import init_context, division_from_name
from model.constants import ACTIONS, STATUS_COLORS
from sipa import logger
from sipa.babel import babel, possible_locales
from sipa.flatpages import cf_pages
from sipa.initialization import init_env_and_config, init_logging
from sipa.utils.graph_utils import render_traffic_chart

login_manager = LoginManager()


class IntegerConverter(BaseIntegerConverter):
    """Modification of the standard IntegerConverter which does not support
    negative values. See
    http://werkzeug.pocoo.org/docs/0.10/routing/#werkzeug.routing.IntegerConverter
    """
    regex = r'-?\d+'


def init_app(app):
    """Initialize the Flask app located in the module sipa.
    This initializes the Flask app by:
    * calling the internal init_app() procedures of each module
    * registering the Blueprints
    * configuring the rotatingFileHandler for loggin
    * registering the Jinja global variables
    :return: None
    """
    init_env_and_config(app)
    logger.debug('Initializing app')
    login_manager.init_app(app)
    babel.init_app(app)
    babel.localeselector(babel_selector)
    cf_pages.init_app(app)

    app.url_map.converters['int'] = IntegerConverter

    from sipa.blueprints import bp_features, bp_usersuite, \
        bp_pages, bp_documents, bp_news, bp_generic

    logger.debug('Registering blueprints')
    app.register_blueprint(bp_generic)
    app.register_blueprint(bp_features)
    app.register_blueprint(bp_usersuite)
    app.register_blueprint(bp_pages)
    app.register_blueprint(bp_documents)
    app.register_blueprint(bp_news)

    if not app.debug:
        app.config.setdefault('LOG_MAX_BYTES', 1024 ** 2)
        app.config.setdefault('LOG_BACKUP_COUNT', 10)
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT'])
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

    from model import query_gauge_data
    logger.debug('Registering Jinja globals')
    app.jinja_env.globals.update(
        cf_pages=cf_pages,
        gauge_data=query_gauge_data,
        get_locale=get_locale,
        possible_locales=possible_locales,
        chart=render_traffic_chart,
        ACTIONS=ACTIONS,
        STATUS_COLORS=STATUS_COLORS
    )

    init_logging(app)
    init_context(app)


@login_manager.user_loader
def load_user(username):
    """Loads a User object from/into the session at every request
    """
    division_name = session.get('division', None)
    if division_name:
        return division_from_name(division_name).user_class.get(username)
    else:
        return AnonymousUserMixin


def babel_selector():
    """Tries to get the language setting from the current session cookie.
    If this fails (if it is not set) it first checks if a language was
    submitted as an argument ('/page?lang=de') and if not, the best matching
    language out of the header accept-language is chosen and set.
    """

    if 'locale' in request.args and Locale(
            request.args['locale']) in possible_locales():
        session['locale'] = request.args['locale']
    elif not session.get('locale'):
        langs = []
        for lang in possible_locales():
            langs.append(lang.language)
        session['locale'] = request.accept_languages.best_match(langs)

    return session.get('locale')
