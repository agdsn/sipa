import json
from base64 import urlsafe_b64encode
from itertools import chain
from os import urandom
from requests import Response
from unittest import TestCase
from unittest.mock import MagicMock, patch

import sipa.model.sample
from flask import Flask
from flask.ext.testing import TestCase as FlaskTestCase
from sipa.model import (dormitory_from_ip, dormitory_from_name,
                        init_datasources_dormitories, list_all_dormitories,
                        list_supported_dormitories)
from sipa.model.default import BaseUser
from sipa.model.property import (ActiveProperty, Capabilities,
                                 UnsupportedProperty, no_capabilities)
from sipa.model.gerok.user import do_api_call
from tests.prepare import AppInitialized


class TestUninitializedBackendCase(FlaskTestCase):
    def create_app(self):
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        test_app.debug = True
        return test_app

    def test_datasources_not_registered(self):
        assert 'datasources' not in self.app.extensions

    def test_dormitories_not_registered(self):
        assert 'dormitories' not in self.app.extensions

    def test_all_dormitories_not_registered(self):
        assert 'all_dormitories' not in self.app.extensions


class TestNoDebugBackends(FlaskTestCase):
    def create_app(self):
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        init_datasources_dormitories(test_app)
        return test_app

    def test_no_debug_backends(self):
        assert not any(
            dsrc.debug_only for dsrc in self.app.extensions['datasources']
        )
        assert not any(
            dorm.datasource.debug_only
            for dorm in self.app.extensions['dormitories']
        )


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


class TestSampleUserCase(AppInitialized):
    expected_result = {
        # 'attr_name': ('key_in_sample_dict', Capabilities())
        'realname': ('name', no_capabilities),
        'login': ('uid', no_capabilities),
        'mac': ('mac', Capabilities(edit=True, delete=False)),
        'mail': ('mail', Capabilities(edit=True, delete=True)),
        'address': ('address', no_capabilities),
        'ips': ('ip', no_capabilities),
        'status': ('status', no_capabilities),
        'id': ('id', no_capabilities),
        'hostname': ('hostname', no_capabilities),
        'hostalias': ('hostalias', no_capabilities),
    }

    rows = expected_result.keys()

    def setUp(self):
        self.User = sipa.model.sample.datasource.user_class
        self.user = self.User('test')
        self.sample_users = self.app.extensions['sample_users']

    def test_uid_not_accepted(self):
        with self.assertRaises(KeyError):
            self.User(0)

    def test_uid_correct(self):
        self.assertEqual(self.user.uid, self.sample_users['test']['uid'])

    def test_row_getters(self):
        """Test if the basic properties have been implemented accordingly.
        """

        for key, val in self.expected_result.items():
            if val:
                self.assertEqual(
                    getattr(self.user, key),
                    ActiveProperty(
                        name=key,
                        value=self.sample_users['test'][val[0]],
                        capabilities=val[1],
                    ),
                )
            else:
                self.assertEqual(
                    getattr(self.user, key),
                    UnsupportedProperty(key),
                )

        self.assertEqual(self.user.userdb_status,
                         UnsupportedProperty('userdb_status'))

    def test_row_setters(self):
        for attr in self.rows:
            class_attr = getattr(self.user.__class__, attr)

            if class_attr.fset:
                value = "given_value"
                setattr(self.user, attr, value)
                self.assertEqual(getattr(self.user, attr).value, value)
            elif not getattr(self.user, attr).capabilities.edit:
                assert not class_attr.fset

    def test_row_deleters(self):
        for attr in self.rows:
            class_attr = getattr(self.user.__class__, attr)

            if class_attr.fdel:
                delattr(self.user, attr)
                assert not getattr(self.user, attr).raw_value
                assert getattr(self.user, attr).empty

            elif not getattr(self.user, attr).capabilities.delete:
                assert not class_attr.fdel

    def test_correct_password(self):
        user = self.User('test')
        # TODO: check authenticate
        user.re_authenticate(
            self.sample_users['test']['password']
        )

    def test_credit_valid(self):
        """check whether the credit is positive and below 63GiB.
        """
        assert 0 <= self.user.credit <= 1024**2 * 63

    def test_traffic_history(self):
        for day in self.user.traffic_history:
            assert 0 <= day['day'] <= 6
            assert 0 <= day['input']
            assert 0 <= day['output']
            self.assertEqual(day['throughput'], day['input'] + day['output'])
            assert 0 <= day['credit'] <= 1024**2 * 63


def mocked_gerok_api(status_code=200, response=b""):
    get = MagicMock()

    get.return_value = Response()
    get().status_code = status_code
    get()._content = response

    return get


class TestGerokApiCall(AppInitialized):
    get = mocked_gerok_api()
    post = mocked_gerok_api()
    url = "supersecret.onion"

    def setUp(self):
        self.app.extensions['gerok_api']['token'] = ""
        self.app.extensions['gerok_api']['endpoint'] = self.url
        self.get.reset_mock()
        self.post.reset_mock()

    @patch('requests.get', get)
    def test_empty_request(self):
        self.assertEqual(do_api_call(""), "")
        assert self.get.called

    @patch('requests.get', get)
    def test_not_200_ValueError(self):
        # loop over a lot of status codes except 200
        for status in chain(range(0, 200, 20), range(201, 600, 20)):
            self.get.reset_mock()
            self.get().status_code = status

            with self.assertRaises(ValueError):
                do_api_call("")

            assert self.get.called

    @patch('requests.get', get)
    def test_correct_url_called(self):
        do_api_call("")

        # assert that the call only got the positional args `(self.url,)`
        self.assertEqual(self.get.call_args[0], (self.url,))

    @patch('requests.get', get)
    def test_json_parsed(self):
        sample_dicts = [
            {},
            {'foo': 'bar'},
            {'foo': 'bar', 'dict': {'baz': 'shizzle'}, 'int': 2},
        ]
        for d in sample_dicts:
            self.get()._content = json.dumps(d).encode()
            self.assertEqual(do_api_call(""), d)

    @patch('requests.get', get)
    @patch('requests.post', post)
    def test_post_called(self):
        do_api_call("", method='post', postdata=None)
        self.get.assert_not_called()
        self.assertEqual(self.post.called, True)

    @patch('requests.get', get)
    @patch('requests.post', post)
    def test_invalid_method(self):
        for method in ['GET', 'POST', 'nothing_of_both', 'something_else']:
            with self.assertRaises(ValueError):
                do_api_call("", method=method, postdata=None)
            self.get.assert_not_called()
            self.post.assert_not_called()


