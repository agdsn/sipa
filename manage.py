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

from flask_script import Manager, prompt_bool

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
    """Run the unittests with a TextTestRunner, return the exit code."""
    import unittest
    tests = unittest.TestLoader().discover(os.path.join(basedir, 'tests'))
    return unittest.TextTestRunner().run(tests)


def run_tests_nose():
    """Check if nosetests is installed and call it.

    If the `nose` package is not available, prompt the user if he
    wants to fall back to the unittest module.
    """
    if importlib.util.find_spec("nose") is None:
        large_message("It You don't have nosetests installed.")
        if not prompt_bool("Shall I fall back to unittest?", default=True):
            print("Aborting.")
            result = 255
        else:
            result = run_tests_unittest()

        return result

    return call(["nosetests", "--verbose", "--rednose", "--with-coverage",
                 "--cover-erase", "--cover-branches", "--cover-package=sipa"])


@manager.option('-u', '--force-unittest', dest='force_unittest',
                required=False, default=False, action="store_true")
def test(force_unittest):
    """Try to run the tests.

    If Flask-Testing does not exist, a hint is displayed.
    """
    spec = importlib.util.find_spec("flask_testing")
    if spec is None:
        large_message("It seems Flask-Testing is missing. "
                      "Are you sure you are in the "
                      "correct environment?")
        if not prompt_bool("Continue?", default=False):
            print("Aborting.")
            exit(255)

    timeout = os.getenv('CONNETION_TIMEOUT')
    if os.getenv('CONNETION_TIMEOUT'):
        connections = [('postgres', 5432), ('ldap_hss', 389)]
        if not wait_until_ready(connections):
            exit(254)

    if not force_unittest:
        result = run_tests_nose()
    else:
        result = run_tests_unittest()

    exit(result)


def wait_until_ready(connections_to_test, timeout=5):
    """Wait until each connection can be established or the timeout is reached.

    :param connections_to_test: A list of `(host, port)` tuples
    :param timeout: Timeout in seconds
    :return: False if the timeout is reached, True else
    """
    import socket
    import time

    print("Starting connectivity test...")

    print("Given TCP endpoints:",
          " ".join("{}:{}".format(*host_port) for host_port in connections_to_test))

    for conn_tuple in connections_to_test:
        print("Trying to connect to {}:{}...".format(*conn_tuple), end='')
        old_time = time.time()
        while time.time() - old_time < timeout:
            try:
                socket.setdefaulttimeout(timeout)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(conn_tuple)
            except ConnectionRefusedError:
                pass
            else:
                print(" SUCCESS")
                break
        else:
            print(" FAIL")
            break
    else:
        return True

    return False


if __name__ == '__main__':
    manager.run()
