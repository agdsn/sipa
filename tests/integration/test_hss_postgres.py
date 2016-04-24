#!/usr/bin/env python
from tests.prepare import AppInitialized
from sipa.model.sqlalchemy import db
from sipa.model.hss.schema import Account


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
        return {
            Account: [
                Account(account='sipatinator'),
            ],
        }


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
