from logging import getLogger, LoggerAdapter

from flask import Flask
from flask.ext.login import current_user
from flask.globals import request

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
            login = 'anonymous'
            if current_user.is_authenticated():
                login = current_user.uid
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
