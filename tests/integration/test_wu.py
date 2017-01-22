import os
from contextlib import contextmanager
from datetime import datetime
from operator import attrgetter
from unittest.mock import MagicMock, patch

from flask_login import AnonymousUserMixin

from sipa.model.wu.user import User
from sipa.model.wu.database_utils import STATUS
from sipa.model.wu.schema import db, Nutzer, Buchung
from sipa.model.wu.factories import (ActiveNutzerFactory, InactiveNutzerFactory,
                                     UnknownStatusNutzerFactory,
                                     ComputerFactory, NutzerFactory,
                                     NoHostAliasComputerFactory,
                                     CreditFactory, TrafficFactory)
from sipa.utils import timetag_today
from tests.base import WuFrontendTestBase


class WuAtlantisFakeDBInitialized(WuFrontendTestBase):
    def create_app(self, *a, **kw):
        userman_uri = os.getenv('SIPA_TEST_DB_USERMAN_URI', None)
        if not userman_uri:
            self.skipTest("SIPA_TEST_DB_USERMAN_URI not set")

        config = {
            **kw.pop('additional_config', {}),
            'DB_NETUSERS_URI': "sqlite:///",
            'DB_TRAFFIC_URI': "sqlite:///",
            'DB_USERMAN_URI': userman_uri,
            'DB_HELIOS_IP_MASK': "10.10.7.%",
        }
        return super().create_app(*a, **kw, additional_config=config)

    def setUp(self):
        db.drop_all()
        db.create_all()

    def assert_computer_data_passed(self, computer, user):
        self.assertIn(computer.c_ip, user.ips)
        self.assertIn(computer.c_etheraddr.upper(), user.mac)
        self.assertIn(computer.c_hname, user.hostname)
        self.assertIn(computer.c_alias, user.hostalias)

    @staticmethod
    def create_user_ldap_patched(uid, name, mail):
        with patch('sipa.model.wu.user.search_in_group',
                   MagicMock(return_value=False)):
            return User(
                uid=uid,
                realname=name,
                mail=mail,
            )


