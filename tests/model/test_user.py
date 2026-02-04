from unittest import TestCase

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation
from sipa.model.pycroft.user import User as PycroftUser
from sipa.model.pycroft.schema import UserStatus

from datetime import date


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
    change_mail = None
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

class UserStatusTest(TestCase):
    class FakeActiveProperty:
        raw_value: any

        def __init__(self, val):
            self.raw_value = val

        @property
        def value(self):
            return self.raw_value

        def __bool__(self):
            return bool(self.raw_value)

        def __len__(self):
            return 1 if self.raw_value else 0

    class TestUserData:
        membership_begin_date: date | None
        membership_end_date: "UserStatusTest.FakeActiveProperty"

    def setUp(self):
        self.user = DegenerateUser
        self.user.user_data = self.TestUserData()
        self.user.user_data.membership_begin_date = None
        self.user.membership_end_date = self.FakeActiveProperty(None)

        self.status = UserStatus(
            violation=False,
            network_access=True,
            member=True,
            account_balanced=True,
            traffic_exceeded=False,
        )

    def test_status_member(self):
        assert (PycroftUser.evaluate_status(self.user, self.status)
                == ('Mitglied', 'success'))

    def test_status_violation(self):
        self.status.violation = True
        assert (PycroftUser.evaluate_status(self.user, self.status)
                == ('Verstoß gegen Netzordnung', 'danger'))

    def test_status_unbalanced(self):
        self.status.account_balanced = False
        assert (PycroftUser.evaluate_status(self.user, self.status)
                == ('Nicht bezahlt', 'warning'))

    def test_status_traffic_exceeded(self):
        self.status.traffic_exceeded = True
        assert (PycroftUser.evaluate_status(self.user, self.status)
                == ('Trafficlimit überschritten', 'danger'))

    def test_status_membership_begin_date(self):
        d = date.today()
        self.status.member = False
        self.user.user_data.membership_begin_date = d
        assert (PycroftUser.evaluate_status(self.user, self.status)
                == (f'Mitglied ab {d.isoformat()}', 'warning'))

    def test_status_not_member(self):
        self.status.member = False
        assert (PycroftUser.evaluate_status(self.user, self.status)
                == ('Kein Mitglied', 'muted'))

    def test_status_membership_end_date(self):
        d = date.today()
        self.user.membership_end_date = self.FakeActiveProperty(d)
        assert (PycroftUser.evaluate_status(self.user, self.status)
                == (f'Mitglied bis {d.isoformat()}', 'warning'))

    def test_exhaust_everything(self):
        def set_property(property: list[str], value: any):
            curr_val = self
            for value in property[0:-1]:
                curr_val = getattr(curr_val, value)

            setattr(curr_val, property[-1], value)

        properties = [["status", "violation"],
                      ["status", "account_balanced"],
                      ["status", "traffic_exceeded"],
                      ["user", "user_data", "membership_begin_date"],
                      ["status", "member"],
                      ["user", "membership_end_date"]]
        true_val = self.FakeActiveProperty(date.today())
        false_val = self.FakeActiveProperty(None)

        for val_mapping in range(2 ** len(properties) - 1):
            for i in range(len(properties)):
                if val_mapping >> i & 1:
                    set_property(properties[i], true_val)
                else:
                    set_property(properties[i], false_val)

            message, style = PycroftUser.evaluate_status(self.user, self.status)
            assert message is not None
            assert style is not None
