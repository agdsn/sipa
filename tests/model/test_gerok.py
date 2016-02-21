import json
from itertools import chain
from requests import Response
from unittest.mock import MagicMock, patch

from sipa.model.gerok.user import do_api_call, User
from tests.prepare import AppInitialized


def mocked_gerok_api(status_code=200, response=b""):
    get = MagicMock()

    get.return_value = Response()
    get().status_code = status_code
    get()._content = response

    return get


class TestGerokApiCall(AppInitialized):
    get = mocked_gerok_api()
    post = mocked_gerok_api()
    url = "supersecret.onion"

    def setUp(self):
        self.set_token("")
        self.app.extensions['gerok_api']['endpoint'] = self.url
        self.get.reset_mock()
        self.post.reset_mock()

    def set_token(self, token):
        self.app.extensions['gerok_api']['token'] = token

    @patch('requests.get', get)
    def test_empty_request(self):
        self.assertEqual(do_api_call(""), "")
        assert self.get.called

    @patch('requests.get', get)
    def test_not_200_ValueError(self):
        # loop over a lot of status codes except 200
        for status in chain(range(0, 200, 20), range(201, 600, 20)):
            self.get.reset_mock()
            self.get().status_code = status

            with self.assertRaises(ValueError):
                do_api_call("")

            assert self.get.called

    @patch('requests.get', get)
    def test_correct_url_called(self):
        do_api_call("")

        # assert that the call only got the positional args `(self.url,)`
        self.assertEqual(self.get.call_args[0], (self.url,))

    @patch('requests.get', get)
    def test_json_parsed(self):
        sample_dicts = [
            {},
            {'foo': 'bar'},
            {'foo': 'bar', 'dict': {'baz': 'shizzle'}, 'int': 2},
        ]
        for d in sample_dicts:
            self.get()._content = json.dumps(d).encode()
            self.assertEqual(do_api_call(""), d)

    @patch('requests.get', get)
    @patch('requests.post', post)
    def test_post_called(self):
        do_api_call("", method='post', postdata=None)
        self.get.assert_not_called()
        self.assertEqual(self.post.called, True)

    @patch('requests.get', get)
    @patch('requests.post', post)
    def test_invalid_method(self):
        for method in ['GET', 'POST', 'nothing_of_both', 'something_else']:
            with self.assertRaises(ValueError):
                do_api_call("", method=method, postdata=None)
            self.get.assert_not_called()
            self.post.assert_not_called()

    @patch('requests.post', post)
    def test_postdata_passed(self):
        postdata = {'foo': "bar"}
        do_api_call("", method='post', postdata=postdata)
        self.assertEqual(self.post.call_args[1]['data'], postdata)

    def assert_token_passed(self, tokens, method):
        for token in tokens:
            self.set_token(token)
            expected_header = {'Authorization': "Token token={}".format(token)}
            do_api_call("", method=method)
            if method == 'get':
                self.assertEqual(self.get.call_args[1]['headers'],
                                 expected_header)
            elif method == 'post':
                self.assertEqual(self.post.call_args[1]['headers'],
                                 expected_header)
            else:
                raise ValueError("`method` must be one of ['get', 'post']!")

    @patch('requests.get', get)
    def test_auth_string_passed_get(self):
        tokens = ["", "foobar123", "dtrndturiaehc",
                  "54TRNEDr:-)/nyUfeg n:s lvℕΓΦ∃Δ∂ℝ⇐⊂6"]
        self.assert_token_passed(tokens, method='get')

    @patch('requests.post', post)
    def test_auth_string_passed_post(self):
        tokens = ["", "foobar123", "dtrndturiaehc",
                  "54TRNEDr:-)/nyUfeg n:s lvℕΓΦ∃Δ∂ℝ⇐⊂6"]
        self.assert_token_passed(tokens, method='post')


class TestGerokUser(AppInitialized):
    users = {
        '1245': {
            'login': "test",
            'address': "Gerokstraße 38, 00-0",
            'mail': "test@test.de",
            'status': "OK",
            'hosts': [
                {'ip': "141.30.0.0", 'mac': "aa-bb-cc-dd-ee-ff",
                 'hostname': "foobar", 'alias': "mein_laptop"},
                {'ip': "141.30.0.1", 'mac': "aa-bb-cc-dd-ee-fe",
                 'hostname': "baz", 'alias': "mein_neuer_laptop"},
            ],
        },
    }
    api_mock = MagicMock()

    def setUp(self):
        def fake_api(request, method='get', postdata=None):
            """A fake gerok api, replacing `do_api_call` for testing."""
            # TODO: read get-arguments.  Currently, only trivial request
            # cases (request == user_id, return a dict with user data) are
            # handled.
            return {
                'id': request,
                **self.users.get(request)
            }

        self.api_mock.side_effect = fake_api

    def get_example_user(self, id):
        try:
            return {
                'id': id,
                **self.users.get(id)
            }
        except KeyError:
            raise ValueError("Id {} not in `users` dict".format(id))

    def assert_userdata_passed(self, user, user_data):
        """Test if contents of `user_data` fully appear in the `user` object
        """
        self.assertEqual(user.uid, user_data['login'])
        self.assertEqual(user.id.value, user_data['id'])
        self.assertEqual(user.login.value, user_data['login'])
        self.assertEqual(user.address.value, user_data['address'])
        self.assertEqual(user.mail.value, user_data['mail'])
        self.assertEqual(user.status.value, user_data['status'])
        for host in user_data['hosts']:
            # using `assertIn` allows agnosticism regarding the chosen
            # string concatenation method
            self.assertIn(host['ip'], user.ips.value)
            self.assertIn(host['mac'], user.mac.value)
            self.assertIn(host['hostname'], user.hostname.value)
            self.assertIn(host['alias'], user.hostalias.value)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_explicit_init(self):
        id = '1245'
        user_data = self.get_example_user(id)
        user = User(user_data['login'], id)

        self.assertTrue(self.api_mock.called)
        self.assertEqual(self.api_mock.call_args[0], (id,))
        self.assert_userdata_passed(user=user, user_data=user_data)