class UserWithDBTestCase(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()

        self.nutzer = NutzerFactory.create(status=1)
        self.computer = ComputerFactory.create(nutzer=self.nutzer)

    @staticmethod
    def get_sql_user_from_login(unix_account):
        return db.session.query(Nutzer).filter_by(unix_account=unix_account).one()

    def test_from_ip_returns_anonymous(self):
        user = User.from_ip("141.30.228.66")
        self.assertIsInstance(user, AnonymousUserMixin)

    def test_from_ip_user_returned(self):
        with patch('sipa.model.wu.user.User.get') as user_get_mock:
            user_get_mock.side_effect = self.get_sql_user_from_login

            user = User.from_ip(self.computer.c_ip)
            self.assertEqual(user_get_mock.call_args[0],
                             (self.nutzer.unix_account,))
            self.assertEqual(user, self.nutzer)

    def test_from_ip_user_not_in_ldap(self):
        with patch('sipa.model.wu.user.User.get', MagicMock(return_value=None)), \
                patch('sipa.model.wu.user.logger.warning') as warning_mock:
            user = User.from_ip(self.computer.c_ip)
            self.assertIsInstance(user, AnonymousUserMixin)
            self.assertIn(" could not ", warning_mock.call_args[0][0])
            self.assertIn("LDAP", warning_mock.call_args[0][0])


class UserNoComputersTestCase(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()
        self.nutzer = NutzerFactory.create()
        self.user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        )

    def test_user_has_no_computer_data(self):
        self.assertFalse(self.user.mac)
        self.assertFalse(self.user.ips)
        self.assertFalse(self.user.hostname)
        self.assertFalse(self.user.hostalias)


class TestUserInitializedCase(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()

        self.nutzer = NutzerFactory.create(status=1)
        self.computers = ComputerFactory.create_batch(20, nutzer=self.nutzer)

        self.name = "Test Nutzer"
        self.mail = "foo@bar.baz"

        self.user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=self.name,
            mail=self.mail,
        )

    def test_mail_passed(self):
        self.assertEqual(self.user.mail, self.mail)

    def test_computer_data_passed(self):
        for computer in self.computers:
            with self.subTest(computer=computer):
                self.assert_computer_data_passed(computer, self.user)

    def test_address_passed(self):
        self.assertEqual(self.user.address, self.nutzer.address)

    def test_id_passed(self):
        original_id = str(self.nutzer.nutzer_id)
        fetched_id = self.user.id.value
        self.assertTrue(
            fetched_id.startswith(original_id),
            msg="id '{}' doesn't start with '{}'".format(fetched_id,
                                                         original_id)
        )


class ComputerWithoutAliasTestCase(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()

        self.nutzer = NutzerFactory.create(status=1)

        self.name = "Test Nutzer"
        self.mail = "foo@bar.baz"

        self.user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=self.name,
            mail=self.mail,
        )

    @contextmanager
    def fail_on_type_error(self):
        try:
            yield
        except TypeError:
            self.fail("Accessing user.hostalias with one alias being None "
                      "threw a TypeError")

    def test_computer_no_alias_returns_empty_string(self):
        NoHostAliasComputerFactory.create(nutzer=self.nutzer)
        with self.fail_on_type_error():
            self.assertEqual(self.user.hostalias, "")

    def test_computer_no_alias_not_included(self):
        self.computers = ComputerFactory.create_batch(2, nutzer=self.nutzer)
        self.computers += NoHostAliasComputerFactory.create_batch(2, nutzer=self.nutzer)
        with self.fail_on_type_error():
            for computer in self.computers:
                if not computer.c_alias:
                    continue

                with self.subTest(computer=computer):
                    self.assertIn(computer.c_alias, self.user.hostalias)


class UserStatusGivenCorrectly(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()
        self.valid_status_nutzer_list = NutzerFactory.create_batch(20)
        self.unknown_status_nutzer_list = UnknownStatusNutzerFactory.create_batch(20)

    def test_unknown_status_empty(self):
        for nutzer in self.unknown_status_nutzer_list:
            user = self.create_user_ldap_patched(
                uid=nutzer.unix_account,
                name=None,
                mail=None,
            )
            with self.subTest(user=user):
                self.assertFalse(user.status)

    def test_known_status_passed(self):
        for nutzer in self.valid_status_nutzer_list:
            user = self.create_user_ldap_patched(
                uid=nutzer.unix_account,
                name=None,
                mail=None,
            )
            with self.subTest(user=user):
                self.assertEqual(STATUS[nutzer.status][0], user.status)


class CorrectUserHasConnection(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()
        self.connection_nutzer_list = ActiveNutzerFactory.create_batch(20)
        self.no_connection_nutzer_list = InactiveNutzerFactory.create_batch(20)

    def test_correct_users_have_connection(self):
        for nutzer in self.connection_nutzer_list:
            user = self.create_user_ldap_patched(
                uid=nutzer.unix_account,
                name=None,
                mail=None
            )
            with self.subTest(user=user):
                self.assertTrue(user.has_connection)

    def test_incorrect_users_no_connection(self):
        for nutzer in self.no_connection_nutzer_list:
            user = self.create_user_ldap_patched(
                uid=nutzer.unix_account,
                name=None,
                mail=None,
            )
            with self.subTest(user=user):
                self.assertFalse(user.has_connection)


class OneUserWithCredit(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()
        self.nutzer = NutzerFactory.create()
        self.credit_entries = []
        self.timetag_range = range(timetag_today()-21, timetag_today())
        for timetag in self.timetag_range:
            self.credit_entries.append(CreditFactory.create(nutzer=self.nutzer,
                                                            timetag=timetag))


class CreditTestCase(OneUserWithCredit):
    def setUp(self):
        super().setUp()

    def test_credit_passed(self):
        fetched_user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        )
        expected_credit = self.credit_entries[-1].amount
        self.assertEqual(fetched_user.credit, expected_credit)

    def test_credit_appears_in_history(self):
        fetched_history = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        ).traffic_history
        # the history is ascending, but wee ned a zip ending at
        # *today* (last element)
        combined_history = zip(reversed(self.credit_entries), reversed(fetched_history))

        for expected_credit, traffic_entry in combined_history:
            with self.subTest(traffic_entry=traffic_entry):
                self.assertEqual(traffic_entry['credit'], expected_credit.amount)


class TrafficOneComputerTestCase(OneUserWithCredit):
    def setUp(self):
        super().setUp()
        self.computer = ComputerFactory(nutzer=self.nutzer)
        self.traffic_entries = []
        for timetag in range(timetag_today()-21, timetag_today()):
            traffic_entry = TrafficFactory.create(timetag=timetag, ip=self.computer.c_ip)
            self.traffic_entries.append(traffic_entry)

    def test_traffic_data_passed(self):
        fetched_history = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        ).traffic_history
        # the history is ascending, but wee ned a zip ending at
        # *today* (last element)
        combined_history = zip(reversed(self.traffic_entries), reversed(fetched_history))

        for expected_traffic, traffic_entry in combined_history:
            with self.subTest(traffic_entry=traffic_entry):
                self.assertEqual(traffic_entry['input'], traffic_entry['input'])
                self.assertEqual(traffic_entry['output'], traffic_entry['output'])


class UsermanInitializedTestCase(WuAtlantisFakeDBInitialized):
    def test_userman_in_binds(self):
        self.assertIn('userman', self.app.config['SQLALCHEMY_BINDS'].keys())

    def test_userman_correctly_initialized(self):
        self.assertFalse(db.session.query(Buchung).all())


class FinanceBalanceTestCase(OneUserWithCredit):
    def setUp(self):
        super().setUp()
        self.transactions = [
            Buchung(wert=-350, soll_uid=self.nutzer.nutzer_id, haben_uid=None,
                    bes="Freischalten!!!", datum=datetime(2016, 6, 1)),
            Buchung(wert=350, soll_uid=self.nutzer.nutzer_id, haben_uid=None,
                    bes="Semesterbeitrag 04/16", datum=datetime(2016, 4, 30)),
            Buchung(wert=350, soll_uid=self.nutzer.nutzer_id, haben_uid=None,
                    bes="Semesterbeitrag 05/16", datum=datetime(2016, 5, 30)),
        ]
        for t in self.transactions:
            db.session.add(t)
        db.session.commit()
        self.user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        )
        self.finance_info = self.user.finance_information

    def test_correct_number_of_transactions(self):
        recvd_transactions = db.session.query(Nutzer).one().transactions
        self.assertEqual(len(self.transactions), len(recvd_transactions))

    def test_user_has_correct_balance(self):
        expected_balance = 3.5
        self.assertEqual(self.finance_info.balance, expected_balance)

    def test_finance_date_max_in_database(self):
        expected_date = max(t.datum for t in self.transactions)
        self.assertEqual(self.finance_info.last_update, expected_date)

    def test_finance_logs_is_duple(self):
        for log in self.finance_info.history:
            with self.subTest(log=log):
                self.assertEqual(len(log), 2)

    def test_user_has_correct_logs(self):
        expected_logs = sorted([t.unsafe_as_tuple() for t in self.transactions],
                               key=attrgetter('datum'))
        self.assertEqual(self.finance_info.history, expected_logs)

    def test_finance_logs_sorted_by_date(self):
        logs = self.finance_info.history
        last_log = None
        for log in logs:
            if last_log is not None:
                self.assertLessEqual(last_log[0], log[0])
            last_log = log


