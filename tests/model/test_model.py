from base64 import urlsafe_b64encode
from os import urandom
from unittest import TestCase

from ipaddress import IPv4Network
from flask import Flask

from sipa.model import Backends
from sipa.model.datasource import DataSource, Dormitory
from sipa.model.default import BaseUser


class TestBackendInitializationCase(TestCase):
    def setUp(self):
        super().setUp()
        self.app = Flask('sipa')
        self.app.config['BACKENDS'] = ['foo']
        datasource = DataSource(
            name='foo',
            user_class=object,
            mail_server="",
            webmailer_url="",
            support_mail="",
            init_context=lambda app: None
        )

        Dormitory(name='test', display_name="",
                  datasource=datasource, subnets=[IPv4Network('127.0.0.0/8')])

        self.backends = Backends(available_datasources=[datasource])
        self.backends.init_app(self.app)
        self.backends.init_backends()

    def test_extension_registrated(self):
        assert 'backends' in self.app.extensions

    def test_datasource_names_unique(self):
        names = [dsrc.name for dsrc in self.backends.datasources]
        self.assertEqual(len(names), len(set(names)))

    def test_dormitory_names_unique(self):
        names = [dorm.name for dorm in self.backends.dormitories]
        self.assertEqual(len(names), len(set(names)))

    def test_all_dormitories_names_unique(self):
        names = [dorm.name for dorm in self.backends.all_dormitories]
        self.assertEqual(len(names), len(set(names)))

    def test_all_dormitories_greater(self):
        assert (set(self.backends.all_dormitories) >=
                set(self.backends.dormitories))

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
            self.backends.dormitories_short,
            self.backends.all_dormitories,
        )

    def test_supported_dormitories_list(self):
        self.assert_dormitories_namelist(
            self.backends.supported_dormitories_short,
            self.backends.dormitories,
        )

    def test_get_dormitory(self):
        for dormitory in self.backends.dormitories:
            self.assertEqual(self.backends.get_dormitory(dormitory.name),
                             dormitory)

        possible_names = [
            dorm.name for dorm in self.backends.dormitories
        ]

        for str_length in range(10):
            random_string = None
            while random_string in possible_names:
                random_string = urlsafe_b64encode(urandom(str_length))

            assert self.backends.get_dormitory(random_string) is None

    def test_dormitory_from_ip(self):
        for dorm in self.backends.dormitories:
            first_ip = next(dorm.subnets.subnets[0].hosts())

            self.assertEqual(self.backends.dormitory_from_ip(first_ip), dorm)

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
