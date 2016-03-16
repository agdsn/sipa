from flask import Flask
from flask.ext.testing import TestCase

from sipa import create_app
from sipa.defaults import WARNINGS_ONLY_CONFIG


class AppInitialized(TestCase):
    def create_app(self, additional_config=None):
        test_app = Flask('sipa')
        test_app.config['TESTING'] = True
        test_app.config['LOG_CONFIG'] = WARNINGS_ONLY_CONFIG
        test_app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        test_app.debug = True
        test_app = create_app(
            app=test_app,
            config=additional_config if additional_config else {},
        )
        return test_app
