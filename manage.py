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

import importlib
import os
from subprocess import call

from flask.ext.script import Manager, prompt_bool

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


def run_tests_unittest():
    import unittest
    tests = unittest.TestLoader().discover(os.path.join(basedir, 'tests'))
    unittest.TextTestRunner().run(tests)


def run_tests_nose():
    """Check if nosetests is installed and call it.

    If the `nose` package is not available, prompt the user if he
    wants to fall back to the unittest module.
    """
    if importlib.util.find_spec("nose") is None:
        large_message("It You don't have nosetests installed.")
        if not prompt_bool("Shall I fall back to unittest?", default=True):
            print("Aborting.")
        else:
            run_tests_unittest()

        return

    call(["nosetests", "--with-coverage", "--cover-erase", "--cover-branches",
          "--cover-package=sipa"])


@manager.option('-u', '--force-unittest', dest='force_unittest',
                required=False, default=False, action="store_true")
def test(force_unittest):
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

    if not force_unittest:
        run_tests_nose()
    else:
        run_tests_unittest()


if __name__ == '__main__':
    manager.run()
