from flask import Flask

from sipa.initialization import init_app


def create_app(app=None, **kwargs):
    app = app if app else Flask(__name__)
    init_app(app, **kwargs)
    return app
