import os.path
from os import environ
from sipa import app
from sipa.base import init_app

app.config.from_pyfile('default_config.py')

# if local config file exists, load everything into local space.
config_dir = os.getenv('SIPA_CONFIG_DIR', '..')

try:
    app.config.from_pyfile( '{}/config.py'.format(config_dir))
except IOError:
    print("No Config found")

app.config['FLATPAGES_ROOT'] = os.path.join(
os.path.dirname(os.path.abspath(__file__)), 'content')
init_app()

if __name__ == "__main__":
    app.run(debug=True, host="localhost")
