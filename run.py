import os.path
from sipa import app
from sipa.base import init_app

app.config.from_pyfile('config.py')

app.config['FLATPAGES_ROOT'] = os.path.join(
os.path.dirname(os.path.abspath(__file__)), 'content')
init_app()

if __name__ == "__main__":
    app.run(debug=True, host="localhost")
