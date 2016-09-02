from unittest import TestCase, expectedFailure

from flask import Flask

from sipa.model import Backends
from sipa.model.pycroft import datasource


class PycroftBackendTestCase(TestCase):
    def setUp(self):
        super().setUp()

        app = Flask('test')
        self.backends = Backends()
        self.backends.init_app(app)
        app.config['BACKENDS'] = ['pycroft']
        self.backends.init_backends()

    @expectedFailure
    def test_pycroft_backend_available(self):
        dsrc = self.backends.get_datasource('pycroft')
        self.assertEqual(dsrc, datasource)

    @expectedFailure
    def test_pycroft_only_backend(self):
        self.assertEqual(len(self.backends.datasources), 1)
