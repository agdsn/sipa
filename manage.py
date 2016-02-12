"""Python helper for generic sipa tasks

The purpose of this module is to provide a generic interface of
often-used functions which usually require some sort of setup or are
accessible at many different locations.

It somewhat is like a makefile, but the usage of Flask-Script makes
the usage of python-like commands (run unittests, run the app,
configure the app, make the translations, etc.pp.) easier.

Usage:

$ python manage.py <command>
$ python manage.py test

"""

import os

from flask.ext.script import Manager

from sipa import create_app


basedir = os.path.dirname(os.path.abspath(__file__))

manager = Manager(create_app)


def large_message(message, title="INFO", width=80, fill='='):
            print("\n{0:{fill}^{width}}\n{1}\n".format(
                title.upper(),
                message,
                fill=fill,
                width=width,
            ))


@manager.command
def test():
    """Try to run the tests.

    If Flask-Testing does not exist, a hint is displayed.
    """
    try:
        import flask.ext.testing  # noqa
    except ImportError:

        large_message("It seems Flask-Testing is missing. "
                      "Are you sure you are in the "
                      "correct environment?")
        raise

    import unittest
    tests = unittest.TestLoader().discover(os.path.join(basedir, 'tests'))
    unittest.TextTestRunner().run(tests)


if __name__ == '__main__':
    manager.run()
