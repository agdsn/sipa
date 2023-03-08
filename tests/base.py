import logging
from abc import ABC
from contextlib import contextmanager

from flask_testing import TestCase as FlaskTestCase


class TestCase(FlaskTestCase, ABC):
    def assertRedirects(self, response, location, message=None):
        # Dirty hack to cincumvent a bug in Flask-Testing (jarus/flask-testing#154)
        # The modern solution is outlined in
        # https://flask.palletsprojects.com/en/2.1.x/testing/#following-redirects
        # and should be implemented when switching to pytest (see #431)
        if response.location.startswith('/'):
            response.location = f"http://localhost{response.location}"
        super().assertRedirects(response, location, message)

    assert_redirects = assertRedirects


@contextmanager
def disable_logs(loglevel):
    logging.disable(loglevel)
    yield
    logging.disable(logging.NOTSET)
