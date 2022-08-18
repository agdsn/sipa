import logging
import os
from abc import ABC
from contextlib import contextmanager

from flask import Flask, url_for
from flask_testing import TestCase as FlaskTestCase

from sipa import create_app, model
from sipa.defaults import WARNINGS_ONLY_CONFIG
from sipa.model.sample.user import User as SampleUser


class TestCase(FlaskTestCase, ABC):
    def assertRedirects(self, response, location, message=None):
        # Dirty hack to cincumvent a bug in Flask-Testing (jarus/flask-testing#154)
        # The modern solution is outlined in
        # https://flask.palletsprojects.com/en/2.1.x/testing/#following-redirects
        # and should be implemented when switching to pytest (see #431)
        if response.location.startswith('/'):
            response.location = f"http://localhost{response.location}"
        super().assertRedirects(response, location, message)

    assert_redirects = assertRedirects


class AppInitialized(TestCase):
    """A frontend test base providing an initialized app.

    This class is based upon :py:class:`flask_testing.TestCase`, which
    provides the attribute ``client`` to be used in tests.

    Configuration of the app is provided by defining the
    :py:meth:`create_app` method.  See it's documentation on how to
    extend the config and set up other things.

    This function contains some helper assert functions as well.
    """
    @property
    def app_config(self):
        return {}

    def create_app(self):
        """Create a new instance of sipa using :py:func:`create_app`

        A new instance of sipa will be executed with the following
        config customizations:

            - SECRET_KEY is set to a random value

            - TESTING is set to True

            - debug is enabled

            - WTF_CSRF_ENABLED is set to False

            - PRESERVE_CONTEXT_ON_EXCEPTION

        This config is extended by the values of the attribute
        :py:attr:`app_config`.
        """
        test_app = Flask('sipa')
        test_app.config['SECRET_KEY'] = os.urandom(100)
        test_app.config['TESTING'] = True
        test_app.config['LOG_CONFIG'] = WARNINGS_ONLY_CONFIG
        test_app.config['WTF_CSRF_ENABLED'] = False
        test_app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        test_app.config['CONTACT_SENDER_MAIL'] = "test@foo.de"
        test_app.debug = True
        return create_app(app=test_app, config=self.app_config)

    @contextmanager
    def temp_set_attribute(self, attr_name, value):
        """Temporarily set an attribute to a certain value.

        Usage:

        >>> with self.temp_set_attribute('longMessage', False):
        ...     assert self.longMessage = True
        ...

        :param str attr_name: The name of the attribute to change
        :param value: The temporary value
        """
        old_value = getattr(self, attr_name)
        setattr(self, attr_name, value)
        yield
        setattr(self, attr_name, old_value)

    def temp_short_log(self):
        return self.temp_set_attribute('longMessage', False)

    def assert_something_flashed(self, data, level='danger'):
        """Assert that something flashed inside the body.

        :param binary data: binary content of the response
        :param str level: the flash level, i.e. one of ['info',
            'success', 'warning', 'danger']
        """
        string_to_find = f"sipa_flash alert alert-{level}"

        with self.temp_short_log():
            self.assertIn(string_to_find.encode('utf-8'), data,
                          msg="Unexpectedly found no flash message"
                          "with level {}!".format(level))

    def assert_nothing_flashed(self, data):
        string_not_to_find = "sipa_flash alert"
        with self.temp_short_log():
            self.assertNotIn(string_not_to_find.encode('utf-8'), data,
                             msg="Flash message found unexpectedly")


def dynamic_frontend_base(backend):
    """Create a test base in which `backend` is enabled

    This returns a subclass of :py:cls:`AppInitialized` with the only
    change that ``'BACKENDS': [backend]`` is added to the config.
    """
    class cls(AppInitialized):
        @property
        def app_config(self):
            return {
                **super().app_config,
                'BACKENDS': [backend],
            }

    return cls


class SampleFrontendTestBase(dynamic_frontend_base('sample')):
    User = SampleUser

    def login(self):
        # raise ValueError("login")
        return self.client.post(
            url_for('generic.login'),
            data={'dormitory': 'localhost',
                  'username': 'test',
                  'password': 'test'},
        )

    @property
    def current_user(self):
        return self.User.get('test')

    def logout(self):
        return self.client.get(
            url_for('generic.logout')
        )


class FormTemplateTestMixin:
    """A Mixin for conveniently testing forms.

    Requires the class to inherit from
    :py:cls:`flask_testing.TestCase` in order to access the assert
    methods.

    Requires the following attributes:

        - client: The flask test client

        - url: The url of the endpoint to test

        - template: The location of the template file, relative to the
          template root
    """
    def submit_form(self, data):
        return self.client.post(self.url, data=data)

    def test_endpoint_reachable(self):
        self.assert200(self.client.get(self.url))
        self.assertTemplateUsed(self.template)

    def test_empty_request_flashes(self):
        resp = self.client.post(self.url)
        self.assert_something_flashed(resp.data)

    def test_invalid_data_flashes(self):
        for data in self.invalid_data:
            with self.subTest(data=data):
                resp = self.submit_form(data=data)
                self.assert_something_flashed(resp.data)

    def test_valid_data_passes(self):
        for data in self.valid_data:
            with self.subTest(data=data):
                resp = self.submit_form(data=data)
                self.assert_nothing_flashed(resp.data)


@contextmanager
def disable_logs(loglevel):
    logging.disable(loglevel)
    yield
    logging.disable(logging.NOTSET)
