from unittest import TestCase

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation


class TestBaseUserCase(TestCase):
    def test_BaseUser_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseUser('')  # pylint: disable=abstract-class-instantiated

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
    birthdate = None
    mail_forwarded = None
    mail_confirmed = None
    resend_confirm_mail = None
    realname = None
    status = None
    traffic_history = None
    userdb = None
    userdb_status = None
    payment_details = None
    is_member = None


class DegenerateUserTestCase(TestCase):
    def setUp(self):
        self.User = DegenerateUser
        self.uid = 'someone'
        self.user = self.User(uid=self.uid)

    def test_uid_passed(self):
        assert self.user.uid == self.uid

    def test_get_id_implemented(self):
        assert self.user.get_id() == self.uid

    def test_equality_when_same_uid(self):
        assert self.user == self.User(uid=self.uid)

    def test_inequality_when_other_uid(self):
        assert self.user != self.User(uid=self.uid + "invalid")

    def test_finance_balance_unsupported(self):
        assert not self.user.finance_balance.supported


class DegenerateFinanceInformation(BaseFinanceInformation):
    raw_balance = None
    has_to_pay = None
    history = None
    last_update = None
    last_received_update = None


class UserWithFinancesTestCase(TestCase):
    class User(DegenerateUser):
        finance_information = DegenerateFinanceInformation()

    def setUp(self):
        self.bal = self.User(uid='').finance_balance

    def test_balance_row_supported(self):
        assert self.bal.supported
        assert self.bal.empty

    def test_balance_correct_name(self):
        assert self.bal.name == "finance_balance"
