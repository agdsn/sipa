from unittest import TestCase
from prepare import AppInitialized

from model.default import BaseUser
import model.sample
from model.property import UnsupportedProperty


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

    def setUp(self):
        self.User = model.sample.datasource.user_class
        self.user = self.User('test')
        self.sample_users = self.app.extensions['sample_users']

    def test_uid_not_accepted(self):
        with self.assertRaises(KeyError):
            self.User(0)

    def test_uid_correct(self):
        self.assertEqual(self.user.uid, self.sample_users['test']['uid'])

    def test_row_properties(self):
        """Test if the basic properties have been implemented accordingly.
        """

        # TODO: implement custom asserton for user
        data = self.app.extensions['sample_users']['test']

        # TODO: check the whole Property, not just .value
        self.assertEqual(self.user.realname.value, data['name'])
        self.assertEqual(self.user.login.value, data['uid'])
        self.assertEqual(self.user.mac.value, data['mac'])
        self.assertEqual(self.user.mail.value, data['mail'])
        self.assertEqual(self.user.address.value, data['address'])
        self.assertEqual(self.user.ips.value, data['ip'])
        self.assertEqual(self.user.status.value, "OK")
        self.assertEqual(self.user.id.value, data['id'])
        self.assertEqual(self.user.hostname.value, data['hostname'])
        self.assertEqual(self.user.hostalias.value, data['hostalias'])
        self.assertEqual(self.user.userdb_status,
                         UnsupportedProperty('userdb_status'))

    def test_correct_password(self):
        user = self.User('test')
        # TODO: check authenticate
        user.re_authenticate(
            self.sample_users['test']['password']
        )

    def test_credit_valid(self):
        """check whether the credit is positive and below 63GiB.
        """
        assert 0 <= self.user.credit <= 1024 * 63

    def test_traffic_history(self):
        for day in self.user.traffic_history:
            assert 0 <= day['day'] <= 6
            assert 0 <= day['input']
            assert 0 <= day['output']
            self.assertEqual(day['throughput'], day['input'] + day['output'])
            assert 0 <= day['credit'] <= 1024 * 63

    # TODO: generically check whether the setter works
    # (by using the capabilities :O)
