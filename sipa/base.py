#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import


from babel import Locale

from flask import request, session
from flask.ext.babel import get_locale
from flask.ext.login import LoginManager

from sipa import app, logger
from sipa.babel import babel, possible_locales
from sipa.flatpages import cf_pages
from sipa.utils.graph_utils import render_traffic_chart
from sipa.utils.ldap_utils import User

from werkzeug.routing import IntegerConverter as BaseIntegerConverter


login_manager = LoginManager()


class IntegerConverter(BaseIntegerConverter):
    """Modification of the standard IntegerConverter which does not support
    negative values. See
    http://werkzeug.pocoo.org/docs/0.10/routing/#werkzeug.routing.IntegerConverter
    """
    regex = r'-?\d+'


app.url_map.converters['int'] = IntegerConverter


def init_app():
    """Initialize the Flask app located in the module sipa.
    This initializes the Flask app by:
    * calling the internal init_app() procedures of each module
    * registering the Blueprints
    * configuring the rotatingFileHandler for loggin
    * registering the Jinja global variables
    :return: None
    """
    logger.debug('Initializing app')
    login_manager.init_app(app)
    babel.init_app(app)
    babel.localeselector(babel_selector)
    cf_pages.init_app(app)

    # todo rethink imports here. These are kind of awkward.
    # I am quite sceptical looking at imports in the middle of the code -
    # not to mention that part “hanging” at the end of this function.
    # importing something just to execute some initializing code like in
    # `import sipa.views` is bad practice. If things need to be done
    # initially, one should make a method for this.
    from sipa.blueprints import bp_features, bp_usersuite, \
        bp_pages, bp_documents, bp_news

    logger.debug('Registering blueprints')
    app.register_blueprint(bp_features)
    app.register_blueprint(bp_usersuite)
    app.register_blueprint(bp_pages)
    app.register_blueprint(bp_documents)
    app.register_blueprint(bp_news)

    if not app.debug:
        # todo what's being done here with logging?
        # I thought logging should be handled *centrally* in the
        # default_log_config?
        # and why should we use a rotatingFileHandler? Sipa is going to run
        # in an isolated docker container. the only things making sense to me
        # would be stdout and streamhandlers.
        app.config.setdefault('LOG_MAX_BYTES', 1024**2)
        app.config.setdefault('LOG_BACKUP_COUNT', 10)
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT'])
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

    from sipa.utils.database_utils import query_gauge_data
    logger.debug('Registering Jinja globals')
    app.jinja_env.globals.update(
        cf_pages=cf_pages,
        gauge_data=query_gauge_data,
        get_locale=get_locale,
        possible_locales=possible_locales,
        chart=render_traffic_chart,
    )
    import sipa.views


@login_manager.user_loader
def load_user(username):
    """Loads a User object from/into the session at every request
    """
    return User.get(username)


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
