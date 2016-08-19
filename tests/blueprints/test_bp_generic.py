from functools import partial

from flask import abort, url_for
from tests.base import SampleFrontendTestBase

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

    def test_login_reachable(self):
        self.assert200(self.client.get(url_for('generic.login')))
        self.assertTemplateUsed('login.html')

    def test_usertraffic_denied(self):
        # throws 401 because we don't have an ip matching a user
        self.assertStatus(self.client.get(url_for('generic.usertraffic')), 401)

    def test_api_reachable(self):
        rv = self.client.get(url_for('generic.traffic_api'))
        self.assert200(rv)

    def test_contact_reachable(self):
        self.assert200(self.client.get(url_for('generic.contact')))
        self.assertTemplateUsed('anonymous_contact.html')

    def test_official_contact_reachable(self):
        self.assert200(self.client.get(url_for('generic.contact_official')))
        self.assertTemplateUsed('official_contact.html')

    def test_version_reachable(self):
        self.assert200(self.client.get(url_for('generic.version')))
        self.assertTemplateUsed('version.html')


class FormTemplateTestMixin:
    """A Mixin for conveniently testing forms.

    Must be mixed with a subclass of :py:cls:`TestCase` in order to
    access the assert methods.

    Requires the following attributes:

        - client: The flask test client

        - url: The url of the endpoint to test

        - template: The location of the template file, relative to the
          template root
    """
    def assert_something_flashed(self, data, level='danger'):
        """Assert that something flashed inside the body.

        :param binary data: binary content of the response
        :param str level: the flash level, i.e. one of ['info',
            'success', 'warning', 'danger']
        """
        string_to_find = "sipa_flash alert alert-{}".format(level)
        self.assertIn(string_to_find.encode('utf-8'), data)

    def assert_nothing_flashed(self, data):
        string_not_to_find = "sipa_flash alert"
        self.assertNotIn(string_not_to_find.encode('utf-8'), data)

    def test_endpoint_reachable(self):
        self.assert200(self.client.get(self.url))
        self.assertTemplateUsed(self.template)

    def test_empty_request_flashes(self):
        resp = self.client.post(self.url)
        self.assert_something_flashed(resp.data)

    def test_invalid_data_flashes(self):
        for data in self.invalid_data:
            with self.subTest(data=data):
                resp = self.client.post(self.url, data=data)
                self.assert_something_flashed(resp.data)

    def test_valid_data_passes(self):
        for data in self.valid_data:
            with self.subTest(data=data):
                resp = self.client.post(self.url, data=data)
                self.assert_nothing_flashed(resp.data)


class AnonymousContactTestCase(FormTemplateTestMixin, SampleFrontendTestBase):
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


class OfficialContactTestCase(FormTemplateTestMixin, SampleFrontendTestBase):
    def setUp(self):
        super().setUp()
        self.url = url_for('generic.contact_official')
        self.template = 'official_contact.html'
        self.dormitory = 'localhost'

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
