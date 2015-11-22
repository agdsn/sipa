# -*- coding: utf-8 -*-
from flask import Flask

from sipa.initialization import init_app


def create_app(app=None, prepare_callable=None):
    app = app if app else Flask(__name__)
    if prepare_callable:
        prepare_callable(app=app)
    init_app(app)
    return app
