#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    sipa.py
    ~~~~~~~~~~~~~~

    This file shall be used to start the Flask app. Specific things are handled
    in the `sipa` package.

"""

import argparse
import logging

from sipa import create_app
from sipa.utils import support_hotline_available

logger = logging.getLogger(__name__)
logger.info('Starting sipa...')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sipa launcher")
    parser.add_argument("--debug", action="store_true",
                        help="run Sipa in debug mode")
    parser.add_argument("--exposed", action="store_const", const='0.0.0.0',
                        dest='host', help="expose Sipa on the network")
    parser.add_argument("-p", "--port", action="store",
                        help="tcp port to use", type=int, default=5000)
    args = parser.parse_args()

    def preparation(app):
        if args.debug:
            app.debug = True
            logger.warning('Running in Debug mode')

    app = create_app(prepare_callable=preparation)
    app.run(debug=args.debug, host=args.host, port=args.port)

else:
    # __name__ == 'uwsgi_file_sipa'
    import uwsgi
    debug = uwsgi.opt.get('debug', False)
    app = create_app()
    if debug:
        logger.warning("Running in debug mode")
        app.debug = True
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
    # app will now be used by `uwsgi`

@app.context_processor
def inject_hotline_status():
    return dict(support_hotline_available=support_hotline_available())
