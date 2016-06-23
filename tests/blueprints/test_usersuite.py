from unittest.mock import patch

from flask import url_for

from tests.prepare import AppInitialized
from sipa.blueprints.usersuite import get_attribute_endpoint


class SampleAuthenticatedTestBase(AppInitialized):
    def login(self):
        return self.client.post(
            url_for('generic.login'),
            data={'dormitory': 'localhost',
                  'username': 'test',
                  'password': 'test'},
        )

    def logout(self):
        return self.client.get(
            url_for('generic.logout')
        )


class SampleAuthenticationTestCase(SampleAuthenticatedTestBase):
    def test_login_successful(self):
        """Test that a login redirects to the usersuite"""
        rv = self.login()
        print("rv:", rv)
        from pprint import pprint
        pprint(rv.data.decode('utf-8'))
        self.assertRedirects(rv, url_for('usersuite.usersuite'))

    def test_logout_successful(self):
        self.login()
        rv = self.logout()
        if rv.status_code == 401:
            self.fail('Logout not permitted, probably because login failed')
        self.assert_redirects(rv, url_for('generic.index'))


class SampleFrontendTestBase(SampleAuthenticatedTestBase):
    def setUp(self):
        super().setUp()
        self.login()

    def tearDown(self):
        self.logout()
        super().tearDown()


class UsersuiteReachableTestCase(SampleFrontendTestBase):
    def test_usersuite_200(self):
        self.assert200(self.client.get(url_for('usersuite.usersuite')))

    def test_contact_200(self):
        self.assert200(self.client.get(url_for('usersuite.usersuite_contact')))

    def test_mac_edit_200(self):
        self.assert200(self.client.get(url_for('usersuite.change_mac')))

    def test_mail_edit_200(self):
        self.assert200(self.client.get(url_for('usersuite.change_mail')))

    def test_usersuite_contains_urls(self):
        """Test the usersuite contains the urls of `sample`s capabilities."""
        usersuite_response = self.client.get(url_for('usersuite.usersuite'))

        # We have to patch `current_user` since it is not defined due
        # to the wrong app context, but the code runs some asserts
        # against it checking capabilities.
        with patch('sipa.blueprints.usersuite.current_user'):
            urls = [
                *(url_for(get_attribute_endpoint(attr))
                  for attr in ['mail', 'mac', 'finance_balance']),
                *(url_for(get_attribute_endpoint(attr, capability='delete'))
                  for attr in ['mail']),
                url_for('usersuite.usersuite_change_password'),
                url_for('generic.contact'),
            ]

        for url in urls:
            with self.subTest(url=url):
                self.assertRegex(usersuite_response.data.decode('utf-8'),
                                 'href="[^"]*{}[^"]*"'.format(url))


class FinanceLogsTestCase(SampleFrontendTestBase):
    def setUp(self):
        super().setUp()
        with patch('sipa.blueprints.usersuite.current_user'):
            self.rv = self.client.get(url_for(get_attribute_endpoint('finance_balance')))

    def test_finance_logs_reachable(self):
        self.assert200(self.rv)

    def test_finance_logs_available(self):
        self.assertTemplateUsed('usersuite/finance_logs.html')

    def test_random_values_contained(self):
        self.assertIn("21", self.rv.data.decode('utf-8'))
        self.assertIn("-3.5", self.rv.data.decode('utf-8'))
