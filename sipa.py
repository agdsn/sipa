# -*- coding: utf-8 -*-
"""
    sipa.py
    ~~~~~~~~~~~~~~

    This file shall be used to start the Flask app. Specific things are handled
    in the `sipa` package.

"""

import os.path
import logging.config

from sipa.utils.git_utils import update_repo, init_repo
from sipa import app, logger
from sipa.base import init_app

# todo rework structure
# looking at pycroft, there is a file `server_run.py` whose *only* purpose is to
# start the server and provide the Flask instance.
# since this question is about the project structure, we have to ask the
# following questions for each file:
# * what should this file do / contain?
# * what should this file *not* do but others, such as the `sipa` package?
# the main reason for creating this comment was that the whole project structure
# starts looking messy and uncoordinated to me – pycroft, on the other hand,
# does not have this issue.
# Reasons for this perceived missing coordination are mainly:
# * statements being partly directly in the `.py` files, partly covered by
#   methods, and partly being included in an `if __name__ == '__main__'` as here
# * imports being done mostly on the top of the file, but sometimes in the
#   middle of the code as in `sipa/base.py:94`
# * packages treated as modules – shouldn't all the things to be made publicly
#   be defined (or imported to the namespace) in the `__init__.py`? Although
#   this has been implemented correctly in `blueprints`, this is not the case
#   in `utils`. What are the explicit reasons for `utils` to be structured as a
#   package and *not* a collection of modules, anyway? Since the modules in
#   `utils` consist of many single functions, wouldn't it be quite a lot of work
#   importing it to the `__init.py__`, or is this done via `from x import *`?
# ~~~~~~~~
# Sorry for “wasting” a commit on these things, but I consider them crucial to
# be resolved or explained to me.
# Although many things may have been caused by me not knowing certain things,
# but on the other hand I believe, implicated by the symptoms, there *are*
# things being done wrong in here.
# It is not just some “cosmetic” thing, but something that bothers – or better:
# confuses – me a lot when trying to write code in Sipa.
# For the following discussion, I would appreciate using reference which allow
# me to RTFM heavily.
# ~~~~~~~~
# Sorry for the long text
# lukasjuhrich

# default configuration
app.config.from_pyfile('default_config.py')

# if local config file exists, load everything into local space.
config_dir = os.getenv('SIPA_CONFIG_DIR', '..')
try:
    app.config.from_pyfile('{}/config.py'.format(config_dir))
except IOError:
    print("No Config found")
if app.config['FLATPAGES_ROOT'] == "":
    app.config['FLATPAGES_ROOT'] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'content')

init_repo(app.config["FLATPAGES_ROOT"], app.config['CONTENT_URL'])

if os.getenv("SIPA_UWSGI" ,"False") == 'True':
    import uwsgi
    def update_uwsgi(signum):
        hasToReload = update_repo(app.config["FLATPAGES_ROOT"])
        if hasToReload:
            uwsgi.reload
    uwsgi.register_signal(20, "", update_uwsgi)
    uwsgi.add_cron(20, -5, -1, -1, -1, -1)

init_app()

location_log_config = app.config['LOGGING_CONFIG_LOCATION']

if os.path.isfile(location_log_config):
    logging.config.fileConfig(location_log_config,
                              disable_existing_loggers=True)
    logger.info('Loaded logging configuration file "{}".'
                .format(location_log_config))
else:
    logger.warn('Given LOGGING_CONFIG_LOCATION "{}" is not accessible.'
                .format(location_log_config))


if __name__ == "__main__":
    logger.info('Starting sipa...')
    logger.warning('Running in Debug mode')
    app.run(debug=True, host="0.0.0.0")