class HabenSollSwitchedTestCase(OneUserWithCredit):
    def setUp(self):
        super().setUp()
        self.transactions = [
            Buchung(wert=-350, soll_uid=self.nutzer.nutzer_id, haben_uid=None,
                    bes="Freischalten!!!", datum=datetime(2016, 6, 1)),
            Buchung(wert=350, soll_uid=self.nutzer.nutzer_id, haben_uid=None,
                    bes="Semesterbeitrag 04/16", datum=datetime(2016, 4, 30)),
            Buchung(wert=-350, haben_uid=self.nutzer.nutzer_id, soll_uid=None,
                    bes="Semesterbeitrag 05/16", datum=datetime(2016, 5, 30)),
        ]
        for t in self.transactions:
            db.session.add(t)
        db.session.commit()
        self.user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        )

    def test_user_has_correct_balance(self):
        expected_balance = 3.5
        self.assertEqual(self.user.finance_information.balance, expected_balance)


class NoInternetByRentalTestCase(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()
        self.nutzer = NutzerFactory()
        self.user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        )

    def test_user_must_pay_fees(self):
        self.assertTrue(self.user.finance_information.has_to_pay)


class InternetByRentalTestCase(WuAtlantisFakeDBInitialized):
    def setUp(self):
        super().setUp()
        self.nutzer = NutzerFactory(internet_by_rental=True)
        self.user = self.create_user_ldap_patched(
            uid=self.nutzer.unix_account,
            name=None,
            mail=None,
        )

    def test_user_doesnt_have_to_pay_fees(self):
        self.assertFalse(self.user.finance_information.has_to_pay)
