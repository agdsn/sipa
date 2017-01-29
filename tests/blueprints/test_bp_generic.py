import logging
from functools import partial

from flask import abort, url_for
from tests.base import SampleFrontendTestBase, FormTemplateTestMixin

from sipa.model import backends


class TestErrorhandlersCase(SampleFrontendTestBase):
    used_codes = [401, 403, 404]

    def create_app(self):
        test_app = super().create_app()

        def failing(code):
            abort(code)

        for code in self.used_codes:
            test_app.add_url_rule(
                rule='/aborting-{}'.format(code),
                endpoint='aborting-with-{}'.format(code),
                view_func=partial(failing, code=code),
            )

        return test_app

    def test_error_handler_redirection(self):
        for code in self.used_codes:
            self.client.get('/aborting-{}'.format(code))
            self.assertTemplateUsed('error.html')


class GenericEndpointsReachableTestCase(SampleFrontendTestBase):
    def test_index_redirects_correctly(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/news/')

    def test_index_reachable(self):
        self.assert200(self.client.get('/', follow_redirects=True))

    def test_usertraffic_permitted(self):
        # only reachable because `from_ip` always returns test user
        self.assert200(self.client.get(url_for('generic.usertraffic')))

    def test_api_reachable(self):
        rv = self.client.get(url_for('generic.traffic_api'))
        self.assert200(rv)

    def test_version_reachable(self):
        self.assert200(self.client.get(url_for('generic.version')))
        self.assertTemplateUsed('version.html')


class LoginTestCase(FormTemplateTestMixin, SampleFrontendTestBase):
    def setUp(self):
        super().setUp()
        self.url = url_for('generic.login')
        self.dormitory = 'localhost'
        self.template = 'login.html'

        self.valid_data = [{
            'dormitory': self.dormitory,
            'username': "test",
            'password': "test",
            'remember': "1",
        }]
        self.invalid_data = [
            {**self.valid_data[0], 'dormitory': ''},
            {**self.valid_data[0], 'dormitory': 'not_'+self.dormitory},
            {**self.valid_data[0], 'username': ''},
            {**self.valid_data[0], 'username': 'not_test'},
        ]


class ContactFormTestBase(SampleFrontendTestBase):
    """This subclass additionally temporarily disables CRITICAL logs.

    These get triggered because no SMTP server is reachable when
    testing the contact form in this setup.
    """
    def setUp(self):
        super().setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        super().tearDown()



class AnonymousContactTestCase(FormTemplateTestMixin, ContactFormTestBase):
    def setUp(self):
        super().setUp()
        self.url = url_for('generic.contact')
        self.dormitory = 'localhost'
        self.template = 'anonymous_contact.html'

        self.valid_data = [{
            'email': "foo@bar.baz",
            'name': "Darc net",
            'dormitory': self.dormitory,
            'subject': "Test",
            'message': "Test message!",
        }]
        self.invalid_data = [
            {**self.valid_data[0], 'email': ''},
            {**self.valid_data[0], 'email': 'foo@bar'},
            {**self.valid_data[0], 'name': ''},
            {**self.valid_data[0], 'dormitory': 'not_'+self.dormitory},
            {**self.valid_data[0], 'subject': ''},
            {**self.valid_data[0], 'message': ''},
        ]


class OfficialContactTestCase(FormTemplateTestMixin, ContactFormTestBase):
    def setUp(self):
        super().setUp()
        self.url = url_for('generic.contact_official')
        self.template = 'official_contact.html'

        self.valid_data = [{
            'email': "foo@bar.baz",
            'name': "Darc net",
            'subject': "Test",
            'message': "Test message!",
        }]
        self.invalid_data = [
            {**self.valid_data[0], 'email': ''},
            {**self.valid_data[0], 'email': 'foo@bar'},
            {**self.valid_data[0], 'name': ''},
            {**self.valid_data[0], 'subject': ''},
            {**self.valid_data[0], 'message': ''},
        ]
