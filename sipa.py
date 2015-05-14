import os.path
import logging.config
from sipa import app, logger
from sipa.base import init_app

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
