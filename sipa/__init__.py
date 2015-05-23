from logging import getLogger, LoggerAdapter

from flask import Flask
from flask.globals import request
from sipa.utils import current_user_name

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
