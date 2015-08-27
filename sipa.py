# -*- coding: utf-8 -*-
"""
    sipa.py
    ~~~~~~~~~~~~~~

    This file shall be used to start the Flask app. Specific things are handled
    in the `sipa` package.

"""

from sipa import app, logger
from sipa.base import init_app


init_app(app)
logger.info('Starting sipa...')
logger.warning('Running in Debug mode')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
