from unittest import TestCase

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation


class TestBaseUserCase(TestCase):
    def test_BaseUser_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseUser('')

    def test_BaseUser_has_flask_login_properties(self):
        assert BaseUser.is_authenticated
        assert BaseUser.is_active
        assert not BaseUser.is_anonymous

    # more can't be done here, we need some instances.


class DegenerateUser(BaseUser):
    address = None
    authenticate = None
    can_change_password = None
    change_password = None
    credit = None
    finance_information = None
    from_ip = None
    get = None
    has_connection = None
    hostalias = None
    hostname = None
    id = None
    login = None
    mac = None
    mail = None
    realname = None
    status = None
    traffic_history = None
    userdb = None
    userdb_status = None


class DegenerateUserTestCase(TestCase):
    User = DegenerateUser

    def test_instantiable(self):
        self.User(uid='')

    def test_finance_balance_unsupported(self):
        bal = self.User(uid='').finance_balance
        self.assertFalse(bal.supported)


class DegenerateFinanceInformation(BaseFinanceInformation):
    _balance = None
    has_to_pay = None
    history = None
    last_update = None


class UserWithFinancesTestCase(TestCase):
    class User(DegenerateUser):
        finance_information = DegenerateFinanceInformation()

    def setUp(self):
        self.bal = self.User(uid='').finance_balance

    def test_balance_row_supported(self):
        self.assertTrue(self.bal.supported)
        self.assertTrue(self.bal.empty)

    def test_balance_correct_name(self):
        self.assertEqual(self.bal.name, 'finance_balance')
