from itertools import combinations
from unittest import TestCase

from flask import Flask

from sipa.model import Backends
from sipa.model.gerok import datasource
from sipa.utils.exceptions import InvalidConfiguration


class DatasourceTestBase(TestCase):
    def setUp(self):
        super().setUp()
        # take an empty app and see it throws shit when configuring.
        self.app = Flask(__name__)

    def assert_invalid_config(self):
        """Test whether something fails with an exception.

        :return: A ContextManager like `self.assertRaises`
        """
        return self.assertRaises(InvalidConfiguration)

    def assert_incomplete_config_keys_raise(self, needed_keys, callable):
        self.invalid_combinations = []
        for l in range(len(needed_keys)):
            self.invalid_combinations += combinations(needed_keys, l)

        for keys in self.invalid_combinations:
            self.app.config = {key: None for key in keys}
            with self.subTest(keys=keys), \
                    self.assert_invalid_config():
                self.datasource.init_context(self.app)

            for key in keys:
                self.app.config.pop(key)


class GerokDatasourceConfigTestCase(DatasourceTestBase):
    def setUp(self):
        super().setUp()
        self.datasource = datasource

    def test_bad_configuration_raises(self):
        keys = ['GEROK_ENDPOINT', 'GEROK_API_TOKEN']

        def try_init():
            self.datasource.init_context(self.app)
        self.assert_incomplete_config_keys_raise(needed_keys=keys)


class GerokDatasourceTestBase(DatasourceTestBase):
    def setUp(self):
        super().setUp()
        self.datasource = datasource

        self.app.config.update({
            'GEROK_ENDPOINT': None,
            'GEROK_API_TOKEN': None,
            'BACKENDS': ['gerok']
        })

        # create app with corresponding backends?
        self.backends = Backends()
        self.backends.init_app(self.app)


class GerokDatasourceTestCase(GerokDatasourceTestBase):
    def test_gerok_in_datasources(self):
        self.assertEqual(self.backends.datasources, [self.datasource])

    def test_backends_init(self):
        self.backends.init_backends()
