from base64 import urlsafe_b64encode
from os import urandom
from unittest import TestCase

from flask import Flask
from flask_testing import TestCase as FlaskTestCase

from sipa.model import (dormitory_from_ip, dormitory_from_name,
                        init_datasources_dormitories, list_all_dormitories,
                        list_supported_dormitories)
from sipa.model.default import BaseUser
from tests.prepare import AppInitialized


class TestUninitializedBackendCase(FlaskTestCase):
    def create_app(self):
        test_app = Flask('sipa')
        test_app.config['TESTING'] = True
        test_app.debug = True
        return test_app

    def test_datasources_not_registered(self):
        assert 'datasources' not in self.app.extensions

    def test_dormitories_not_registered(self):
        assert 'dormitories' not in self.app.extensions

    def test_all_dormitories_not_registered(self):
        assert 'all_dormitories' not in self.app.extensions


class TestBackendInitializationCase(AppInitialized):
    def test_extensions_registrated(self):
        assert 'datasources' in self.app.extensions
        assert 'dormitories' in self.app.extensions
        assert 'all_dormitories' in self.app.extensions

    def test_datasource_names_unique(self):
        names = [dsrc.name for dsrc in self.app.extensions['datasources']]
        self.assertEqual(len(names), len(set(names)))

    def test_dormitory_names_unique(self):
        names = [dorm.name for dorm in self.app.extensions['dormitories']]
        self.assertEqual(len(names), len(set(names)))

    def test_all_dormitories_names_unique(self):
        names = [dorm.name for dorm in self.app.extensions['all_dormitories']]
        self.assertEqual(len(names), len(set(names)))

    def test_all_dormitories_greater(self):
        assert (set(self.app.extensions['all_dormitories']) >=
                set(self.app.extensions['dormitories']))

    def assert_dormitories_namelist(self, list, base):
        """Asserts whether the list consists of (str, str) tuples

        …and has the correct length
        """
        self.assertEqual(len(list), len(base))
        for name, display_name in list:
            assert isinstance(name, str)
            assert isinstance(display_name, str)

    def test_all_dormitories_list(self):
        self.assert_dormitories_namelist(
            list_all_dormitories(),
            self.app.extensions['all_dormitories'],
        )

    def test_supported_dormitories_list(self):
        self.assert_dormitories_namelist(
            list_supported_dormitories(),
            self.app.extensions['dormitories'],
        )

    def test_dormitory_from_name(self):
        for dormitory in self.app.extensions['dormitories']:
            self.assertEqual(dormitory_from_name(dormitory.name),
                             dormitory)

        possible_names = [
            dorm.name for dorm in self.app.extensions['dormitories']
        ]

        for str_length in range(10):
            random_string = None
            while random_string in possible_names:
                random_string = urlsafe_b64encode(urandom(str_length))

            assert dormitory_from_name(random_string) is None

    def test_dormitory_from_ip(self):
        for dorm in self.app.extensions['dormitories']:
            first_ip = next(dorm.subnets.subnets[0].hosts())

            self.assertEqual(dormitory_from_ip(first_ip), dorm)

        # TODO: Find an ip not in any dormitory


class TestBaseUserCase(TestCase):
    def test_BaseUser_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseUser('')

    def test_BaseUser_has_flask_login_properties(self):
        assert BaseUser.is_authenticated
        assert BaseUser.is_active
        assert not BaseUser.is_anonymous

    # more can't be done here, we need some instances.
