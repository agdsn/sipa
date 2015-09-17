# -*- coding: utf-8 -*-
"""
    sipa.py
    ~~~~~~~~~~~~~~

    This file shall be used to start the Flask app. Specific things are handled
    in the `sipa` package.

"""

import argparse
from sipa import app
from sipa.initialization import init_app

import logging
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sipa launcher")
    parser.add_argument("--debug", action="store_true",
                        help="run Sipa in debug mode")
    parser.add_argument("--exposed", action="store_const", const='0.0.0.0',
                        dest='host', help="expose Sipa on the network")
    parser.add_argument("-p", "--port", action="store",
                        help="tcp port to use", type=int, default=5000)
    args = parser.parse_args()

    logger.info('Starting sipa...')
    if args.debug:
        app.debug = True
        logger.warning('Running in Debug mode')

    init_app(app)
    app.run(debug=args.debug, host=args.host, port=args.port)

else:
    init_app(app)
