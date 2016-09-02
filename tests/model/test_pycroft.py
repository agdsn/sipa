from unittest import TestCase

from flask import Flask

from sipa.model import Backends
from sipa.model.fancy_property import PropertyBase
from sipa.model.pycroft import datasource
from sipa.model.user import BaseUser


class PycroftBackendTestCase(TestCase):
    def setUp(self):
        super().setUp()

        app = Flask('test')
        self.backends = Backends()
        app.config['BACKENDS'] = ['pycroft']
        self.backends.init_app(app)
        self.backends.init_backends()

    def test_pycroft_backend_available(self):
        dsrc = self.backends.get_datasource('pycroft')
        self.assertEqual(dsrc, datasource)

    def test_pycroft_only_backend(self):
        self.assertEqual(len(self.backends.datasources), 1)


class PycroftUserClassInheritanceTestCase(TestCase):
    """Ckheck whether the pycroft user class complies with our API.

    This should be refactored so that any arbitrary user class can be
    tested in the same way.
    """
    def setUp(self):
        super().setUp()
        self.User = datasource.user_class

    def test_user_instanciable(self):
        self.User(uid=0)

    def test_user_inherits_from_baseuser(self):
        self.assertTrue(issubclass(self.User, BaseUser))

    def test_user_datasource_is_pycroft(self):
        self.assertEqual(self.User.datasource, datasource)


class PropertyTestMixin(TestCase):
    def assert_is_fancy_property(self, prop):
        self.assertIsInstance(prop, PropertyBase)

    def assert_property_empty(self, prop):
        if not prop.empty:
            self.fail("Property {!r} is not empty".format(prop))

    def assert_property_not_empty(self, prop):
        if prop.empty:
            self.fail("Property {!r} unexpectedly empty".format(prop))

    def assert_property_supported(self, prop):
        if not prop.supported:
            self.fail("Property {!r} unexpectedly not supported".format(prop))

    def assert_property_unsupported(self, prop):
        if prop.supported:
            self.fail("Property {!r} unexpectedly supported".format(prop))


class PycroftUserClassTestCase(PropertyTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()
        self.all_properties = ['id', 'status', 'login', 'mac', 'mail', 'address',
                               'hostname', 'hostalias', 'finance_balance', 'realname']
        self.supported = ['status', 'login', 'mac', 'address', 'realname']
        self.unsupported = ['id', 'mail', 'finance_balance', 'hostname', 'hostalias']

    @staticmethod
    def create_user():
        return datasource.user_class(uid=0)

    def test_things_are_fancy_properties(self):
        for prop in self.all_properties:
            with self.subTest(prop=prop):
                self.assert_is_fancy_property(getattr(self.user, prop))

    def test_supported_properties(self):
        for prop in self.supported:
            with self.subTest(prop=prop):
                self.assert_property_supported(getattr(self.user, prop))

    def test_unsupported_properties(self):
        for prop in self.unsupported:
            with self.subTest(prop=prop):
                self.assert_property_unsupported(getattr(self.user, prop))

    def test_user_cannot_change_password(self):
        self.assertFalse(self.user.can_change_password)

    def test_user_password_change_raises(self):
        with self.assertRaises(NotImplementedError):
            self.user.change_password(None, None)

