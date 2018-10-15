from unittest.mock import patch

from flask import url_for

from tests.base import SampleFrontendTestBase
from sipa.blueprints.usersuite import get_attribute_endpoint


class SampleAuthenticationTestCase(SampleFrontendTestBase):
    def test_login_successful(self):
        """Test that a login redirects to the usersuite"""
        rv = self.login()
        print("rv:", rv)
        from pprint import pprint
        pprint(rv.data.decode('utf-8'))
        self.assertRedirects(rv, url_for('usersuite.index'))

    def test_logout_successful(self):
        self.login()
        rv = self.logout()
        if rv.status_code == 401:
            self.fail('Logout not permitted, probably because login failed')
        self.assert_redirects(rv, url_for('generic.index'))


class SampleAuthenticatedTestBase(SampleFrontendTestBase):
    def setUp(self):
        super().setUp()
        self.login()

    def tearDown(self):
        self.logout()
        super().tearDown()


class UsersuiteReachableTestCase(SampleAuthenticatedTestBase):
    def test_usersuite_200(self):
        self.assert200(self.client.get(url_for('usersuite.index')))

    def test_contact_200(self):
        self.assert200(self.client.get(url_for('usersuite.contact')))

    def test_mac_edit_200(self):
        self.assert200(self.client.get(url_for('usersuite.change_mac')))

    def activate_network_access_200(self):
        self.assert200(self.client.get(url_for('usersuite.activate_network_access')))

    def test_mail_edit_200(self):
        self.assert200(self.client.get(url_for('usersuite.change_mail')))

    def test_usersuite_contains_urls(self):
        """Test the usersuite contains the urls of `sample`s capabilities."""
        usersuite_response = self.client.get(url_for('usersuite.index'))

        # We have to patch `current_user` since it is not defined due
        # to the wrong app context, but the code runs some asserts
        # against it checking capabilities.
        with patch('sipa.blueprints.usersuite.current_user'):
            urls = [
                *(url_for(get_attribute_endpoint(attr))
                  for attr in ['mail', 'mac', 'use_cache']),
                *(url_for(get_attribute_endpoint(attr, capability='delete'))
                  for attr in ['mail']),
                url_for('usersuite.change_password'),
                url_for('generic.contact'),
            ]

        for url in urls:
            with self.subTest(url=url):
                self.assertRegex(usersuite_response.data.decode('utf-8'),
                                 'href="[^"]*{}[^"]*"'.format(url))

    def test_cache_200(self):
        self.assert200(self.client.get(url_for('usersuite.change_use_cache')))

    def test_cache_toggling_works(self):
        self.assertEqual(self.current_user.use_cache, False)

        resp = self.client.post(url_for('usersuite.change_use_cache'),
                                data={'use_cache': "1"})
        self.assert_redirects(resp, url_for('usersuite.index'))
        self.assertEqual(self.current_user.use_cache, True)

        resp = self.client.post(url_for('usersuite.change_use_cache'),
                                data={'use_cache': "0"})
        self.assert_redirects(resp, url_for('usersuite.index'))
        self.assertEqual(self.current_user.use_cache, False)
