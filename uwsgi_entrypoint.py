#!/usr/bin/env python3
import logging

from sipa import create_app
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.error("This file is not meant to be executed directly. Please use it in uwsgi only.")
else:
    # __name__ == 'uwsgi_file_sipa'
    import uwsgi

    logger.info('Starting sipa...')
    load_dotenv()
    debug = uwsgi.opt.get('debug', False)
    app = create_app()
    if debug:
        logger.warning("Running in debug mode")
        app.debug = True
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
    # app will now be used by `uwsgi`
