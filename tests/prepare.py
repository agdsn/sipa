from flask import Flask
from flask.ext.testing import TestCase
from sipa import create_app


class AppInitialized(TestCase):
    @classmethod
    def create_app(cls):
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        test_app.debug = True
        test_app = create_app(app=test_app)
        return test_app
