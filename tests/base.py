import os
from contextlib import contextmanager
from functools import wraps

from flask import Flask
from flask_testing import TestCase

from sipa import create_app
from sipa.defaults import WARNINGS_ONLY_CONFIG


class AppInitialized(TestCase):
    """A frontend test base providing an initialized app.

    This class is based upon :py:class:`flask_testing.TestCase`, which
    provides the attribute ``client`` to be used in tests.

    Configuration of the app is provided by defining the
    :py:meth:`create_app` method.  See it's documentation on how to
    extend the config and set up other things.

    This function contains some helper assert functions as well.
    """
    def create_app(self, additional_config=None):
        """Create a new instance of sipa using

        A new instance of sipa will be executed with the following
        config customizations:

            - SECRET_KEY is set to a random value

            - TESTING is set to True

            - debug is enabled

            - WTF_CSRF_ENABLED is set to False

            - PRESERVE_CONTEXT_ON_EXCEPTION

        :param dict additional_config: a dict of additional config
            values taking precedence of what has ben set before.  This
            argument can be used when subclassing by calling ``super()``
            with the desired config.
        """
        test_app = Flask('sipa')
        test_app.config['SECRET_KEY'] = os.urandom(100)
        test_app.config['TESTING'] = True
        test_app.config['LOG_CONFIG'] = WARNINGS_ONLY_CONFIG
        test_app.config['WTF_CSRF_ENABLED'] = False
        test_app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        test_app.debug = True
        test_app = create_app(
            app=test_app,
            config=additional_config if additional_config else {},
        )
        return test_app

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
        string_to_find = "sipa_flash alert alert-{}".format(level)

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
        def create_app(self, *a, **kw):
            config = {
                **kw.pop('additional_config', {}),
                'BACKENDS': [backend],
            }
            return super().create_app(additional_config=config)

    return cls


SampleFrontendTestBase = dynamic_frontend_base('sample')
WuFrontendTestBase = dynamic_frontend_base('wu')
HssFrontendTestBase = dynamic_frontend_base('hss')
GerokFrontendTestBase = dynamic_frontend_base('gerok')


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


class TestWhenSubclassedMeta(type):
    """Metaclass that sets `__test__` back to `True` when subclassed.

    Usage:

        >>> class GenericTestCase(TestCase, metaclass=TestWhenSubclassed):
        ...     __test__ = False
        ...
        ...     def test_something(self):
        ...         self.fail("This test is executed in a subclass, only.")
        ...
        ...
        >>> class SpecificTestCase(GenericTestCase):
        ...     pass

    """

    def __new__(mcs, name, bases, attrs):
        ATTR_NAME = '__test__'
        VALUE_TO_RESET = False
        RESET_VALUE = True

        values = [getattr(base, ATTR_NAME) for base in bases
                  if hasattr(base, ATTR_NAME)]

        # only reset if the first attribute is `VALUE_TO_RESET`
        try:
            first_value = values[0]
        except IndexError:
            pass
        else:
            if first_value == VALUE_TO_RESET and ATTR_NAME not in attrs:
                attrs[ATTR_NAME] = RESET_VALUE

        return super().__new__(mcs, name, bases, attrs)


class subtests_over:
    def __init__(self, attr_name, getter=None):
        #: The function taking ``inst.attr`` and extracting the
        #: iterable of params iterable
        self.getter = getter
        self.attr_name = attr_name

    def __call__(self, func):
        @wraps(func)
        def _func(inst):
            params = (self.getter(getattr(inst, self.attr_name)) if self.getter
                      else getattr(inst, self.attr_name))

            for param in params:
                with inst.subTest(param=param):
                    func(inst, param)

        return _func
