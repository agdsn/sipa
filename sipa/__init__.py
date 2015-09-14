# -*- coding: utf-8 -*-
from functools import wraps
from logging import getLogger, LoggerAdapter

from flask import Flask, flash, redirect
from flask.globals import request

from sipa.utils import current_user_name, redirect_url


app = Flask('sipa')


class CustomAdapter(LoggerAdapter):
    """
    Custom LoggingAdapter to prepend the current unixlogin and IP to the log
    if possible
    """
    def process(self, msg, kwargs):
        extra = kwargs.pop('extra', {})
        tags = extra.pop('tags', {})
        if request:
            login = current_user_name()
            tags['user'] = login
            tags['ip'] = request.remote_addr
            extra['tags'] = tags
            kwargs['extra'] = extra
            if app.config['GENERIC_LOGGING']:
                return msg, kwargs
            else:
                return '{} - {} - {}'.format(
                    request.remote_addr,
                    login,
                    msg), kwargs
        else:
            return msg, kwargs


logger = CustomAdapter(logger=getLogger(name=__name__), extra={})
http_logger = getLogger(name='{}.http'.format(__name__))    # 'sipa.http'


def feature_required(needed_feature, given_features):
    """A decorator used to disable functions (routes) if a certain feature
    is not provided by the User class.

    given_features has to be a callable to ensure runtime distinction
    between divisions.

    :param needed_feature: The feature needed
    :param given_features: A callable returning the set of supported features
    :return:
    """
    def feature_decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if needed_feature in given_features():
                return func(*args, **kwargs)
            else:
                def not_supported():
                    flash(u"Diese Funktion ist nicht verfügbar.", 'error')
                    return redirect(redirect_url())
                return not_supported()

        return decorated_view
    return feature_decorator
