#!/usr/bin/env python
from collections import OrderedDict

from flask.ext.login import AnonymousUserMixin

from tests.prepare import AppInitialized
from sipa.model.sqlalchemy import db
from sipa.model.hss.schema import Account, Access, IP, Mac
from sipa.model.hss.user import User


class HssPgTestBase(AppInitialized):
    def create_app(self):
        test_app = super().create_app(additional_config={
            'WU_CONNECTION_STRING': "sqlite:///",
            'HSS_CONNECTION_STRING': "postgresql://sipa:password@postgres:5432/",
            'DB_HELIOS_IP_MASK': "10.10.7.%",
        })
        return test_app

    def setUp(self):
        db.drop_all(bind='hss')
        db.create_all(bind='hss')
        self.session = db.session


class HSSPgEmptyTestCase(HssPgTestBase):
    def test_no_accounts_existent(self):
        self.assertFalse(self.session.query(Account).all())


class FixtureLoaderMixin:
    """A Mixin that creates `self.fixtures` on setUp.

    It expects the class to have the attributes `fixtures` and
    `session`.
    """
    def setUp(self):
        super().setUp()
        for objs in self.fixtures.values():
            for obj in objs:
                self.session.add(obj)
        self.session.commit()


class HSSOneAccountFixture(FixtureLoaderMixin):
    @property
    def fixtures(self):
        return OrderedDict([
            (Account, [
                Account(
                    account='sipatinator',
                    name="Sipa Tinator",
                    traffic_balance=67206545441,
                    access_id=1,
                ),
            ]),
            (Access, [
                Access(
                    id=1,
                    building="HSS46",
                    floor="0",
                    flat="1",
                    room="b",
                )
            ]),
            (IP, [
                IP(ip="141.30.234.15", account="sipatinator"),
                IP(ip="141.30.234.16"),
                IP(ip="141.30.234.18", account="sipatinator"),
            ]),
            (Mac, [
                Mac(id=1, mac="aa:bb:cc:ff:ee:dd"),
                Mac(id=2, mac="aa:bb:cc:ff:ee:de", account='sipatinator'),
                Mac(id=3, mac="aa:bb:cc:ff:ee:df", account='sipatinator'),
            ]),
        ])


class HSSPgOneAccountTestCase(HSSOneAccountFixture, HssPgTestBase):
    def setUp(self):
        super().setUp()
        self.received_accounts = self.session.query(Account).all()
        self.received_account = self.received_accounts[0]

    def test_number_of_accounts(self):
        self.assertEqual(len(self.received_accounts),
                         len(self.fixtures[Account]))

    def test_accountname(self):
        self.assertEqual(self.fixtures[Account][0].account,
                         self.received_account.account)


class TestUserFromPgCase(HSSOneAccountFixture, HssPgTestBase):
    def setUp(self):
        super().setUp()
        account = self.fixtures[Account][0].account
        # re-receive the account in order to get the relationship
        self.account = db.session.query(Account).filter_by(account=account).one()
        self.user = User(uid=self.account.account)

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

    def test_from_ip_correct_user(self):
        for ip in self.fixtures[IP]:
            if not ip.account:
                continue
            with self.subTest(ip=ip.ip):
                self.assertEqual(User.get(ip.account), User.from_ip(ip.ip))

    def test_from_ip_without_account_anonymous(self):
        for ip in self.fixtures[IP]:
            if ip.account:
                continue

            with self.subTest(ip=ip.ip):
                self.assertIsInstance(User.from_ip(ip.ip), AnonymousUserMixin)

    def test_ips_passed(self):
        for account in self.fixtures[Account]:
            with self.subTest(account=account):
                user = User.get(account.account)
                expected_ips = self.session.query(Account).get(account.account).ips
                for ip in expected_ips:
                    with self.subTest(ip=ip):
                        self.assertIn(ip.ip, user.ips)

    def test_macs_passed(self):
        for mac in self.fixtures.get(Mac, []):
            if mac.account is None:
                continue

            with self.subTest(mac=mac.mac):
                print("mac.account:", mac.account)
                print("accounts:", [a.account for a in self.fixtures[Account]])
                user = User.get(mac.account)
                self.assertIn(mac.mac.lower(), user.mac)
