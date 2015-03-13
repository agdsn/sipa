import os.path
from sektionsweb.app import app, init_app

if __name__ == "__main__":
    app.config.from_pyfile('settings.py')
    app.config['FLATPAGES_ROOT'] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'content')
    init_app()
    app.run(debug=True, host="localhost")
