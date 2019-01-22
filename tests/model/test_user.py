from unittest import TestCase

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation


class TestBaseUserCase(TestCase):
    def test_BaseUser_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseUser('')  # pylint: disable=abstract-class-instantiated

    def test_BaseUser_has_flask_login_properties(self):
        self.assertTrue(BaseUser.is_authenticated)
        self.assertTrue(BaseUser.is_active)
        self.assertFalse(BaseUser.is_anonymous)

    # more can't be done here, we need some instances.


class DegenerateUser(BaseUser):
    address = None
    authenticate = None
    can_change_password = None
    change_password = None
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
    use_cache = None
    payment_details = None


class DegenerateUserTestCase(TestCase):
    def setUp(self):
        self.User = DegenerateUser
        self.uid = 'someone'
        self.user = self.User(uid=self.uid)

    def test_uid_passed(self):
        self.assertEqual(self.user.uid, self.uid)

    def test_get_id_implemented(self):
        self.assertEqual(self.user.get_id(), self.uid)

    def test_equality_when_same_uid(self):
        self.assertEqual(self.user, self.User(uid=self.uid))

    def test_inequality_when_other_uid(self):
        self.assertNotEqual(self.user, self.User(uid=self.uid + 'invalid'))

    def test_finance_balance_unsupported(self):
        self.assertFalse(self.user.finance_balance.supported)


class DegenerateFinanceInformation(BaseFinanceInformation):
    raw_balance = None
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
