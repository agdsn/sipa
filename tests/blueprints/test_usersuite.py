from flask import url_for

from tests.prepare import AppInitialized


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
