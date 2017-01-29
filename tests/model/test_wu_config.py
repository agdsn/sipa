from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import Flask

from sipa.model.wu.database_utils import init_atlantis, init_userdb, init_db
from sipa.utils.exceptions import InvalidConfiguration
from sipa.model import Backends


class WuInitializationTestBase(TestCase):
    def setUp(self):
        super().setUp()
        self.app = Flask('sipa')
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        Backends.backends_preinit(self.app)


class InitAtlantisTestCase(WuInitializationTestBase):
    KEYS = {
        'DB_USERMAN_URI': 'userman',
        'DB_NETUSERS_URI': 'netusers',
        'DB_TRAFFIC_URI': 'traffic',
    }

    def test_unconfigured_init_fails(self):
        with self.assertRaises(InvalidConfiguration):
            init_atlantis(self.app)

    def test_incomplete_config_fails(self):
        for key in self.KEYS.keys():
            with self.subTest(key=key), \
                 self.assertRaises(InvalidConfiguration):
                print("key:", key)
                self.app.config[key] = "sqlite:///"
                init_atlantis(self.app)

            del self.app.config[key]

    def test_complete_config_sets_correct_bindings(self):
        self.app.config.update(**{conf_key: "sqlite:///" for conf_key in self.KEYS})
        init_atlantis(self.app)

        for bind_key in self.KEYS.values():
            self.assertIn(bind_key, self.app.config['SQLALCHEMY_BINDS'])


class InitUserDBTestCase(WuInitializationTestBase):
    KEYS = {
        'DB_HELIOS_USER': 'sipa',
        'DB_HELIOS_PASSWORD': 'apis',
        'DB_HELIOS_HOST': 'localhost',
        'DB_HELIOS_PORT': '3306',
        'SQL_TIMEOUT': 5,
    }

    def test_unconfigured_init_fails(self):
        with self.assertRaises(InvalidConfiguration):
            init_userdb(self.app)

    def test_complete_config_sets_extension(self):
        self.app.config.update(**self.KEYS)
        init_userdb(self.app)

        self.assertIn('db_helios', self.app.extensions)


class InitDBTestCase(WuInitializationTestBase):
    """Test Case for the cumulated `init_db` function"""
    def raise_invalid_conf(*a, **kw):
        raise InvalidConfiguration()

    def setUp(self):
        super().setUp()
        self.init_atlantis = MagicMock()
        self.init_userdb = MagicMock()
        self.init_atlantis_bad = MagicMock(side_effect=self.raise_invalid_conf)
        self.init_userdb_bad = MagicMock(side_effect=self.raise_invalid_conf)
        self.expected_call = ('', (self.app,), {})

    def test_subinits_called(self):
        """Test that `init_atlantis` and `init_userdb` get called correctly"""

        with patch('sipa.model.wu.database_utils.init_userdb', self.init_userdb), \
                patch('sipa.model.wu.database_utils.init_atlantis', self.init_atlantis):
            init_db(self.app)

        self.assertEqual(self.init_atlantis.call_args, self.expected_call)
        self.assertEqual(self.init_userdb.call_args, self.expected_call)

    def test_userdb_raising_passes(self):
        """Test that `init_userdb` raising `InvalidConfiguration` get's skipped"""
        with patch('sipa.model.wu.database_utils.init_userdb', self.init_userdb_bad), \
                patch('sipa.model.wu.database_utils.init_atlantis',
                      self.init_atlantis):
            try:
                init_db(self.app)
            except InvalidConfiguration:
                self.fail("InvalidConfiguration has been raised unexpectedly")

    def test_atlantis_raising_fails(self):
        """Test that raising in `init_atlantis` doesn't get caught"""
        with patch('sipa.model.wu.database_utils.init_userdb', self.init_userdb_bad), \
                patch('sipa.model.wu.database_utils.init_atlantis',
                      self.init_atlantis_bad), \
                self.assertRaises(InvalidConfiguration):
            init_db(self.app)
