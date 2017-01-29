#!/usr/bin/env python
import os
import logging
from datetime import datetime, timedelta
from operator import attrgetter

from flask_babel import gettext
from flask_login import AnonymousUserMixin

from .hss_fixtures import HSSOneAccountFixture, HSSOneTrafficAccountFixture, \
    HSSOneTrafficAccountDaysMissingFixture, HSSAccountsWithPropertiesFixture, \
    HSSOneFinanceAccountFixture, OneCreditAccountFixture
from tests.base import HssFrontendTestBase
from sipa.model.sqlalchemy import db
from sipa.model.hss.schema import Account, IP, Mac, TrafficLog, AccountStatementLog, \
    TrafficQuota
from sipa.model.hss.user import User, FinanceInformation


class HssPgTestBase(HssFrontendTestBase):
    def create_app(self, *a, **kw):
        pg_uri = os.getenv('SIPA_TEST_HSS_CONNECTION_STRING', None)
        if not pg_uri:
            self.skipTest("SIPA_TEST_HSS_CONNECTION_STRING not set")

        conf = {
            **kw.pop('additional_config', {}),
            'HSS_CONNECTION_STRING': pg_uri,
            'DB_HELIOS_IP_MASK': "10.10.7.%",
        }
        test_app = super().create_app(*a, additional_config=conf, **kw)
        return test_app

    def setUp(self, *a, **kw):
        super().setUp(*a, **kw)
        db.drop_all(bind='hss')
        db.create_all(bind='hss')
        self.session = db.session
        # create the fixtures
        for objs in self.fixtures_pg.values():
            for obj in objs:
                self.session.add(obj)
        self.session.commit()

    fixtures_pg = {}


class HSSPgEmptyTestCase(HssPgTestBase):
    def test_no_accounts_existent(self):
        self.assertFalse(self.session.query(Account).all())


class HSSPgOneAccountTestCase(HSSOneAccountFixture, HssPgTestBase):
    def setUp(self):
        super().setUp()
        self.received_accounts = self.session.query(Account).all()
        self.received_account = self.received_accounts[0]

    def test_number_of_accounts(self):
        self.assertEqual(len(self.received_accounts),
                         len(self.fixtures_pg[Account]))

    def test_accountname(self):
        self.assertEqual(self.fixtures_pg[Account][0].account,
                         self.received_account.account)


class OneAccountTestBase(HSSOneAccountFixture, HssPgTestBase):
    def setUp(self):
        super().setUp()
        account = self.fixtures_pg[Account][0].account
        # re-receive the account in order to get the relationship
        self.account = db.session.query(Account).filter_by(account=account).one()
        self.user = User(uid=self.account.account)


class PgUserDataTestCase(OneAccountTestBase):
    def test_realname_passed(self):
        self.assertEqual(self.user.realname, self.account.name)

    def test_uid_passed(self):
        self.assertEqual(self.user.uid, self.account.account)

    def test_login_passed(self):
        self.assertEqual(self.user.login, self.account.account)

    def test_credit_passed(self):
        self.assertEqual(self.user.credit, self.account.traffic_balance / 1024)

    def test_address_passed(self):
        access = self.account.access
        for part in [access.building, access.floor, access.flat, access.room]:
            with self.subTest(part=part):
                self.assertIn(part, self.user.address)

    def test_mail_correct(self):
        acc = self.fixtures_pg[Account][0]
        user = User.get(acc.account)
        expected_mail = "{}@wh12.tu-dresden.de".format(acc.account)
        self.assertEqual(user.mail, expected_mail)

    def test_uninitialized_max_credit_throws_warning(self):
        logger = logging.getLogger('sipa.model.hss.user')
        with self.assertLogs(logger, level='WARNING') as cm:
            self.assertEqual(self.user.max_credit, 63 * 1024**2)
            self.assertEqual(self.user.daily_credit, 3 * 1024**2)

            self.assertEqual(len(cm.output), 2)
            last_log = cm.output.pop()
            self.assertEqual(cm.output.pop(), last_log)
            self.assertIn("No traffic quota object found", last_log)


class CreditMaximumTestCase(OneCreditAccountFixture, OneAccountTestBase):
    def test_correct_max_credit_passed(self):
        self.assertEqual(self.user.max_credit * 1024,
                         self.fixtures_pg[TrafficQuota][0].max_credit)

    def test_correct_daily_credit_passed(self):
        self.assertEqual(self.user.daily_credit * 1024,
                         self.fixtures_pg[TrafficQuota][0].daily_credit)


class UserFromIpTestCase(OneAccountTestBase):
    def test_from_ip_correct_user(self):
        for ip in self.fixtures_pg[IP]:
            if not ip.account:
                continue
            with self.subTest(ip=ip.ip):
                self.assertEqual(User.get(ip.account), User.from_ip(ip.ip))

    def test_from_ip_without_account_anonymous(self):
        for ip in self.fixtures_pg[IP]:
            if ip.account:
                continue

            with self.subTest(ip=ip.ip):
                self.assertIsInstance(User.from_ip(ip.ip), AnonymousUserMixin)


