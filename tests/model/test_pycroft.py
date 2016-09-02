from unittest import TestCase

from flask import Flask

from sipa.model import Backends
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