class UserIpsTestCase(OneAccountTestBase):
    def test_ips_passed(self):
        for account in self.fixtures_pg[Account]:
            with self.subTest(account=account):
                user = User.get(account.account)
                expected_ips = self.session.query(Account).get(account.account).ips
                for ip in expected_ips:
                    with self.subTest(ip=ip):
                        self.assertIn(ip.ip, user.ips)


class UserMacsTestCase(OneAccountTestBase):
    def test_macs_passed(self):
        for mac in self.fixtures_pg.get(Mac, []):
            if mac.account is None:
                continue

            with self.subTest(mac=mac.mac):
                user = User.get(mac.account)
                self.assertIn(mac.mac.lower(), user.mac)


# Dependency injection of new fixture
class UserTrafficLogTestCaseMixin:
    def setUp(self):
        super().setUp()
        self.user = User.get(self.account.account)
        self.history = self.user.traffic_history

    def test_traffic_log_correct_length(self):
        self.assertEqual(len(self.history), 7)

    def test_traffic_data_passed(self):
        # Pick the latest 7 entries
        expected_logs = sorted(self.fixtures_pg[TrafficLog], key=attrgetter('date'))[-7:]
        expected_entries = []

        for date_delta in range(-6, 1):
            expected_date = (datetime.today() + timedelta(date_delta)).date()
            possible_logs = [log for log in expected_logs
                             if (log.date == expected_date and
                                 log.account == self.account.account)]
            try:
                expected_entries.append(possible_logs.pop())
            except IndexError:
                expected_entries.append(None)

        for entry, expected_log in zip(self.history, expected_entries):
            with self.subTest(entry=entry, expected_log=expected_log):

                if expected_log is None:
                    self.assertFalse(entry['input'])
                    self.assertFalse(entry['output'])
                else:
                    self.assertEqual(entry['day'], expected_log.date.weekday())
                    self.assertEqual(entry['input'], expected_log.bytes_in / 1024)
                    self.assertEqual(entry['output'], expected_log.bytes_out / 1024)

    def test_correct_credit_difference(self):
        for i, entry in enumerate(self.history):
            with self.subTest(i=i, entry=entry):
                try:
                    credit_difference = self.history[i+1]['credit'] - entry['credit']
                except IndexError:
                    pass
                else:
                    self.assertEqual(credit_difference, 3 * 1024**2 - entry['throughput'])


class UserTrafficLogTestCase(
        HSSOneTrafficAccountFixture,
        UserTrafficLogTestCaseMixin,
        OneCreditAccountFixture,
):
    pass


class UserMissingTrafficLogTestCase(
        HSSOneTrafficAccountDaysMissingFixture,
        UserTrafficLogTestCaseMixin,
        OneCreditAccountFixture,
):
    pass


class UsersActiveTestCase(
        HSSAccountsWithPropertiesFixture,
        HssPgTestBase,
):

    def setUp(self):
        super().setUp()
        self.accounts = self.session.query(Account).all()

    def test_user_is_active_or_not(self):
        for account in self.accounts:
            with self.subTest(account=account):
                user = User.get(account.account)
                self.assertEqual(user.has_connection, account.properties.active)

    def test_active_user_status_correct(self):
        for account in self.accounts:
            if not account.properties.active:
                continue

            with self.subTest(account=account):
                user = User.get(account.account)
                self.assertEqual(user.status, gettext("Aktiv"))

    def test_passive_user_status_correct(self):
        for account in self.accounts:
            if account.properties.active:
                continue

            with self.subTest(account=account):
                user = User.get(account.account)
                self.assertEqual(user.status, gettext("Passiv"))


class UserFinanceTestCase(HSSOneFinanceAccountFixture, OneAccountTestBase):
    def test_finance_balance_correct(self):
        self.assertEqual(self.user.finance_balance, 3.5)

    def test_last_update_date_exists(self):
        expected_date = max(l.timestamp for l in self.fixtures_pg[AccountStatementLog])
        self.assertEqual(self.user.finance_information.last_update, expected_date)


class UserNoFinanceTestCase(OneAccountTestBase):
    def test_finance_balance_zero(self):
        """Test that an account with nothing set has a zero finance balance"""
        self.assertEqual(self.user.finance_balance, 0)


class UserFinanceLogTestCase(HSSOneFinanceAccountFixture, OneAccountTestBase):
    def setUp(self):
        super().setUp()
        self.finance_info = FinanceInformation.from_pg_account(self.account)
        self.transactions = self.account.combined_transactions
        self.expected_length = len(self.account.transactions) + len(self.account.fees)

    def test_user_transaction_length_correct(self):
        self.assertEqual(len(self.transactions), self.expected_length)

    def test_user_transaction_sorted(self):
        last_log = None
        for log in self.transactions:
            if last_log is not None:
                self.assertLessEqual(last_log.datum, log.datum)
            last_log = log

    def test_user_logs_correct_length(self):
        self.assertEqual(len(self.finance_info.history),
                         self.expected_length)

    def test_user_logs_two_items(self):
        for log in self.finance_info.history:
            with self.subTest(log=log):
                self.assertEqual(len(log), 2)

    def test_finance_information_passed_to_user(self):
        self.assertEqual(self.user.finance_information, self.finance_info)
